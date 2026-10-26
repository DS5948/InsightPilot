import { Sparkles } from "lucide-react";

export default function ChatWelcome() {
  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <div className="brand-mark mb-4">
        <Sparkles />
      </div>
      <h2 className="text-lg font-medium text-white">
        What would you like to know?
      </h2>
      <p className="mt-2 max-w-md text-sm text-slate-500">
        Ask about trends, products, regions, or findings in your uploaded
        reports.
      </p>
    </div>
  );
}
