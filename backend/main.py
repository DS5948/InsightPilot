from __future__ import annotations

import csv
import hashlib
import traceback
from io import StringIO
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from charts import (
    ChartSpecError,
    build_chart,
    capabilities,
    describe_chart,
    spec_from_question,
    wants_chart,
)
from database import (
    add_pinned_chart,
    clear_dataset,
    dataset_exists,
    delete_pinned_chart,
    list_pinned_charts,
    load_dataset,
    override_column_role,
    save_dataset,
)
from dataset_profile import (
    OVERRIDABLE_ROLES,
    generate_insights,
    suggest_chart_specs,
    suggest_questions,
    to_jsonable,
)
from ingest_documents import get_chroma_collection, ingest_document
from rag_llm import retrieve_relevant_evidence
from workflow import graph


# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="InsightPilot API",
    description="REST API for the InsightPilot business intelligence assistant.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://insight-pilot-bay.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".txt"}

MAX_CSV_BYTES = 50 * 1024 * 1024
MAX_CSV_ROWS = 500_000
MAX_CSV_COLUMNS = 300
MAX_PINNED_CHARTS = 24


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def error_response(
    status_code: int,
    detail: str,
    code: str,
    errors: list[str] | None = None,
) -> JSONResponse:
    """Return the consistent error shape used by the React API client."""
    payload: dict = {"detail": detail, "code": code}
    if errors:
        payload["errors"] = errors
    return JSONResponse(status_code=status_code, content=payload)


def no_dataset_response() -> JSONResponse:
    return error_response(409, "No dataset is loaded. Upload a CSV first.", "NO_DATASET")


def chart_error_response(exc: ChartSpecError, profile: dict | None) -> JSONResponse:
    errors = None
    if profile:
        names = [c["name"] for c in profile["columns"]]
        errors = ["Available columns: " + ", ".join(names)]
    return error_response(422, str(exc), "CHART_SPEC_INVALID", errors)


def format_cell(value, role: str):
    """Serialize one table cell for JSON."""
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        if value == value.normalize():
            return value.strftime("%Y-%m-%d")
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return to_jsonable(value)


def dataset_summary(df: pd.DataFrame, meta: dict) -> dict:
    """General dashboard data. Depends only on rows and columns."""
    profile = meta["profile"]
    roles = profile["role_counts"]
    return {
        "has_data": True,
        "name": meta["filename"],
        "uploaded_at": meta["uploaded_at"],
        "rows": profile["rows"],
        "column_count": profile["column_count"],
        "kpis": {
            "rows": profile["rows"],
            "columns": profile["column_count"],
            "missing_pct": profile["missing_pct"],
            "missing_cells": profile["missing_cells"],
            "duplicate_rows": profile["duplicate_rows"],
            "numeric_columns": roles.get("numeric", 0),
            "categorical_columns": roles.get("categorical", 0),
            "date_columns": roles.get("date", 0),
        },
        "role_counts": roles,
        "insights": generate_insights(df, profile),
    }


def document_id_for_filename(filename: str) -> str:
    """Create a stable frontend identifier from the indexed source filename."""
    normalized = Path(filename).name
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"doc_{digest}"


def get_document_inventory() -> list[dict]:
    """Build a file-level inventory from Chroma chunk metadata.

    The current ingestion pipeline stores source and chunk_index metadata, but
    does not persist upload timestamps or a separate document registry.
    """
    collection = get_chroma_collection()
    result = collection.get(include=["metadatas"])

    counts: dict[str, int] = {}
    for metadata in result.get("metadatas") or []:
        if not metadata:
            continue
        source = metadata.get("source")
        if source:
            counts[source] = counts.get(source, 0) + 1

    return [
        {
            "id": document_id_for_filename(filename),
            "filename": filename,
            "status": "indexed",
            "chunks_indexed": chunk_count,
            "uploaded_at": None,
        }
        for filename, chunk_count in sorted(
            counts.items(), key=lambda item: item[0].lower()
        )
    ]


def get_document_sources_for_answer(question: str) -> list[dict]:
    """Return short source excerpts for the chat UI, when retrieval succeeds."""
    try:
        evidence = retrieve_relevant_evidence(question)
    except Exception:
        # Do not fail an otherwise successful answer just because source preview
        # retrieval failed. The main answer path will report its own errors.
        return []

    sources = []
    seen = set()
    for item in evidence:
        source_name = item.get("source", "Business report")
        text = (item.get("text") or "").strip()
        key = (source_name, text)
        if not text or key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "type": "document",
                "label": source_name,
                "excerpt": text[:500],
            }
        )
        if len(sources) >= 5:
            break

    return sources


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class ChartRenderRequest(BaseModel):
    spec: dict


class ChartQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class PinChartRequest(BaseModel):
    spec: dict
    title: str | None = Field(default=None, max_length=120)


class ColumnRoleRequest(BaseModel):
    role: str


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "ok",
        "service": "insightpilot-api",
        "version": "2.0.0",
    }


# ---------------------------------------------------------------------------
# Dataset: general dashboard data
# ---------------------------------------------------------------------------

@app.get("/api/v1/dataset")
def get_dataset():
    """Header, KPI cards and quick insights for whatever CSV is loaded."""
    df, meta = load_dataset()
    if df is None:
        return {"has_data": False}
    return dataset_summary(df, meta)


@app.get("/api/v1/dataset/columns")
def get_dataset_columns():
    """Column summary table: type, nulls, uniques and min/max or top values."""
    df, meta = load_dataset()
    if df is None:
        return {"has_data": False, "items": [], "overridable_roles": list(OVERRIDABLE_ROLES)}
    return {
        "has_data": True,
        "items": meta["profile"]["columns"],
        "overridable_roles": list(OVERRIDABLE_ROLES),
    }


@app.patch("/api/v1/dataset/columns/{column_name}")
def set_column_role(column_name: str, request: ColumnRoleRequest):
    """Let the user correct how a column is treated (e.g. a ZIP code)."""
    if not dataset_exists():
        return no_dataset_response()
    try:
        meta = override_column_role(column_name, request.role.strip().lower())
    except ValueError as exc:
        return error_response(422, str(exc), "COLUMN_ROLE_ERROR")
    column = next(c for c in meta["profile"]["columns"] if c["name"] == column_name)
    return {"success": True, "column": column}


@app.get("/api/v1/dataset/rows")
def get_dataset_rows(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=200),
    sort_by: str | None = Query(default=None, max_length=200),
    sort_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
):
    """Paginated, searchable, sortable data preview for any dataset."""
    df, meta = load_dataset()
    if df is None:
        return {
            "has_data": False,
            "columns": [],
            "items": [],
            "pagination": {"limit": limit, "offset": offset, "total": 0},
        }

    roles = {c["name"]: c["role"] for c in meta["profile"]["columns"]}
    view = df

    if search and search.strip():
        needle = search.strip().lower()
        mask = pd.Series(False, index=view.index)
        for column in view.columns:
            text = view[column].astype("string").str.lower()
            mask |= text.str.contains(needle, regex=False, na=False)
        view = view[mask]

    if sort_by:
        if sort_by not in roles:
            return error_response(
                422, f"There is no column named '{sort_by}'.", "INVALID_SORT_COLUMN"
            )
        view = view.sort_values(
            by=sort_by,
            ascending=(sort_dir == "asc"),
            na_position="last",
            kind="stable",
        )

    total = int(len(view))
    page = view.iloc[offset: offset + limit]
    items = []
    for index, row in page.iterrows():
        item = {"_row": int(index) + 1}
        for column in view.columns:
            item[column] = format_cell(row[column], roles[column])
        items.append(item)

    return {
        "has_data": True,
        "columns": [{"name": name, "role": role} for name, role in roles.items()],
        "items": items,
        "pagination": {"limit": limit, "offset": offset, "total": total},
    }


@app.get("/api/v1/dataset/suggestions")
def get_dataset_suggestions():
    """Questions and ready-made chart specs generated from the column profile."""
    df, meta = load_dataset()
    if df is None:
        return {"has_data": False, "questions": [], "charts": []}
    profile = meta["profile"]
    return {
        "has_data": True,
        "questions": suggest_questions(profile),
        "charts": suggest_chart_specs(profile),
    }


# ---------------------------------------------------------------------------
# CSV upload
# ---------------------------------------------------------------------------

class CsvValidationError(Exception):
    def __init__(self, detail: str, errors: list[str] | None = None):
        super().__init__(detail)
        self.detail = detail
        self.errors = errors


def parse_csv_bytes(file_bytes: bytes) -> tuple[pd.DataFrame, list[str]]:
    """Decode and parse an uploaded CSV. Returns (DataFrame, warnings)."""
    warnings: list[str] = []

    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")
        warnings.append("The file was not UTF-8, so it was read as Latin-1. Check accented characters.")

    try:
        delimiter = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|").delimiter
    except csv.Error:
        delimiter = ","
    if delimiter != ",":
        names = {";": "semicolon", "\t": "tab", "|": "pipe"}
        warnings.append(f"Detected a {names.get(delimiter, delimiter)}-separated file.")

    # Read the original header so duplicate or blank names are detected before
    # pandas renames duplicates.
    try:
        raw_headers = next(csv.reader(StringIO(text), delimiter=delimiter), [])
    except csv.Error as exc:
        raise CsvValidationError("Could not parse the CSV file.", [str(exc)])

    headers = [header.strip() for header in raw_headers]
    if not headers or not any(headers):
        raise CsvValidationError("The CSV must contain column headers.")

    named = [header for header in headers if header]
    if len(named) != len(set(named)):
        raise CsvValidationError(
            "Column names must be unique.",
            ["The CSV contains duplicate column names."],
        )

    try:
        # index_col=False stops pandas from using the first column as an index
        # when rows have a trailing delimiter.
        df = pd.read_csv(StringIO(text), sep=delimiter, index_col=False)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, ValueError) as exc:
        raise CsvValidationError("Could not parse the CSV file.", [str(exc)])

    # Columns with a blank header are dropped when empty (a trailing comma),
    # and rejected when they hold data.
    blank_positions = [i for i, header in enumerate(headers) if not header]
    drop = []
    for position in blank_positions:
        if position < len(df.columns) and df.iloc[:, position].isna().all():
            drop.append(df.columns[position])
        else:
            raise CsvValidationError("Column names cannot be empty.")
    if drop:
        df = df.drop(columns=drop)
        warnings.append(f"Ignored {len(drop)} empty column{'s' if len(drop) != 1 else ''} with no header.")

    df.columns = [str(column).strip() for column in df.columns]
    df = df.dropna(how="all").reset_index(drop=True)

    if len(df.columns) == 0 or df.empty:
        raise CsvValidationError("The CSV contains no records.")
    if len(df.columns) > MAX_CSV_COLUMNS:
        raise CsvValidationError(
            f"The CSV has {len(df.columns)} columns; the limit is {MAX_CSV_COLUMNS}."
        )
    if len(df) > MAX_CSV_ROWS:
        raise CsvValidationError(
            f"The CSV has {len(df):,} rows; the limit is {MAX_CSV_ROWS:,}."
        )

    return df, warnings


@app.post("/api/v1/dataset/upload", status_code=201)
@app.post("/api/v1/sales/upload", status_code=201)  # kept so the old frontend still works
async def upload_dataset_csv(file: UploadFile = File(...)):
    """Upload any CSV. It becomes the active dataset."""
    filename = Path(file.filename or "").name

    if not filename or Path(filename).suffix.lower() != ".csv":
        return error_response(415, "Upload a CSV file.", "UNSUPPORTED_FILE_TYPE")

    file_bytes = await file.read()

    if not file_bytes:
        return error_response(422, "The CSV file is empty.", "CSV_VALIDATION_ERROR")
    if len(file_bytes) > MAX_CSV_BYTES:
        return error_response(
            413,
            f"The file is larger than {MAX_CSV_BYTES // (1024 * 1024)} MB.",
            "CSV_TOO_LARGE",
        )

    try:
        df, warnings = parse_csv_bytes(file_bytes)
    except CsvValidationError as exc:
        return error_response(422, exc.detail, "CSV_VALIDATION_ERROR", exc.errors)

    try:
        meta = save_dataset(df, filename)
    except Exception as exc:
        print(f"Dataset save failed: {type(exc).__name__}: {exc}")
        return error_response(
            500,
            "The CSV was valid but could not be saved.",
            "DATASET_SAVE_ERROR",
        )

    profile = meta["profile"]
    dates = [c["name"] for c in profile["columns"] if c["role"] == "date"]
    if dates:
        warnings.append("Detected date columns: " + ", ".join(dates) + ".")
    if profile["missing_cells"]:
        warnings.append(f"{profile['missing_pct']}% of cells are empty.")
    if profile["duplicate_rows"]:
        warnings.append(f"{profile['duplicate_rows']:,} duplicate rows found.")

    loaded, loaded_meta = load_dataset()
    return {
        "success": True,
        "filename": filename,
        "rows_loaded": int(len(df)),
        "columns": list(df.columns),
        "warnings": warnings,
        "message": "Dataset loaded successfully.",
        "dataset": dataset_summary(loaded, loaded_meta),
    }


# ---------------------------------------------------------------------------
# Chart studio
# ---------------------------------------------------------------------------

@app.get("/api/v1/charts/capabilities")
def get_chart_capabilities():
    """Chart types, aggregations and filter operators the builder can offer."""
    return capabilities()


@app.post("/api/v1/charts/render")
def render_chart(request: ChartRenderRequest):
    """Render a chart from a spec (used by the manual builder and pinned charts)."""
    df, meta = load_dataset()
    if df is None:
        return no_dataset_response()
    try:
        return build_chart(df, request.spec, meta["profile"])
    except ChartSpecError as exc:
        return chart_error_response(exc, meta["profile"])


@app.post("/api/v1/charts/from-question")
def chart_from_question(request: ChartQuestionRequest):
    """Turn a plain-English request into a validated spec, then render it."""
    df, meta = load_dataset()
    if df is None:
        return no_dataset_response()
    try:
        spec, assumptions = spec_from_question(request.question.strip(), meta["profile"])
        chart = build_chart(df, spec, meta["profile"])
    except ChartSpecError as exc:
        return chart_error_response(exc, meta["profile"])
    except Exception as exc:
        print("\n--- INSIGHTPILOT CHART ERROR ---")
        traceback.print_exc()
        print("--- END CHART ERROR ---\n")
        return error_response(
            503,
            f"Chart generation failed: {type(exc).__name__}: {exc}",
            "CHART_GENERATION_ERROR",
        )
    return {"chart": chart, "assumptions": assumptions}


@app.get("/api/v1/charts/pinned")
def get_pinned_charts():
    """Pinned charts, re-rendered against the current data."""
    df, meta = load_dataset()
    pinned = list_pinned_charts()
    if df is None:
        return {"items": [], "total": 0}

    items = []
    for pin in pinned:
        entry = {**pin, "chart": None, "error": None}
        try:
            entry["chart"] = build_chart(df, pin["spec"], meta["profile"])
        except ChartSpecError as exc:
            entry["error"] = str(exc)
        items.append(entry)
    return {"items": items, "total": len(items)}


@app.post("/api/v1/charts/pinned", status_code=201)
def pin_chart(request: PinChartRequest):
    df, meta = load_dataset()
    if df is None:
        return no_dataset_response()
    if len(list_pinned_charts()) >= MAX_PINNED_CHARTS:
        return error_response(
            409,
            f"You can pin up to {MAX_PINNED_CHARTS} charts. Remove one first.",
            "PIN_LIMIT_REACHED",
        )
    try:
        chart = build_chart(df, request.spec, meta["profile"])
    except ChartSpecError as exc:
        return chart_error_response(exc, meta["profile"])

    pin = add_pinned_chart(request.title or chart["title"], chart["spec"])
    return {"success": True, "pinned": {**pin, "chart": chart, "error": None}}


@app.delete("/api/v1/charts/pinned/{pin_id}")
def unpin_chart(pin_id: str):
    if not delete_pinned_chart(pin_id):
        return error_response(404, "Pinned chart not found.", "PIN_NOT_FOUND")
    return {"success": True, "deleted_pin_id": pin_id}


# ---------------------------------------------------------------------------
# AI Analyst chat
# ---------------------------------------------------------------------------

def try_chart_answer(question: str) -> tuple[dict | None, str | None]:
    """When the user asks for a chart in chat, build one from the same engine.

    Returns (response_payload, warning). The payload is None when a chart could
    not be made, so the caller falls back to the normal text workflow.
    """
    df, meta = load_dataset()
    if df is None:
        return None, None
    try:
        spec, assumptions = spec_from_question(question, meta["profile"])
        chart = build_chart(df, spec, meta["profile"])
    except ChartSpecError as exc:
        return None, f"Could not draw a chart: {exc}"
    except Exception:
        traceback.print_exc()
        return None, None

    answer = describe_chart(chart)
    if assumptions:
        answer += "\n\nAssumptions: " + " ".join(assumptions)
    return {
        "answer": answer,
        "route": "analytics",
        "chart": chart,
        "sources": [
            {
                "type": "analytics",
                "label": "Dataset analytics",
                "excerpt": f"Chart calculated from {meta['filename']} with pandas.",
            }
        ],
        "warnings": [],
    }, None


@app.post("/api/v1/chat")
def chat(request: ChatRequest):
    question = request.question.strip()
    if not question:
        return error_response(400, "Question must not be empty.", "INVALID_QUESTION")

    chart_warning = None
    if wants_chart(question):
        payload, chart_warning = try_chart_answer(question)
        if payload is not None:
            return payload

    # Keep routing inside LangGraph, as it was in the Streamlit application.
    # React only submits the question; the workflow chooses analytics/documents/both.
    try:
        result = graph.invoke(
            {"question": question, "answer": "", "route": ""}
        )
        answer = result.get("answer", "")
        route = result.get("route", "analytics")

    except Exception as exc:
        if "No dataset found" in str(exc):
            return no_dataset_response()

        print("\n--- INSIGHTPILOT CHAT ERROR ---")
        traceback.print_exc()
        print("--- END CHAT ERROR ---\n")

        return error_response(
            503,
            f"Chat processing failed: {type(exc).__name__}: {exc}",
            "CHAT_PROCESSING_ERROR",
        )

    sources: list[dict] = []
    warnings: list[str] = []
    if chart_warning:
        warnings.append(chart_warning)

    if route in {"documents", "both"}:
        sources = get_document_sources_for_answer(question)
        if not sources:
            warnings.append("No document source excerpts were available for this answer.")
    elif route == "analytics":
        _, meta = load_dataset()
        name = meta["filename"] if meta else "the active dataset"
        sources = [
            {
                "type": "analytics",
                "label": "Dataset analytics",
                "excerpt": f"Calculated from {name} using a read-only SQL query.",
            }
        ]

    return {
        "answer": answer,
        "route": route,
        "chart": None,
        "sources": sources,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Document upload, list, and delete
# ---------------------------------------------------------------------------

@app.post("/api/v1/documents/upload", status_code=201)
async def upload_business_document(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if not filename or extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        return error_response(
            415,
            "Unsupported file type. Upload a PDF or TXT file.",
            "UNSUPPORTED_FILE_TYPE",
        )

    file_bytes = await file.read()
    if not file_bytes:
        return error_response(422, "The uploaded file is empty.", "DOCUMENT_INGESTION_ERROR")

    try:
        result = ingest_document(filename=filename, file_bytes=file_bytes)
    except ValueError as exc:
        return error_response(422, str(exc), "DOCUMENT_INGESTION_ERROR")
    except Exception:
        return error_response(
            500,
            "The document could not be indexed. Check the backend logs.",
            "DOCUMENT_INGESTION_ERROR",
        )

    return {
        "success": True,
        "document": {
            "id": document_id_for_filename(result["filename"]),
            "filename": result["filename"],
            "status": "indexed",
            "chunks_indexed": result["chunks_stored"],
            # The current storage schema does not record upload timestamps.
            "uploaded_at": None,
        },
        "message": "Document indexed successfully.",
    }


@app.get("/api/v1/documents")
def list_documents():
    try:
        items = get_document_inventory()
    except Exception:
        return error_response(
            500,
            "Could not read the indexed document list.",
            "DOCUMENT_LIST_ERROR",
        )

    return {"items": items, "total": len(items)}


@app.delete("/api/v1/documents/{document_id}")
def delete_document(document_id: str):
    try:
        inventory = get_document_inventory()
        document = next((item for item in inventory if item["id"] == document_id), None)

        if document is None:
            return error_response(
                404,
                "Document not found.",
                "DOCUMENT_NOT_FOUND",
            )

        collection = get_chroma_collection()
        collection.delete(where={"source": document["filename"]})

        return {
            "success": True,
            "deleted_document_id": document_id,
            "message": "Document and its indexed chunks were deleted.",
        }
    except Exception:
        return error_response(
            500,
            "Could not delete the document. Check the backend logs.",
            "DOCUMENT_DELETE_ERROR",
        )


# ---------------------------------------------------------------------------
# Clear all data for the current local analysis
# ---------------------------------------------------------------------------

@app.delete("/api/v1/analysis")
def clear_analysis():
    rows_deleted = 0
    documents_deleted = 0

    try:
        rows_deleted = clear_dataset()

        collection = get_chroma_collection()
        existing = collection.get(include=["metadatas"])
        ids = existing.get("ids") or []
        metadatas = existing.get("metadatas") or []
        documents_deleted = len({
            metadata.get("source")
            for metadata in metadatas
            if metadata and metadata.get("source")
        })

        if ids:
            collection.delete(ids=ids)

    except Exception:
        return error_response(
            500,
            "Could not clear the current analysis data.",
            "CLEAR_ANALYSIS_ERROR",
        )

    return {
        "success": True,
        "sales_rows_deleted": int(rows_deleted),  # name kept for the existing client
        "rows_deleted": int(rows_deleted),
        "documents_deleted": int(documents_deleted),
        "message": "Current analysis data cleared.",
    }
