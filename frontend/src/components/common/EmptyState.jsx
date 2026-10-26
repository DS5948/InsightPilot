export default function EmptyState({ icon: Icon, title, hint, className = "" }) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-2 px-6 py-10 text-center ${className}`}
    >
      <div className="flex size-10 items-center justify-center rounded-xl bg-white/[0.04] text-slate-500">
        <Icon className="size-5" />
      </div>
      <div className="text-sm font-medium text-slate-300">{title}</div>
      {hint && <div className="max-w-xs text-xs text-slate-600">{hint}</div>}
    </div>
  );
}
