"""Dataset-agnostic profiling for InsightPilot.

Everything here depends only on rows and columns, never on column names.
Works with pandas 2.x and 3.x.
"""

from __future__ import annotations

import re
import warnings
from typing import Any

import numpy as np
import pandas as pd
from pandas.api import types as ptypes


# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

DATE_PARSE_MIN_RATIO = 0.9       # share of non-null values that must parse
CATEGORICAL_MAX_UNIQUE = 50      # text columns up to this many uniques
CATEGORICAL_MAX_RATIO = 0.5      # ...and unique/non-null no higher than this
LOW_CARDINALITY_NUMERIC = 12     # numeric columns usable as a group-by
FREE_TEXT_AVG_LENGTH = 60        # long strings are free text
TOP_VALUES = 8

# A string must look date-like before we even try to parse it. This stops
# values such as "12345" or "1.5" from being read as dates.
_DATE_HINT = re.compile(
    r"(\d{1,4}[-/.]\d{1,2}([-/.]\d{1,4})?)"
    r"|(\d{1,2}:\d{2})"
    r"|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
    re.IGNORECASE,
)

_ID_NAME = re.compile(
    r"(^|[_\s-])(id|key|uuid|guid|code|no|number|index|zip|zipcode|postal|pincode|pin|phone)$"
    r"|^id[_\s-]|[a-z0-9](ID|Id)$",
    re.IGNORECASE,
)
_YEAR_NAME = re.compile(r"(^|[_\s-])(year|yr)$|^(year|yr)[_\s-]", re.IGNORECASE)

ROLES = ("numeric", "categorical", "date", "boolean", "identifier", "text")


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def to_jsonable(value: Any) -> Any:
    """Convert numpy / pandas scalars to plain JSON-safe Python values."""
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp, pd.Period)):
        if pd.isna(value):
            return None
        return value.isoformat()
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        if np.isnan(value) or np.isinf(value):
            return None
        return value
    if isinstance(value, (int, bool, str)):
        return value
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return str(value)


def _num(value: Any) -> float | int | None:
    value = to_jsonable(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return None


# ---------------------------------------------------------------------------
# Date detection and normalisation
# ---------------------------------------------------------------------------

def _try_parse_dates(series: pd.Series) -> pd.Series | None:
    """Return a datetime Series if the text column is mostly dates, else None."""
    non_null = series.dropna().astype(str).str.strip()
    non_null = non_null[non_null != ""]
    if non_null.empty:
        return None

    sample = non_null.head(200)
    hinted = sample.map(lambda v: bool(_DATE_HINT.search(v))).mean()
    if hinted < DATE_PARSE_MIN_RATIO:
        return None

    cleaned = series.astype("string").str.strip()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            parsed = pd.to_datetime(cleaned, errors="coerce", format="mixed")
        except (TypeError, ValueError):
            try:
                parsed = pd.to_datetime(cleaned, errors="coerce")
            except (TypeError, ValueError):
                return None

    if parsed.dropna().empty:
        return None
    ratio = parsed.notna().sum() / max(int(cleaned.notna().sum()), 1)
    if ratio < DATE_PARSE_MIN_RATIO:
        return None
    return parsed


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Parse date-like text columns to datetime. Returns a new DataFrame."""
    df = df.copy()
    for column in df.columns:
        series = df[column]
        if ptypes.is_numeric_dtype(series) or ptypes.is_bool_dtype(series):
            continue
        if ptypes.is_datetime64_any_dtype(series):
            continue
        parsed = _try_parse_dates(series)
        if parsed is not None:
            df[column] = parsed
    return df


def dataframe_for_storage(df: pd.DataFrame) -> pd.DataFrame:
    """Turn datetime columns into ISO text so SQLite date functions work.

    Date-only columns become YYYY-MM-DD; columns with a time part become
    YYYY-MM-DD HH:MM:SS.
    """
    out = df.copy()
    for column in out.columns:
        if not ptypes.is_datetime64_any_dtype(out[column]):
            continue
        series = pd.to_datetime(out[column], errors="coerce")
        if series.dt.tz is not None:
            series = series.dt.tz_convert("UTC").dt.tz_localize(None)
        valid = series.dropna()
        has_time = bool(len(valid)) and bool((valid.dt.normalize() != valid).any())
        fmt = "%Y-%m-%d %H:%M:%S" if has_time else "%Y-%m-%d"
        out[column] = series.dt.strftime(fmt)
    return out


def restore_dataframe(df: pd.DataFrame, profile: dict | None) -> pd.DataFrame:
    """Re-apply roles from a stored profile after reading from SQLite."""
    if not profile:
        return df
    out = df.copy()
    roles = {c["name"]: c["role"] for c in profile.get("columns", [])}
    for column, role in roles.items():
        if column not in out.columns:
            continue
        if role == "date":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                out[column] = pd.to_datetime(out[column], errors="coerce")
        elif role == "boolean" and ptypes.is_numeric_dtype(out[column]):
            # Real boolean columns are stored by SQLite as 0/1. Text columns
            # such as Yes/No are left untouched.
            out[column] = out[column].map(
                lambda v: None if pd.isna(v) else bool(v)
            ).astype(object)
    return out


# ---------------------------------------------------------------------------
# Column role inference
# ---------------------------------------------------------------------------

def infer_role(series: pd.Series, total_rows: int) -> str:
    non_null = series.dropna()
    count = int(len(non_null))
    unique = int(non_null.nunique()) if count else 0
    name = str(series.name or "")

    if ptypes.is_datetime64_any_dtype(series):
        return "date"
    if ptypes.is_bool_dtype(series):
        return "boolean"

    if ptypes.is_numeric_dtype(series):
        if count == 0:
            return "numeric"
        is_integer = ptypes.is_integer_dtype(series) or bool(
            (non_null == non_null.round()).all()
        )
        # Years are better used as an axis label than summed as a measure.
        if (
            is_integer
            and _YEAR_NAME.search(name)
            and float(non_null.min()) >= 1900
            and float(non_null.max()) <= 2100
        ):
            return "categorical"
        # Zip codes, phone numbers and similar are labels, not quantities.
        if is_integer and re.search(r"(zip|postal|pincode|phone)", name, re.IGNORECASE):
            return "identifier"
        # An integer column where every value is different is an ID/key.
        if is_integer and total_rows > 1 and unique == count and count == total_rows:
            sorted_vals = non_null.sort_values().to_numpy()
            consecutive = len(sorted_vals) > 1 and bool(
                (np.diff(sorted_vals) == 1).all()
            )
            name_hint = bool(_ID_NAME.search(str(series.name or "")))
            if consecutive or name_hint:
                return "identifier"
        if unique == 2 and set(non_null.unique()) <= {0, 1}:
            return "boolean"
        return "numeric"

    # Text-like from here on.
    if count == 0:
        return "text"
    strings = non_null.astype(str)
    lowered = set(strings.str.strip().str.lower().unique())
    if unique <= 2 and lowered <= {
        "true", "false", "yes", "no", "y", "n", "t", "f", "0", "1"
    }:
        return "boolean"
    if total_rows > 1 and unique == count and count == total_rows:
        # Unique per row: an identifier if short, otherwise free text.
        return "text" if strings.str.len().mean() > FREE_TEXT_AVG_LENGTH else "identifier"
    if strings.str.len().mean() > FREE_TEXT_AVG_LENGTH:
        return "text"
    if unique <= CATEGORICAL_MAX_UNIQUE and (unique / count) <= CATEGORICAL_MAX_RATIO:
        return "categorical"
    if unique <= 12:
        return "categorical"
    return "text"


# ---------------------------------------------------------------------------
# Column profile
# ---------------------------------------------------------------------------

def _profile_column(df: pd.DataFrame, name: str, forced_role: str | None = None) -> dict:
    series = df[name]
    total = int(len(df))
    non_null = series.dropna()
    count = int(len(non_null))
    nulls = total - count
    unique = int(non_null.nunique()) if count else 0
    role = forced_role or infer_role(series, total)

    info: dict[str, Any] = {
        "name": name,
        "role": role,
        "dtype": str(series.dtype),
        "null_count": nulls,
        "null_pct": round(nulls / total * 100, 2) if total else 0.0,
        "unique_count": unique,
        "groupable": False,
        "role_overridden": forced_role is not None,
    }

    if role == "numeric":
        info["groupable"] = unique <= LOW_CARDINALITY_NUMERIC
        if count:
            info.update(
                {
                    "min": _num(non_null.min()),
                    "max": _num(non_null.max()),
                    "mean": _num(non_null.mean()),
                    "median": _num(non_null.median()),
                    "std": _num(non_null.std()) if count > 1 else None,
                    "sum": _num(non_null.sum()),
                }
            )
    elif role == "date":
        if count:
            info["min"] = to_jsonable(non_null.min())
            info["max"] = to_jsonable(non_null.max())
            span = non_null.max() - non_null.min()
            info["span_days"] = int(span.days)
    elif role in {"categorical", "boolean"}:
        info["groupable"] = True
        counts = non_null.astype(str).value_counts().head(TOP_VALUES)
        info["top_values"] = [
            {"value": str(v), "count": int(c)} for v, c in counts.items()
        ]
    elif role in {"identifier", "text"}:
        if count:
            info["examples"] = [str(v)[:80] for v in non_null.head(3).tolist()]

    return info


# ---------------------------------------------------------------------------
# Whole-dataset profile
# ---------------------------------------------------------------------------

OVERRIDABLE_ROLES = ("numeric", "categorical", "identifier", "text")


def profile_dataframe(df: pd.DataFrame, overrides: dict[str, str] | None = None) -> dict:
    """Build the profile stored with the dataset and served to the dashboard.

    ``overrides`` maps column name -> role chosen by the user.
    """
    overrides = overrides or {}
    total_rows = int(len(df))
    total_cols = int(len(df.columns))
    total_cells = total_rows * total_cols
    missing_cells = int(df.isna().sum().sum()) if total_cells else 0

    try:
        duplicate_rows = int(df.duplicated().sum())
    except TypeError:
        duplicate_rows = 0

    columns = [_profile_column(df, str(c), overrides.get(str(c))) for c in df.columns]
    by_role: dict[str, int] = {role: 0 for role in ROLES}
    for column in columns:
        by_role[column["role"]] += 1

    return {
        "rows": total_rows,
        "column_count": total_cols,
        "missing_cells": missing_cells,
        "missing_pct": round(missing_cells / total_cells * 100, 2) if total_cells else 0.0,
        "duplicate_rows": duplicate_rows,
        "role_counts": by_role,
        "columns": columns,
    }


def column_map(profile: dict) -> dict[str, dict]:
    return {c["name"]: c for c in profile.get("columns", [])}


# ---------------------------------------------------------------------------
# Insights (computed in Python, phrased deterministically)
# ---------------------------------------------------------------------------

def _fmt_number(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 10_000:
        return f"{value / 1_000:.1f}K"
    if float(value).is_integer():
        return f"{int(value):,}"
    return f"{value:,.2f}"


def generate_insights(df: pd.DataFrame, profile: dict, limit: int = 6) -> list[dict]:
    insights: list[dict] = []
    columns = profile["columns"]

    def add(kind: str, text: str) -> None:
        insights.append({"kind": kind, "text": text})

    if profile["missing_cells"] == 0:
        add("quality", "No missing values were found.")
    else:
        worst = sorted(
            (c for c in columns if c["null_count"] > 0),
            key=lambda c: c["null_pct"],
            reverse=True,
        )
        affected = len(worst)
        top = worst[0]
        add(
            "quality",
            f"{affected} column{'s contain' if affected != 1 else ' contains'} missing values; "
            f"“{top['name']}” has the most ({top['null_pct']:.1f}% empty).",
        )

    if profile["duplicate_rows"]:
        add("quality", f"{profile['duplicate_rows']:,} duplicate rows were found.")

    for column in columns:
        if column["role"] == "date" and column.get("min"):
            add(
                "date",
                f"“{column['name']}” runs from {column['min'][:10]} to {column['max'][:10]}.",
            )
            break

    numeric = [c for c in columns if c["role"] == "numeric" and c.get("max") is not None]
    for column in numeric[:2]:
        add(
            "numeric",
            f"“{column['name']}” averages {_fmt_number(column['mean'])} "
            f"(range {_fmt_number(column['min'])} to {_fmt_number(column['max'])}).",
        )

    for column in columns:
        if column["role"] == "categorical" and column.get("top_values"):
            top = column["top_values"][0]
            share = top["count"] / max(profile["rows"] - column["null_count"], 1) * 100
            add(
                "category",
                f"In “{column['name']}”, “{top['value']}” is the most common value "
                f"({share:.0f}% of rows).",
            )
            break

    # Strongest correlation among numeric columns.
    num_names = [c["name"] for c in numeric]
    if 2 <= len(num_names) <= 40:
        try:
            corr = df[num_names].corr(numeric_only=True)
            best: tuple[str, str, float] | None = None
            for i, a in enumerate(num_names):
                for b in num_names[i + 1:]:
                    value = corr.loc[a, b]
                    if pd.notna(value) and (best is None or abs(value) > abs(best[2])):
                        best = (a, b, float(value))
            if best and abs(best[2]) >= 0.6:
                direction = "positively" if best[2] > 0 else "negatively"
                add(
                    "correlation",
                    f"“{best[0]}” and “{best[1]}” are strongly {direction} correlated "
                    f"(r = {best[2]:.2f}). This shows association, not cause.",
                )
        except Exception:
            pass

    return insights[:limit]


# ---------------------------------------------------------------------------
# Suggested questions and chart specs, built purely from the profile
# ---------------------------------------------------------------------------

def _pick_measure(columns: list[dict]) -> dict | None:
    numeric = [c for c in columns if c["role"] == "numeric" and c.get("max") is not None]
    if not numeric:
        return None
    # Prefer columns with real spread over near-constant ones.
    numeric.sort(key=lambda c: (c["unique_count"] > LOW_CARDINALITY_NUMERIC, c["unique_count"]), reverse=True)
    return numeric[0]


def suggest_questions(profile: dict, limit: int = 6) -> list[str]:
    columns = profile["columns"]
    measure = _pick_measure(columns)
    dims = [c for c in columns if c["role"] == "categorical"]
    dates = [c for c in columns if c["role"] == "date"]
    numeric = [c for c in columns if c["role"] == "numeric"]
    questions: list[str] = ["How many rows are in this dataset?"]

    if measure and dims:
        questions.append(f"What is the total {measure['name']} by {dims[0]['name']}?")
        questions.append(
            f"Which {dims[0]['name']} has the highest average {measure['name']}?"
        )
    if measure and dates:
        questions.append(f"How has {measure['name']} changed over {dates[0]['name']}?")
    if len(dims) >= 2:
        questions.append(
            f"How are {dims[0]['name']} and {dims[1]['name']} related? Show counts."
        )
    if len(numeric) >= 2:
        questions.append(
            f"Is there a relationship between {numeric[0]['name']} and {numeric[1]['name']}?"
        )
    if dims:
        questions.append(f"What are the top 5 most common values of {dims[0]['name']}?")
    if profile["missing_cells"]:
        questions.append("Which columns have missing values?")
    return questions[:limit]


def suggest_chart_specs(profile: dict, limit: int = 6) -> list[dict]:
    """Ready-to-render chart specs for one-click use in the chart studio."""
    columns = profile["columns"]
    measure = _pick_measure(columns)
    dims = [c for c in columns if c["role"] == "categorical"]
    dates = [c for c in columns if c["role"] == "date"]
    numeric = [c for c in columns if c["role"] == "numeric"]
    specs: list[dict] = []

    if measure and dates:
        specs.append(
            {
                "title": f"{measure['name']} over time",
                "spec": {
                    "chart": "line", "x": dates[0]["name"], "y": measure["name"],
                    "agg": "sum",
                },
            }
        )
    if measure and dims:
        specs.append(
            {
                "title": f"{measure['name']} by {dims[0]['name']}",
                "spec": {
                    "chart": "bar", "x": dims[0]["name"], "y": measure["name"],
                    "agg": "sum", "sort": "desc", "top_n": 10,
                },
            }
        )
    if dims:
        specs.append(
            {
                "title": f"Rows by {dims[0]['name']}",
                "spec": {
                    "chart": "pie", "x": dims[0]["name"], "agg": "count",
                    "sort": "desc", "top_n": 8,
                },
            }
        )
    if measure:
        specs.append(
            {
                "title": f"Distribution of {measure['name']}",
                "spec": {"chart": "histogram", "x": measure["name"]},
            }
        )
    if len(numeric) >= 2:
        specs.append(
            {
                "title": f"{numeric[0]['name']} vs {numeric[1]['name']}",
                "spec": {"chart": "scatter", "x": numeric[0]["name"], "y": numeric[1]["name"]},
            }
        )
    if len(numeric) >= 3:
        specs.append({"title": "Correlation between numeric columns", "spec": {"chart": "heatmap"}})
    return specs[:limit]
