import { Bot } from "lucide-react";

export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-3 text-xs text-slate-500">
      <div className="flex size-8 items-center justify-center rounded-lg bg-cyan-300/10 text-cyan-200">
        <Bot className="size-4" />
      </div>
      <span className="typing">
        <i />
        <i />
        <i />
      </span>{" "}
      Analyzing your workspace...
    </div>
  );
}
