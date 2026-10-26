import { Sparkles } from "lucide-react";

export default function Brand() {
  return (
    <div className="flex items-center gap-3">
      <div className="brand-mark">
        <Sparkles />
      </div>
      <div>
        <div className="text-sm font-semibold tracking-tight text-white">
          InsightPilot
        </div>
        <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500">
          Business intelligence
        </div>
      </div>
    </div>
  );
}
