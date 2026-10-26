import { useEffect, useMemo, useRef, useState } from "react";
import { FileSpreadsheet, RefreshCw } from "lucide-react";
import PageHeader from "@/components/common/PageHeader";
import UploadNotice from "@/components/common/UploadNotice";
import KpiGrid from "@/components/dashboard/KpiGrid";
import SalesTable from "@/components/dashboard/SalesTable";
import ColumnProfile from "@/components/dashboard/ColumnProfile";
import ChartStudio from "@/components/dashboard/ChartStudio";
import AskAnalystBanner from "@/components/dashboard/AskAnalystBanner";
import { useDatasetColumnsQuery, useDatasetQuery, useDatasetRowsQuery, useDatasetSuggestionsQuery, useUploadDatasetMutation } from "@/services/queries";

function ErrorNotice({ error }) { return error ? <div role="alert" className="rounded-lg border border-rose-400/20 bg-rose-400/[0.06] px-4 py-3 text-xs text-rose-200">{error.message || "Something went wrong."}</div> : null; }
function dateLabel(value) { if (!value) return "Upload time unavailable"; const date = new Date(value); return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString(); }

export default function OverviewPage({ setActive, onAskQuestion }) {
  const fileRef = useRef(null); const [notice,setNotice] = useState(""); const [search,setSearch] = useState(""); const [offset,setOffset] = useState(0); const [limit,setLimit] = useState(25); const [sortBy,setSortBy] = useState(""); const [sortDir,setSortDir] = useState("asc"); const [totalColumn,setTotalColumn] = useState("");
  const dataset = useDatasetQuery(); const columns = useDatasetColumnsQuery(); const suggestions = useDatasetSuggestionsQuery();
  const rows = useDatasetRowsQuery({ limit, offset, search, sort_by: sortBy, sort_dir: sortDir }); const upload = useUploadDatasetMutation();
  const info = dataset.data; const hasData = Boolean(info?.has_data); const profile = columns.data?.items || []; const rowData = rows.data?.items || []; const rowColumns = rows.data?.columns || profile.map(c=>({name:c.name,role:c.role}));
  const numericColumns = useMemo(()=>profile.filter(c=>c.role==="numeric"),[profile]);
  useEffect(()=>{ if (!totalColumn && numericColumns.length) setTotalColumn(numericColumns[0].name); else if (totalColumn && !numericColumns.some(c=>c.name===totalColumn)) setTotalColumn(numericColumns[0]?.name || ""); },[numericColumns,totalColumn]);
  const numericTotal = useMemo(()=>rowData.length && totalColumn ? rowData.reduce((sum,row)=>sum+(Number(row[totalColumn])||0),0):0,[rowData,totalColumn]);
  const handleFile = async (event) => { const file=event.target.files?.[0]; event.target.value=""; if(!file)return; if(hasData&&!window.confirm("Uploading a CSV replaces the active dataset and clears pinned charts. Continue?"))return; setNotice(""); try { const result=await upload.mutateAsync(file); setOffset(0);setSearch("");setSortBy("");setNotice([result.message,...(result.warnings||[])].filter(Boolean).join(" ")); } catch {} };
  const handleSort = (name) => { if(sortBy===name)setSortDir(d=>d==="asc"?"desc":"asc");else{setSortBy(name);setSortDir("asc");}setOffset(0); };
  const handleSearch = (value) => { setSearch(value);setOffset(0); };
  const loading = dataset.isLoading || columns.isLoading || rows.isLoading;
  return <div className="flex flex-col gap-6 p-5 sm:p-8">
    <PageHeader eyebrow="Dataset workspace" title="Explore your data." description="A general-purpose view of any CSV, independent of its column names." action={<><input ref={fileRef} type="file" accept=".csv,text/csv" className="hidden" onChange={handleFile}/><button className="button-primary" onClick={()=>fileRef.current?.click()} disabled={upload.isPending}><FileSpreadsheet className="size-4"/>{upload.isPending?"Importing…":hasData?"Switch dataset":"Import CSV"}</button></>}/>
    {notice && <UploadNotice onDismiss={()=>setNotice("")}>{notice}</UploadNotice>}
    <ErrorNotice error={upload.error || dataset.error || columns.error || rows.error}/>
    {loading && <p className="text-xs text-slate-500">Loading dataset…</p>}
    {hasData && <div className="panel flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between"><div><div className="flex items-center gap-2 text-sm font-medium text-slate-100"><FileSpreadsheet className="size-4 text-cyan-200"/>{info.name || "Active dataset"}</div><p className="mt-1 text-xs text-slate-500">{Number(info.rows||0).toLocaleString()} rows × {Number(info.column_count||0).toLocaleString()} columns · Uploaded {dateLabel(info.uploaded_at)}</p></div><button className="button-secondary" onClick={()=>{dataset.refetch();columns.refetch();rows.refetch();suggestions.refetch()}}><RefreshCw className="size-3"/> Refresh</button></div>}
    <KpiGrid hasData={hasData} dataset={info}/>
    {!hasData && !loading && <div className="panel flex flex-col items-start gap-3 p-7"><div className="brand-mark"><FileSpreadsheet/></div><h2 className="text-base font-medium text-white">Start with any CSV dataset</h2><p className="max-w-xl text-sm text-slate-500">Upload a file to automatically profile its columns, check data quality, explore rows, and create charts. Column names do not need to follow a predefined schema.</p><button className="button-primary" onClick={()=>fileRef.current?.click()}>Choose CSV file</button></div>}
    {hasData && <>
      <ColumnProfile columns={profile} hasData={hasData}/>
      <SalesTable rows={rowData} columns={rowColumns} hasData={hasData} query={search} onQueryChange={handleSearch} offset={offset} limit={limit} total={rows.data?.pagination?.total ?? info.rows ?? 0} sortBy={sortBy} sortDir={sortDir} onSort={handleSort} onPage={(nextOffset,nextLimit)=>{setOffset(nextOffset);setLimit(nextLimit)}}/>
      {numericColumns.length>0 && <div className="panel flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between"><div><h3 className="text-sm font-medium text-slate-200">Numeric column total · current preview page</h3><p className="mt-1 text-xs text-slate-500">Optional quick calculation across the rows currently loaded in the preview.</p></div><div className="flex items-center gap-3"><select className="select-button bg-[#111923]" value={totalColumn} onChange={e=>setTotalColumn(e.target.value)}>{numericColumns.map(c=><option key={c.name} value={c.name}>{c.name}</option>)}</select><span className="text-lg font-semibold text-cyan-100">{numericTotal.toLocaleString(undefined,{maximumFractionDigits:2})}</span></div></div>}
      {(info.insights?.length>0 || suggestions.data?.questions?.length>0) && <div className="panel p-5"><h2 className="text-sm font-medium text-slate-200">Quick insights</h2><div className="mt-3 flex flex-wrap gap-2">{(info.insights||[]).map((insight,i)=><span key={`i-${i}`} className="rounded-lg border border-white/[0.07] bg-white/[0.025] px-3 py-2 text-xs text-slate-400">{typeof insight==="string"?insight:insight.text||insight.message||JSON.stringify(insight)}</span>)}{!(info.insights||[]).length && (suggestions.data?.questions||[]).slice(0,3).map(q=><button key={q} className="suggestion" onClick={()=>setActive("AI Analyst")}>{q}</button>)}</div></div>}
      <ChartStudio hasData={hasData} onAsk={onAskQuestion}/>
    </>}
    <AskAnalystBanner onOpen={()=>setActive("AI Analyst")}/>
  </div>;
}
