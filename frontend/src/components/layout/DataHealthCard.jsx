import { Zap } from "lucide-react";
import { EMPTY } from "@/lib/format";

export default function DataHealthCard({ synced }) {
  return (
    <div className="mt-auto rounded-xl border border-cyan-300/10 bg-cyan-300/[0.04] p-4">
      <div className="flex items-center gap-2 text-xs font-medium text-cyan-100">
        <Zap className="size-3.5" />
        Data health
      </div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-cyan-300"
          style={{ width: synced ? "100%" : "0%" }}
        />
      </div>
      <div className="mt-2 flex justify-between text-[11px] text-slate-500">
        <span>{synced ? `${synced} records synced` : "No data synced"}</span>
        <span>{synced ? "100%" : EMPTY}</span>
      </div>
    </div>
  );
}
