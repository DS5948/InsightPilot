"""SQLite storage for the active dataset.

The active dataset lives in a table named ``sales``. The name is kept for
historical reasons so the text-to-SQL layer in llm.py keeps working, but the
table can hold any CSV. A small ``dataset_meta`` table records the filename,
upload time and the column profile, and ``pinned_charts`` stores chart specs
the user pinned to the dashboard.
"""

import json
import sqlite3
import threading
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from dataset_profile import (
    dataframe_for_storage,
    prepare_dataframe,
    profile_dataframe,
    restore_dataframe,
)


DB_PATH = Path(__file__).parent / "data" / "sales.db"

DATA_TABLE = "sales"
META_TABLE = "dataset_meta"
PINNED_TABLE = "pinned_charts"

_cache_lock = threading.Lock()
_cache: dict = {"key": None, "df": None}


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone()
    return row is not None


def _ensure_support_tables(connection: sqlite3.Connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {META_TABLE} (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            filename TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            profile_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {PINNED_TABLE} (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            spec_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


def _invalidate_cache() -> None:
    with _cache_lock:
        _cache["key"] = None
        _cache["df"] = None


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

def dataset_exists() -> bool:
    if not DB_PATH.exists():
        return False
    with closing(_connect()) as connection:
        return _table_exists(connection, DATA_TABLE)


def save_dataset(df: pd.DataFrame, filename: str) -> dict:
    """Store a new active dataset, replacing any previous one.

    Date-like text columns are parsed and stored as ISO text, a column profile
    is computed, and any pinned charts from the previous dataset are removed
    because their columns may no longer exist.
    """
    prepared = prepare_dataframe(df)
    profile = profile_dataframe(prepared)
    stored = dataframe_for_storage(prepared)
    uploaded_at = datetime.now(timezone.utc).isoformat()

    with closing(_connect()) as connection:
        stored.to_sql(DATA_TABLE, connection, if_exists="replace", index=False)
        _ensure_support_tables(connection)
        connection.execute(f"DELETE FROM {META_TABLE}")
        connection.execute(
            f"INSERT INTO {META_TABLE} (id, filename, uploaded_at, profile_json) "
            "VALUES (1, ?, ?, ?)",
            (filename, uploaded_at, json.dumps(profile)),
        )
        connection.execute(f"DELETE FROM {PINNED_TABLE}")
        connection.commit()

    _invalidate_cache()
    return {"filename": filename, "uploaded_at": uploaded_at, "profile": profile}


def load_dataset_meta() -> dict | None:
    """Return {filename, uploaded_at, profile} or None when no dataset exists.

    A database created before metadata existed is upgraded on first read.
    """
    if not dataset_exists():
        return None

    with closing(_connect()) as connection:
        _ensure_support_tables(connection)
        row = connection.execute(
            f"SELECT filename, uploaded_at, profile_json FROM {META_TABLE} WHERE id = 1"
        ).fetchone()
        if row:
            return {"filename": row[0], "uploaded_at": row[1], "profile": json.loads(row[2])}

        # Legacy database: build the profile from the stored table.
        raw = pd.read_sql_query(f'SELECT * FROM "{DATA_TABLE}"', connection)
        profile = profile_dataframe(prepare_dataframe(raw))
        uploaded_at = datetime.fromtimestamp(DB_PATH.stat().st_mtime, timezone.utc).isoformat()
        connection.execute(
            f"INSERT INTO {META_TABLE} (id, filename, uploaded_at, profile_json) "
            "VALUES (1, ?, ?, ?)",
            ("Uploaded dataset", uploaded_at, json.dumps(profile)),
        )
        connection.commit()
        return {"filename": "Uploaded dataset", "uploaded_at": uploaded_at, "profile": profile}


def load_dataset() -> tuple[pd.DataFrame, dict] | tuple[None, None]:
    """Return (DataFrame with roles restored, meta) or (None, None)."""
    meta = load_dataset_meta()
    if meta is None:
        return None, None

    key = (meta["uploaded_at"], meta["profile"]["rows"])
    with _cache_lock:
        if _cache["key"] == key and _cache["df"] is not None:
            return _cache["df"], meta

    with closing(_connect()) as connection:
        raw = pd.read_sql_query(f'SELECT * FROM "{DATA_TABLE}"', connection)
    df = restore_dataframe(raw, meta["profile"])

    with _cache_lock:
        _cache["key"] = key
        _cache["df"] = df
    return df, meta


def override_column_role(name: str, role: str) -> dict:
    """Change how one column is treated and re-profile the dataset.

    Raises ValueError for unknown columns or roles the data cannot support.
    """
    from dataset_profile import OVERRIDABLE_ROLES

    df, meta = load_dataset()
    if df is None:
        raise ValueError("No dataset found. Upload a CSV first.")
    columns = {c["name"]: c for c in meta["profile"]["columns"]}
    if name not in columns:
        raise ValueError(f"There is no column named '{name}'.")
    if role not in OVERRIDABLE_ROLES:
        raise ValueError(f"Role must be one of: {', '.join(OVERRIDABLE_ROLES)}.")
    if columns[name]["role"] in {"date", "boolean"}:
        raise ValueError(f"'{name}' is a {columns[name]['role']} column and cannot be changed.")
    if role == "numeric" and not pd.api.types.is_numeric_dtype(df[name]):
        raise ValueError(f"'{name}' contains text, so it cannot be treated as a number.")

    overrides = {
        n: c["role"] for n, c in columns.items() if c.get("role_overridden")
    }
    overrides[name] = role
    profile = profile_dataframe(df, overrides)

    with closing(_connect()) as connection:
        connection.execute(
            f"UPDATE {META_TABLE} SET profile_json = ? WHERE id = 1", (json.dumps(profile),)
        )
        connection.commit()
    _invalidate_cache()
    meta["profile"] = profile
    return meta


def clear_dataset() -> int:
    """Remove the active dataset and its pinned charts. Returns rows deleted."""
    if not DB_PATH.exists():
        return 0
    rows = 0
    with closing(_connect()) as connection:
        if _table_exists(connection, DATA_TABLE):
            rows = connection.execute(f'SELECT COUNT(*) FROM "{DATA_TABLE}"').fetchone()[0]
            connection.execute(f'DROP TABLE "{DATA_TABLE}"')
        if _table_exists(connection, META_TABLE):
            connection.execute(f"DELETE FROM {META_TABLE}")
        if _table_exists(connection, PINNED_TABLE):
            connection.execute(f"DELETE FROM {PINNED_TABLE}")
        connection.commit()
    _invalidate_cache()
    return int(rows)


# ---------------------------------------------------------------------------
# Pinned charts
# ---------------------------------------------------------------------------

def list_pinned_charts() -> list[dict]:
    if not DB_PATH.exists():
        return []
    with closing(_connect()) as connection:
        _ensure_support_tables(connection)
        rows = connection.execute(
            f"SELECT id, title, spec_json, created_at FROM {PINNED_TABLE} ORDER BY created_at"
        ).fetchall()
    return [
        {"id": r[0], "title": r[1], "spec": json.loads(r[2]), "created_at": r[3]}
        for r in rows
    ]


def add_pinned_chart(title: str, spec: dict) -> dict:
    item = {
        "id": f"pin_{uuid.uuid4().hex[:10]}",
        "title": title,
        "spec": spec,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with closing(_connect()) as connection:
        _ensure_support_tables(connection)
        connection.execute(
            f"INSERT INTO {PINNED_TABLE} (id, title, spec_json, created_at) VALUES (?, ?, ?, ?)",
            (item["id"], title, json.dumps(spec), item["created_at"]),
        )
        connection.commit()
    return item


def delete_pinned_chart(pin_id: str) -> bool:
    if not DB_PATH.exists():
        return False
    with closing(_connect()) as connection:
        _ensure_support_tables(connection)
        cursor = connection.execute(f"DELETE FROM {PINNED_TABLE} WHERE id = ?", (pin_id,))
        connection.commit()
        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Backwards-compatible helpers (used by the older test scripts)
# ---------------------------------------------------------------------------

def save_sales_data(df, filename: str = "Uploaded dataset"):
    """Save a DataFrame as the active dataset."""
    return save_dataset(df, filename)


def load_sales_data():
    """Load the active dataset as a DataFrame."""
    df, _ = load_dataset()
    if df is None:
        raise ValueError("No dataset found. Upload a CSV first.")
    return df.copy()


def get_revenue_by_region():
    """Calculate revenue by region using SQL (sales-shaped data only)."""
    query = """
        SELECT region, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY region
        ORDER BY total_revenue DESC
    """

    with closing(_connect()) as connection:
        return pd.read_sql_query(query, connection)
