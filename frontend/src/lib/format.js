export const EMPTY = "—";

export function formatMoney(value) {
  return `$${Number(value).toLocaleString()}`;
}

export function formatCompact(value) {
  if (value >= 1_000_000) return `$${+(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${+(value / 1_000).toFixed(1)}k`;
  return `$${Math.round(value)}`;
}
