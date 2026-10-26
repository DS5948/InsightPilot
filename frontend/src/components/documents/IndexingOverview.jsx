import { Database } from "lucide-react";
import { EMPTY } from "@/lib/format";

const steps = [
  "Extract text",
  "Split into chunks",
  "Create embeddings",
  "Store in vector database",
];

export default function IndexingOverview({ documentCount, totalChunks }) {
  return (
    <div className="panel grid gap-4 p-5 md:grid-cols-4">
      <div className="md:col-span-3">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-cyan-300/10 text-cyan-200">
            <Database className="size-5" />
          </div>
          <div>
            <div className="text-sm font-medium text-slate-200">
              How indexing works
            </div>
            <div className="mt-1 text-xs text-slate-500">
              Your reports become searchable in four simple steps.
            </div>
          </div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-4">
          {steps.map((step, i) => (
            <div
              key={step}
              className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3"
            >
              <div className="text-[10px] font-semibold text-cyan-300">
                0{i + 1}
              </div>
              <div className="mt-2 text-xs font-medium text-slate-300">
                {step}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="hidden border-l border-white/[0.07] pl-5 md:block">
        <div className="text-xs text-slate-500">Indexed storage</div>
        <div className="mt-2 text-xl font-semibold text-white">
          {documentCount ? `${totalChunks} chunks` : EMPTY}
        </div>
        <div className="mt-1 text-xs text-slate-500">
          {documentCount
            ? `${documentCount} documents ready`
            : "No documents yet"}
        </div>
      </div>
    </div>
  );
}
