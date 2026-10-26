import { Bot } from "lucide-react";

export default function AskAnalystBanner({ onOpen }) {
  return (
    <button
      onClick={onOpen}
      className="group flex items-center justify-between rounded-xl border border-cyan-300/10 bg-gradient-to-r from-cyan-300/[0.06] to-violet-300/[0.04] p-5 text-left"
    >
      <div>
        <div className="flex items-center gap-2 text-sm font-medium text-cyan-100">
          <Bot className="size-4" /> Ask your data anything
        </div>
        <div className="mt-1 text-xs text-slate-500">
          Use natural language to uncover trends across sales and documents.
        </div>
      </div>
      <span className="rounded-lg bg-white/10 px-3 py-2 text-xs text-slate-200 transition group-hover:bg-white/15">
        Open AI Analyst <span className="ml-2">→</span>
      </span>
    </button>
  );
}
