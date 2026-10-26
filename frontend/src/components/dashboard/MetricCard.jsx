export default function MetricCard({ label, value, detail, accent }) {
  return (
    <div className="panel p-5">
      <div className="flex items-start justify-between">
        <span className="text-xs text-slate-500">{label}</span>
        <div className={`metric-dot ${accent}`} />
      </div>
      <div className="mt-4 text-2xl font-semibold tracking-tight text-white">
        {value}
      </div>
      <div className="mt-2 text-[11px] text-slate-600">{detail}</div>
    </div>
  );
}
