/** Sum revenue grouped by `key`, sorted high → low. Returns [{ label, value }]. */
export function sumBy(rows, key) {
  const totals = {};
  rows.forEach((r) => {
    totals[r[key]] = (totals[r[key]] || 0) + (Number(r.revenue) || 0);
  });
  return Object.entries(totals)
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value);
}

/** Bucket revenue by calendar month, sorted chronologically. Returns [{ label, value }]. */
export function monthlyRevenue(rows) {
  const buckets = new Map();
  rows.forEach((r) => {
    const d = new Date(r.date);
    if (Number.isNaN(d.getTime())) return;
    const key = d.getFullYear() * 12 + d.getMonth();
    const prev = buckets.get(key) || {
      label: d.toLocaleString("en-US", { month: "short" }),
      value: 0,
    };
    prev.value += Number(r.revenue) || 0;
    buckets.set(key, prev);
  });
  return [...buckets.entries()].sort((a, b) => a[0] - b[0]).map(([, v]) => v);
}
