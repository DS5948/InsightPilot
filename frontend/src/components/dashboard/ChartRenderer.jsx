import { useMemo, useState } from "react";
import { Download, Eye, Pin } from "lucide-react";

const COLORS = ["#83e5df", "#a99af8", "#f6c86d", "#7de0ad", "#f49eae", "#79b9f8", "#d6a3e8", "#b6d99a"];
const n = (v) => Number.isFinite(Number(v)) ? Number(v) : 0;
const fmt = (v) => n(v).toLocaleString(undefined, { maximumFractionDigits: 2 });
const esc = (value) => String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&apos;");
function downloadPng(svg, title) {
  if (!svg) return;
  const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob); const image = new Image();
  image.onload = () => { const canvas = document.createElement("canvas"); canvas.width = 1440; canvas.height = 600; const ctx = canvas.getContext("2d"); ctx.drawImage(image, 0, 0, canvas.width, canvas.height); URL.revokeObjectURL(url); canvas.toBlob((png) => { if (!png) return; const pngUrl = URL.createObjectURL(png); const a = document.createElement("a"); a.href = pngUrl; a.download = `${(title || "insightpilot-chart").replace(/[^a-z0-9-_]+/gi, "-")}.png`; a.click(); URL.revokeObjectURL(pngUrl); }, "image/png"); };
  image.onerror = () => URL.revokeObjectURL(url); image.src = url;
}

export default function ChartRenderer({ chart, onPin, pinned = false, onUnpin, pinning = false }) {
  const [showData, setShowData] = useState(false);
  const svgId = useMemo(() => `chart-${Math.random().toString(36).slice(2)}`, [chart?.title]);
  if (!chart) return null;
  const data = chart.data || []; const type = chart.chart || chart.spec?.chart || "bar";
  const series = chart.series?.length ? chart.series : [{ key: "s0", label: chart.y_label || "Value" }];
  const valuesForScale = type === "box" ? data.flatMap((d) => [n(d.min), n(d.max)]) : type === "heatmap" ? data.map((d) => n(d.value)) : type === "scatter" ? data.map((d) => n(d.y)) : data.flatMap((d) => series.map((s) => n(d[s.key])));
  const max = Math.max(1, ...valuesForScale);
  const min = Math.min(0, ...valuesForScale);
  const svg = (() => {
    const W = 720, H = 300, L = 62, R = 18, T = 18, B = 50, plotW = W-L-R, plotH=H-T-B;
    const base = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(chart.title || "Chart")}"><rect width="100%" height="100%" fill="#101721"/>`;
    const grid = [0, .25, .5, .75, 1].map((t) => `<line x1="${L}" x2="${W-R}" y1="${T+plotH*t}" y2="${T+plotH*t}" stroke="#ffffff" stroke-opacity=".09"/><text x="${L-9}" y="${T+plotH*t+4}" fill="#78869b" text-anchor="end" font-size="10">${fmt(max*(1-t))}</text>`).join("");
    let body = "";
    if (type === "scatter") {
      const xs=data.map(d=>n(d.x)), ys=data.map(d=>n(d.y)); const xmin=Math.min(...xs,0), xmax=Math.max(...xs,1), ymin=Math.min(...ys,0), ymax=Math.max(...ys,1);
      body=data.map((d,i)=>`<circle cx="${L+((n(d.x)-xmin)/(xmax-xmin||1))*plotW}" cy="${T+plotH-((n(d.y)-ymin)/(ymax-ymin||1))*plotH}" r="4" fill="${COLORS[i%COLORS.length]}" fill-opacity=".85"><title>${esc(String(d.series ?? ""))}: ${fmt(d.x)}, ${fmt(d.y)}</title></circle>`).join("");
    } else if (type === "heatmap") {
      const cols=chart.columns||[...new Set(data.map(d=>d.y))]; const xs=[...new Set(data.map(d=>d.x))]; const vals=data.map(d=>n(d.value)); const vmax=Math.max(1,...vals), cellW=plotW/Math.max(xs.length,1), cellH=plotH/Math.max(cols.length,1);
      body=data.map(d=>{const xi=xs.indexOf(d.x), yi=cols.indexOf(d.y), alpha=Math.min(1,Math.abs(n(d.value))/vmax);return `<rect x="${L+xi*cellW+1}" y="${T+yi*cellH+1}" width="${Math.max(1,cellW-2)}" height="${Math.max(1,cellH-2)}" rx="3" fill="#83e5df" fill-opacity="${.12+.78*alpha}"><title>${esc(d.x)} / ${esc(d.y)}: ${fmt(d.value)}</title></rect><text x="${L+(xi+.5)*cellW}" y="${T+(yi+.5)*cellH+3}" fill="#e8f4f5" text-anchor="middle" font-size="10">${fmt(d.value)}</text>`}).join("")+cols.map((c,i)=>`<text x="${L-8}" y="${T+(i+.5)*cellH+3}" text-anchor="end" fill="#9aa7b9" font-size="10">${esc(String(c).slice(0,12))}</text>`).join("");
    } else if (type === "box") {
      const groups=data.slice(0,12), groupW=plotW/Math.max(groups.length,1); body=groups.map((d,i)=>{const y=(v)=>T+plotH-(n(v)-min)/(max-min||1)*plotH;const x=L+(i+.5)*groupW;return `<line x1="${x}" x2="${x}" y1="${y(d.min)}" y2="${y(d.max)}" stroke="#83e5df"/><rect x="${x-groupW*.22}" y="${y(d.q3)}" width="${groupW*.44}" height="${Math.max(2,y(d.q1)-y(d.q3))}" fill="#83e5df" fill-opacity=".4" stroke="#83e5df"/><line x1="${x-groupW*.22}" x2="${x+groupW*.22}" y1="${y(d.median)}" y2="${y(d.median)}" stroke="#f6c86d" stroke-width="2"/><text x="${x}" y="${H-24}" fill="#8b98aa" font-size="10" text-anchor="middle">${esc(String(d.x).slice(0,12))}</text>`}).join("");
    } else if (type === "pie") {
      const values=data.map(d=>Math.max(0,n(d[series[0].key]))), total=values.reduce((a,b)=>a+b,0)||1; let angle=-Math.PI/2;
      body=data.map((d,i)=>{const portion=values[i]/total, next=angle+portion*Math.PI*2, x1=360+110*Math.cos(angle), y1=145+110*Math.sin(angle), x2=360+110*Math.cos(next), y2=145+110*Math.sin(next), large=portion>.5?1:0;const path=`M 360 145 L ${x1} ${y1} A 110 110 0 ${large} 1 ${x2} ${y2} Z`;const piece=`<path d="${path}" fill="${COLORS[i%COLORS.length]}" stroke="#101721" stroke-width="2"><title>${esc(String(d.x))}: ${fmt(values[i])} (${(portion*100).toFixed(1)}%)</title></path>`;angle=next;return piece}).join("")+data.slice(0,8).map((d,i)=>`<rect x="${520+(i%2)*92}" y="${55+Math.floor(i/2)*38}" width="9" height="9" rx="2" fill="${COLORS[i%COLORS.length]}"/><text x="${534+(i%2)*92}" y="${64+Math.floor(i/2)*38}" fill="#a6b2c2" font-size="10">${esc(String(d.x).slice(0,12))}</text>`).join("");
    } else if (type === "histogram") {
      const bw=plotW/Math.max(data.length,1); body=data.map((d,i)=>{const v=n(d[series[0].key]);return `<rect x="${L+i*bw+2}" y="${T+plotH-v/max*plotH}" width="${Math.max(1,bw-4)}" height="${Math.max(0,v/max*plotH)}" rx="3" fill="${COLORS[0]}" fill-opacity=".8"><title>${esc(d.x)}: ${fmt(v)}</title></rect><text x="${L+(i+.5)*bw}" y="${H-24}" fill="#8b98aa" font-size="9" text-anchor="middle">${esc(String(d.x).slice(0,10))}</text>`}).join("");
    } else {
      const count=Math.max(data.length,1), groupW=plotW/count, barW=groupW/Math.max(series.length,1)*.72;
      body=data.map((d,i)=>series.map((s,j)=>{const v=n(d[s.key]), h=Math.max(0,v/max*plotH), x=L+i*groupW+j*barW;return type==="line"?"":`<rect x="${x+groupW*.12}" y="${T+plotH-h}" width="${Math.max(1,barW-2)}" height="${h}" rx="3" fill="${COLORS[j%COLORS.length]}" fill-opacity=".85"><title>${esc(String(d.x))} · ${esc(s.label)}: ${fmt(v)}</title></rect>`}).join("")+`<text x="${L+(i+.5)*groupW}" y="${H-24}" fill="#8b98aa" font-size="10" text-anchor="middle">${esc(String(d.x).slice(0,12))}</text>`).join("");
      if(type==="line") body=series.map((s,j)=>{const pts=data.map((d,i)=>`${L+(i+.5)*groupW},${T+plotH-n(d[s.key])/max*plotH}`).join(" ");return `<polyline points="${pts}" fill="none" stroke="${COLORS[j%COLORS.length]}" stroke-width="3" stroke-linejoin="round"/>`+data.map((d,i)=>`<circle cx="${L+(i+.5)*groupW}" cy="${T+plotH-n(d[s.key])/max*plotH}" r="3.5" fill="${COLORS[j%COLORS.length]}"><title>${esc(String(d.x))}: ${fmt(d[s.key])}</title></circle>`).join("")}).join("");
    }
    return `${base}${type !== "pie" && type !== "heatmap" ? grid : ""}${body}</svg>`;
  })();
  const csv = [Object.keys(data[0] || {}).join(","), ...data.map(row => Object.values(row).map(v => `"${String(v ?? "").replaceAll('"','""')}"`).join(","))].join("\n");
  return <div className="panel overflow-hidden">
    <div className="flex flex-wrap items-start justify-between gap-3 border-b border-white/[0.07] p-4"><div><h3 className="text-sm font-medium text-slate-100">{chart.title || "Chart"}</h3><p className="mt-1 text-[11px] text-slate-500">{chart.rows_used != null ? `${chart.rows_used.toLocaleString()} rows used` : "Computed from the active dataset"}</p></div><div className="flex flex-wrap gap-2">
      {onPin && <button className="button-secondary" disabled={pinning || pinned} onClick={() => onPin(chart.spec, chart.title)}><Pin className="size-3"/>{pinned ? "Pinned" : pinning ? "Pinning…" : "Pin"}</button>}
      {onUnpin && <button className="button-secondary" onClick={onUnpin}>Unpin</button>}
      <button className="button-secondary" onClick={() => {const blob=new Blob([csv],{type:"text/csv;charset=utf-8"});const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="chart-data.csv";a.click();URL.revokeObjectURL(url)}}>Export data</button>
      <button className="button-secondary" onClick={() => downloadPng(document.getElementById(svgId)?.outerHTML, chart.title)}><Download className="size-3"/>PNG</button>
      <button className="button-secondary" onClick={() => setShowData(v=>!v)}><Eye className="size-3"/>{showData ? "Hide data" : "Show data"}</button>
    </div></div>
    <div className="p-3"><div className="w-full overflow-x-auto"><div className="mx-auto min-w-[500px] max-w-4xl" dangerouslySetInnerHTML={{__html: svg.replace('<svg ', `<svg id="${svgId}" `)}} /></div></div>
    {chart.notes?.length > 0 && <div className="px-5 pb-3 text-xs text-slate-500">{chart.notes.join(" · ")}</div>}
    {showData && <div className="overflow-x-auto border-t border-white/[0.07]"><table><thead><tr>{Object.keys(data[0] || {}).map(k=><th key={k}>{k}</th>)}</tr></thead><tbody>{data.map((row,i)=><tr key={i}>{Object.values(row).map((v,j)=><td key={j}>{v == null ? "—" : String(v)}</td>)}</tr>)}</tbody></table></div>}
  </div>;
}
