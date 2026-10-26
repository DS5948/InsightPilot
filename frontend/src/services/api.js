const API_BASE_URL = import.meta.env.API_BASE_URL;

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = typeof payload === "object" && payload !== null ? payload.detail || payload.message || `Request failed (${response.status})` : payload || `Request failed (${response.status})`;
    const error = new Error(Array.isArray(message) ? message.map((item) => item.msg || String(item)).join("; ") : String(message));
    error.status = response.status; error.code = payload?.code; error.details = payload?.errors || payload; throw error;
  }
  return payload;
}
function jsonOptions(method, body) { return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }; }
function queryString(values = {}) {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => { if (value !== undefined && value !== null && value !== "") params.set(key, String(value)); });
  return params.size ? `?${params.toString()}` : "";
}

export const api = {
  health: () => request("/health"),
  getDataset: () => request("/dataset"),
  getDatasetColumns: () => request("/dataset/columns"),
  getDatasetRows: (params = {}) => request(`/dataset/rows${queryString(params)}`),
  getDatasetSuggestions: () => request("/dataset/suggestions"),
  setColumnRole: (name, role) => request(`/dataset/columns/${encodeURIComponent(name)}`, jsonOptions("PATCH", { role })),
  uploadDatasetCsv: (file) => { const form = new FormData(); form.append("file", file); return request("/dataset/upload", { method: "POST", body: form }); },
  getChartCapabilities: () => request("/charts/capabilities"),
  renderChart: (spec) => request("/charts/render", jsonOptions("POST", { spec })),
  chartFromQuestion: (question) => request("/charts/from-question", jsonOptions("POST", { question })),
  getPinnedCharts: () => request("/charts/pinned"),
  pinChart: (spec, title) => request("/charts/pinned", jsonOptions("POST", { spec, title })),
  unpinChart: (id) => request(`/charts/pinned/${encodeURIComponent(id)}`, { method: "DELETE" }),
  askChat: ({ question, mode = "auto" }) => request("/chat", jsonOptions("POST", { question, mode })),
  getDocuments: () => request("/documents"),
  uploadDocument: (file) => { const form = new FormData(); form.append("file", file); return request("/documents/upload", { method: "POST", body: form }); },
  deleteDocument: (documentId) => request(`/documents/${encodeURIComponent(documentId)}`, { method: "DELETE" }),
  clearAnalysis: () => request("/analysis", { method: "DELETE" }),
};
export { API_BASE_URL };
