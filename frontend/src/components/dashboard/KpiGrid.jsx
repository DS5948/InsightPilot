import MetricCard from "@/components/dashboard/MetricCard";
import { EMPTY } from "@/lib/format";

export default function KpiGrid({ hasData, dataset }) {
  const kpis = dataset?.kpis || {};
  return <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
    <MetricCard label="Rows" value={hasData ? Number(kpis.rows ?? dataset?.rows ?? 0).toLocaleString() : EMPTY} detail="Records in active dataset" accent="bg-cyan-300" />
    <MetricCard label="Columns" value={hasData ? Number(kpis.columns ?? dataset?.column_count ?? 0).toLocaleString() : EMPTY} detail="Detected fields" accent="bg-violet-300" />
    <MetricCard label="Missing values" value={hasData ? `${kpis.missing_pct ?? 0}%` : EMPTY} detail={hasData ? `${Number(kpis.missing_cells || 0).toLocaleString()} empty cells` : "No dataset loaded"} accent="bg-amber-300" />
    <MetricCard label="Duplicate rows" value={hasData ? Number(kpis.duplicate_rows || 0).toLocaleString() : EMPTY} detail="Exact duplicate records" accent="bg-emerald-300" />
  </div>;
}
