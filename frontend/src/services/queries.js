import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";

export const queryKeys = {
  health: ["health"], dataset: ["dataset"], columns: ["dataset", "columns"], rows: ["dataset", "rows"],
  suggestions: ["dataset", "suggestions"], capabilities: ["charts", "capabilities"], pinned: ["charts", "pinned"], documents: ["documents"],
};
const refreshDataset = async (client) => Promise.all([
  client.invalidateQueries({ queryKey: queryKeys.dataset }), client.invalidateQueries({ queryKey: queryKeys.columns }),
  client.invalidateQueries({ queryKey: queryKeys.rows }), client.invalidateQueries({ queryKey: queryKeys.suggestions }),
  client.invalidateQueries({ queryKey: queryKeys.pinned }),
]);
export function useHealthQuery() { return useQuery({ queryKey: queryKeys.health, queryFn: api.health, retry: 1 }); }
export function useDatasetQuery() { return useQuery({ queryKey: queryKeys.dataset, queryFn: api.getDataset }); }
export function useDatasetColumnsQuery() { return useQuery({ queryKey: queryKeys.columns, queryFn: api.getDatasetColumns }); }
export function useDatasetRowsQuery(params = {}) { return useQuery({ queryKey: [...queryKeys.rows, params], queryFn: () => api.getDatasetRows(params), placeholderData: (previous) => previous }); }
export function useDatasetSuggestionsQuery() { return useQuery({ queryKey: queryKeys.suggestions, queryFn: api.getDatasetSuggestions }); }
export function useChartCapabilitiesQuery() { return useQuery({ queryKey: queryKeys.capabilities, queryFn: api.getChartCapabilities }); }
export function usePinnedChartsQuery() { return useQuery({ queryKey: queryKeys.pinned, queryFn: api.getPinnedCharts }); }
export function useUploadDatasetMutation() { const client = useQueryClient(); return useMutation({ mutationFn: api.uploadDatasetCsv, onSuccess: () => refreshDataset(client) }); }
export function useSetColumnRoleMutation() { const client = useQueryClient(); return useMutation({ mutationFn: ({ name, role }) => api.setColumnRole(name, role), onSuccess: () => Promise.all([client.invalidateQueries({ queryKey: queryKeys.columns }), client.invalidateQueries({ queryKey: queryKeys.dataset })]) }); }
export function useRenderChartMutation() { return useMutation({ mutationFn: api.renderChart }); }
export function useChartFromQuestionMutation() { return useMutation({ mutationFn: api.chartFromQuestion }); }
export function usePinChartMutation() { const client = useQueryClient(); return useMutation({ mutationFn: ({ spec, title }) => api.pinChart(spec, title), onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.pinned }) }); }
export function useUnpinChartMutation() { const client = useQueryClient(); return useMutation({ mutationFn: api.unpinChart, onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.pinned }) }); }
export function useChatMutation() { return useMutation({ mutationFn: api.askChat }); }
export function useDocumentsQuery() { return useQuery({ queryKey: queryKeys.documents, queryFn: api.getDocuments }); }
export function useUploadDocumentMutation() { const client = useQueryClient(); return useMutation({ mutationFn: api.uploadDocument, onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.documents }) }); }
export function useDeleteDocumentMutation() { const client = useQueryClient(); return useMutation({ mutationFn: api.deleteDocument, onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.documents }) }); }
export function useClearAnalysisMutation() { const client = useQueryClient(); return useMutation({ mutationFn: api.clearAnalysis, onSuccess: () => client.invalidateQueries() }); }
