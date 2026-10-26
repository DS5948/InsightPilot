import { FileText } from "lucide-react";
import EmptyState from "@/components/common/EmptyState";
import SearchInput from "@/components/common/SearchInput";
import DocumentRow from "@/components/documents/DocumentRow";

export default function DocumentList({ documents, filtered, query, onQueryChange, onDelete, deleting }) {
  return (
    <div className="panel overflow-hidden">
      <div className="flex flex-col gap-4 border-b border-white/[0.07] p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-sm font-medium text-slate-200">Indexed documents <span className="ml-2 rounded-full bg-white/10 px-2 py-0.5 text-[10px] text-slate-400">{documents.length}</span></div>
          <div className="mt-1 text-xs text-slate-500">Files available to the AI Analyst</div>
        </div>
        <SearchInput value={query} onChange={onQueryChange} placeholder="Search documents..." />
      </div>
      {filtered.length === 0 ? (
        <EmptyState icon={FileText} title={documents.length ? "No matching documents" : "No documents yet"} hint={documents.length ? "Try a different search term." : "Upload PDF or TXT reports to build your knowledge base."} />
      ) : (
        <div className="divide-y divide-white/[0.06]">{filtered.map((document) => <DocumentRow key={document.id || document.name} doc={document} onDelete={() => onDelete?.(document)} deleting={deleting} />)}</div>
      )}
    </div>
  );
}
