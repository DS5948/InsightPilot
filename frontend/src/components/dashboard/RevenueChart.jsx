import { BarChart3, ChevronDown } from "lucide-react";
import EmptyState from "@/components/common/EmptyState";
import { formatCompact } from "@/lib/format";

export default function RevenueChart({ data }) {
  const max = Math.max(0, ...data.map((d) => d.value));
  const ticks = [1, 0.8, 0.6, 0.4, 0.2];
  return (
    <div className="panel p-5">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm font-medium text-slate-200">
            Revenue trend
          </div>
          <div className="mt-1 text-xs text-slate-500">Monthly performance</div>
        </div>
        <button className="select-button">
          Date range <ChevronDown />
        </button>
      </div>
      {data.length === 0 ? (
        <EmptyState
          icon={BarChart3}
          title="No revenue data yet"
          hint="Import a CSV to see your monthly revenue trend."
        />
      ) : (
        <div className="mt-6 flex h-44 gap-4">
          <div className="flex flex-col justify-between pb-5 text-[10px] text-slate-600">
            {ticks.map((t) => (
              <span key={t}>{formatCompact(max * t)}</span>
            ))}
          </div>
          <div className="relative flex flex-1 flex-col justify-between">
            <div className="chart-grid" />
            <div className="relative flex flex-1 items-end justify-around gap-6 px-6 pb-5">
              {data.map((d, i) => (
                <div
                  key={`${d.label}-${i}`}
                  className="chart-bar"
                  style={{ height: `${max ? (d.value / max) * 84 : 0}%` }}
                >
                  <span>{formatCompact(d.value)}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-around px-6 text-[10px] text-slate-600">
              {data.map((d, i) => (
                <span key={`${d.label}-${i}`}>{d.label}</span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
