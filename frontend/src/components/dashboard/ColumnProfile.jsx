import { useState } from "react";
import { useSetColumnRoleMutation } from "@/services/queries";

const ROLE_OPTIONS = ["numeric", "categorical", "date", "boolean", "identifier", "text"];
export default function ColumnProfile({ columns = [], hasData }) {
  const [editing, setEditing] = useState(null);
  const roleMutation = useSetColumnRoleMutation();
  if (!hasData) return null;
  return <section className="panel overflow-hidden">
    <div className="border-b border-white/[0.07] p-5"><h2 className="text-sm font-medium text-slate-200">Column profile</h2><p className="mt-1 text-xs text-slate-500">Detected types, completeness, distinct values, and basic statistics.</p></div>
    <div className="overflow-x-auto"><table className="min-w-[850px]"><thead><tr><th>Column</th><th>Detected type</th><th>Missing</th><th>Unique</th><th>Summary</th><th>Adjust role</th></tr></thead><tbody>
      {columns.map((column) => <tr key={column.name}>
        <td className="font-medium text-slate-200">{column.name}</td><td><span className="rounded-full bg-white/[0.06] px-2 py-1 text-[10px]">{column.role || column.type || "text"}</span></td>
        <td>{Number(column.null_count ?? column.nulls ?? 0).toLocaleString()}</td><td>{Number(column.unique_count ?? column.unique ?? 0).toLocaleString()}</td>
        <td className="max-w-xs text-xs text-slate-400">{column.min != null || column.max != null ? `${column.min ?? "—"} – ${column.max ?? "—"}${column.mean != null ? ` · avg ${column.mean}` : ""}` : (column.top_values || column.top || []).map?.((v) => typeof v === "object" ? `${v.value} (${v.count})` : v).join(", ") || column.summary || "—"}</td>
        <td><select aria-label={`Set role for ${column.name}`} className="select-button max-w-32 bg-[#111923]" value={editing?.[column.name] ?? column.role ?? "text"} disabled={roleMutation.isPending} onChange={async (e) => { const role = e.target.value; setEditing((old) => ({ ...old, [column.name]: role })); try { await roleMutation.mutateAsync({ name: column.name, role }); } catch { setEditing((old) => ({ ...old, [column.name]: column.role ?? "text" })); } }}>
          {ROLE_OPTIONS.map((role) => <option key={role} value={role}>{role}</option>)}
        </select></td>
      </tr>)}
    </tbody></table></div>
    {roleMutation.error && <p role="alert" className="px-5 pb-4 text-xs text-rose-300">{roleMutation.error.message}</p>}
  </section>;
}
