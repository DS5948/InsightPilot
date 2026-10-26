import { FileText, Trash2 } from "lucide-react";

export default function DocumentRow({ doc, onDelete, deleting }) {
  return (
    <div className="flex items-center gap-4 px-5 py-4 transition hover:bg-white/[0.02]">
      <div className={`flex size-10 shrink-0 items-center justify-center rounded-lg text-[10px] font-bold ${doc.type === "PDF" ? "bg-rose-400/10 text-rose-300" : "bg-cyan-300/10 text-cyan-200"}`}>{doc.type || <FileText className="size-4" />}</div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium text-slate-200">{doc.name}</div>
        <div className="mt-1 text-xs text-slate-600">{doc.chunks} chunks · Indexed {doc.date}</div>
      </div>
      <span className="hidden items-center gap-1.5 text-[11px] text-emerald-300 sm:flex"><span className="size-1.5 rounded-full bg-emerald-300" />{doc.status === "indexed" ? "Ready" : doc.status}</span>
      <button className="icon-button" onClick={onDelete} disabled={deleting} title={`Delete ${doc.name}`} aria-label={`Delete ${doc.name}`}><Trash2 className="size-4" /></button>
    </div>
  );
}
