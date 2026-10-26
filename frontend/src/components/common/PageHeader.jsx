/**
 * Eyebrow + title + description, with an optional action slot on the right.
 * `className` controls the wrapper layout, `titleClassName` the <h1> styling.
 */
export default function PageHeader({
  eyebrow,
  title,
  description,
  action,
  className = "flex flex-col justify-between gap-4 sm:flex-row sm:items-end",
  titleClassName = "mt-2 text-2xl font-semibold text-white",
}) {
  return (
    <div className={className}>
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1 className={titleClassName}>{title}</h1>
        <p className="mt-2 text-sm text-slate-500">{description}</p>
      </div>
      {action}
    </div>
  );
}
