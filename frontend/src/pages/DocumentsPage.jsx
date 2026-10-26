import { useMemo, useRef, useState } from "react";
import PageHeader from "@/components/common/PageHeader";
import UploadNotice from "@/components/common/UploadNotice";
import IndexingOverview from "@/components/documents/IndexingOverview";
import DocumentList from "@/components/documents/DocumentList";
import { useDeleteDocumentMutation, useDocumentsQuery, useUploadDocumentMutation } from "@/services/queries";

export default function DocumentsPage() {
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");
  const fileRef = useRef(null);
  const documentsQuery = useDocumentsQuery();
  const upload = useUploadDocumentMutation();
  const remove = useDeleteDocumentMutation();
  const rawItems = documentsQuery.data?.items ?? [];
  const documents = useMemo(() => rawItems.map((item) => {
    const filename = item.filename || item.name || "Untitled document";
    const extension = filename.toLowerCase().endsWith(".pdf") ? "PDF" : "TXT";
    const uploadedAt = item.uploaded_at ? new Date(item.uploaded_at).toLocaleDateString() : "—";
    return { ...item, id: item.id, name: filename, type: extension, chunks: item.chunks_indexed ?? item.chunks ?? 0, date: uploadedAt, status: item.status || "indexed" };
  }), [rawItems]);
  const filtered = documents.filter((document) => document.name.toLowerCase().includes(query.toLowerCase()));
  const totalChunks = documents.reduce((sum, document) => sum + (Number(document.chunks) || 0), 0);

  const handleFiles = async (event) => {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    if (!files.length) return;
    setNotice("");
    try {
      const results = [];
      for (const file of files) results.push(await upload.mutateAsync(file));
      setNotice(results.map((result) => result.message || `${result.document?.filename || "Document"} indexed`).join(" "));
    } catch (error) {
      setNotice(`Upload failed: ${error.message}`);
    }
  };

  const handleDelete = async (document) => {
    if (!window.confirm(`Delete ${document.name} and its indexed content?`)) return;
    try {
      await remove.mutateAsync(document.id);
      setNotice(`${document.name} was deleted.`);
    } catch (error) {
      setNotice(`Delete failed: ${error.message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6 p-5 sm:p-8">
      <PageHeader
        eyebrow="Knowledge base"
        title="Business documents"
        description="Upload reports to give your AI Analyst more context."
        action={<><input ref={fileRef} type="file" accept=".pdf,.txt,application/pdf,text/plain" multiple className="hidden" onChange={handleFiles} /><button className="button-primary" onClick={() => fileRef.current?.click()} disabled={upload.isPending}>{upload.isPending ? "Indexing…" : "Upload documents"}</button></>}
      />
      {notice && <UploadNotice onDismiss={() => setNotice("")}>{notice}</UploadNotice>}
      {(documentsQuery.error || remove.error) && <div role="alert" className="rounded-lg border border-rose-400/20 bg-rose-400/[0.06] px-4 py-3 text-xs text-rose-200">{documentsQuery.error?.message || remove.error?.message}</div>}
      {documentsQuery.isLoading && <div className="text-xs text-slate-500">Loading indexed documents…</div>}
      <IndexingOverview documentCount={documents.length} totalChunks={totalChunks} />
      <DocumentList documents={documents} filtered={filtered} query={query} onQueryChange={setQuery} onDelete={handleDelete} deleting={remove.isPending} />
    </div>
  );
}
