import { Check, X } from "lucide-react";

/** Green confirmation banner. Pass `onDismiss` to show the close button. */
export default function UploadNotice({ children, onDismiss }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-emerald-400/20 bg-emerald-400/[0.06] px-4 py-3 text-xs text-emerald-200">
      <span className="flex items-center gap-2">
        <Check className="size-4" /> {children}
      </span>
      {onDismiss && (
        <button onClick={onDismiss}>
          <X className="size-4" />
        </button>
      )}
    </div>
  );
}
