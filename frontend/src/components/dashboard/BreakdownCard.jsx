import { BarChart3 } from "lucide-react";
import EmptyState from "@/components/common/EmptyState";
import { formatMoney } from "@/lib/format";

export default function BreakdownCard({
  title,
  subtitle,
  items,
  colors,
  emptyLabel,
}) {
  const max = Math.max(0, ...items.map((i) => i.value));
  return (
    <div className="panel p-5">
      <div className="text-sm font-medium text-slate-200">{title}</div>
      <div className="mt-1 text-xs text-slate-500">{subtitle}</div>
      {items.length === 0 ? (
        <EmptyState icon={BarChart3} title={emptyLabel} className="py-8" />
      ) : (
        <div className="mt-6 flex flex-col gap-5">
          {items.map((item, i) => (
            <div key={item.label}>
              <div className="mb-2 flex items-center justify-between text-xs">
                <span className="text-slate-300">{item.label}</span>
                <span className="font-medium text-slate-100">
                  {formatMoney(item.value)}
                </span>
              </div>
              <div className="h-1.5 rounded-full bg-white/[0.06]">
                <div
                  className={`h-full rounded-full ${colors[i % colors.length]}`}
                  style={{ width: `${max ? (item.value / max) * 100 : 0}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
