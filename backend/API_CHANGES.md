# InsightPilot API v2: generic datasets and chart studio

Any CSV can now be uploaded. The dashboard is built from a column profile, not from column names.

## Removed (hardcoded to sales columns)

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/monthly-revenue`
- `GET /api/v1/dashboard/product-performance`
- `GET /api/v1/dashboard/region-performance`
- `GET /api/v1/sales`

## Dataset

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/dataset/upload` | Upload a CSV (`/api/v1/sales/upload` still works as an alias). Returns `dataset` summary plus `warnings`. |
| GET | `/api/v1/dataset` | Header, KPI cards, role counts, quick insights. `{has_data:false}` when empty. |
| GET | `/api/v1/dataset/columns` | Column summary table (role, nulls, uniques, min/max/mean, top values). |
| PATCH | `/api/v1/dataset/columns/{name}` | Body `{role}`. Fix a wrong guess: `numeric`, `categorical`, `identifier`, `text`. |
| GET | `/api/v1/dataset/rows` | `limit`, `offset`, `search`, `sort_by`, `sort_dir`. Rows are `{_row, <column>: value}`. |
| GET | `/api/v1/dataset/suggestions` | `questions` (strings) and `charts` (`{title, spec}`), generated from the profile. |
| DELETE | `/api/v1/analysis` | Clears dataset, pinned charts and documents. |

Column roles: `numeric`, `categorical`, `date`, `boolean`, `identifier`, `text`.

## Charts

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/charts/capabilities` | Chart types, aggregations, time grains, filter operators. |
| POST | `/api/v1/charts/render` | Body `{spec}`. Validates and computes. Used by the manual builder. |
| POST | `/api/v1/charts/from-question` | Body `{question}`. Returns `{chart, assumptions}`. |
| GET | `/api/v1/charts/pinned` | Pinned charts, each re-rendered (`chart` or `error`). |
| POST | `/api/v1/charts/pinned` | Body `{spec, title?}`. |
| DELETE | `/api/v1/charts/pinned/{id}` | Unpin. |

### Spec

```json
{
  "chart": "bar",
  "x": "region", "y": "revenue", "agg": "sum",
  "color": null,
  "filters": [{"col": "product", "op": "==", "value": "Laptop"}],
  "sort": "desc", "top_n": 10, "bins": null, "time_grain": "auto"
}
```

Chart types: `bar`, `line`, `pie`, `scatter`, `histogram`, `box`, `heatmap`.

### Chart result

```json
{
  "chart": "bar", "title": "Total revenue by region",
  "spec": { "...normalised spec..." },
  "x_label": "region", "y_label": "Total of revenue",
  "series": [{"key": "s0", "label": "Total of revenue"}],
  "data": [{"x": "East", "s0": 110000}],
  "notes": ["4 of 12 rows match the filters."],
  "rows_used": 12, "truncated": false
}
```

Shape of `data` by type:

- `bar`, `line`, `pie`, `histogram`: `{x, s0, s1, ...}`. Series keys map to `series[].label`. Histogram rows also carry `start` and `end`.
- `scatter`: `{x, y, series}`, plus top-level `correlation`.
- `box`: `{x, min, q1, median, q3, max, mean, count, outliers}`.
- `heatmap`: `{x, y, value}` plus top-level `columns`.

## Chat

`POST /api/v1/chat` now also returns `chart` (a chart result, or `null`). If the question asks for a chart ("plot", "graph", "visualize", ...), the answer is a short description and `chart` is filled. If a chart cannot be drawn, it falls back to the normal text answer and adds a warning.

## Errors

Same shape as before: `{detail, code, errors?}`. New codes: `NO_DATASET` (409), `CHART_SPEC_INVALID` (422, `errors` lists the available columns), `COLUMN_ROLE_ERROR`, `CSV_TOO_LARGE` (413), `PIN_LIMIT_REACHED`, `PIN_NOT_FOUND`, `CHART_GENERATION_ERROR`.

## Storage notes

- The active dataset still lives in the SQLite table `sales` so the text-to-SQL layer is unchanged. Only one dataset is active at a time; uploading a new one replaces it and clears pinned charts.
- Date-like text columns are stored as ISO text (`YYYY-MM-DD`).
- `analytics.py`, `tools.py`, `app.py` (Streamlit) and their tests are sales-specific legacy files. The API no longer imports them.
