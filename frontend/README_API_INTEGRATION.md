# InsightPilot frontend API integration

The UI now uses **native `fetch`** for HTTP requests and **TanStack Query** for server-state fetching, caching, mutations, and invalidation.

## Configure the API URL

Create a `.env` file in the frontend project root (or copy `.env.example`) and set:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Do not put your Groq API key in this frontend `.env`; only the public API base URL belongs here.

## Install and run

```powershell
npm install
npm run dev
```

The FastAPI backend is expected at `http://localhost:8000` and should allow CORS from the Vite origin, usually `http://localhost:5173`.

## Integrated API endpoints

- `GET /health`
- `GET /dashboard/summary`
- `GET /dashboard/monthly-revenue`
- `GET /dashboard/product-performance`
- `GET /dashboard/region-performance`
- `GET /sales?limit=100&offset=0`
- `POST /sales/upload` (`multipart/form-data`, field `file`)
- `POST /chat` (JSON `{ question, mode: "auto" }`)
- `GET /documents`
- `POST /documents/upload` (`multipart/form-data`, field `file`)
- `DELETE /documents/{document_id}`
- `DELETE /analysis` is exposed in the API service but is not currently connected to a UI button.

## Expected response contract

Responses follow `InsightPilot_API_Contract.docx`. Dashboard endpoints return `has_data` and `items`/`kpis`; chat returns `answer`, optional `route`, `sources`, and `warnings`; document listing returns `items` and `total`.

If the backend is not running yet, API-backed screens will show request errors rather than silently substituting mock data.
