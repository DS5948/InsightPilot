
import { Bot, User, FileText, Database } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ChartRenderer from "@/components/dashboard/ChartRenderer";

export default function ChatMessage({
  role,
  text,
  sources = [],
  route,
  warnings = [],
  chart = null,
}) {
  const assistant = role === "assistant";

  return (
    <div className={`mb-5 flex gap-3 ${!assistant ? "justify-end" : ""}`}>
      <div
        className={`flex size-8 shrink-0 items-center justify-center rounded-lg ${
          assistant
            ? "bg-cyan-300/10 text-cyan-200"
            : "bg-violet-400/15 text-violet-200"
        }`}
      >
        {assistant ? (
          <Bot className="size-4" />
        ) : (
          <User className="size-4" />
        )}
      </div>

      <div
        className={`max-w-2xl min-w-0 rounded-xl border px-4 py-3 text-sm leading-6 ${
          assistant
            ? "border-white/[0.07] bg-white/[0.03] text-slate-300"
            : "border-violet-300/10 bg-violet-300/[0.08] text-slate-200"
        }`}
      >
        <div
          className={`break-words ${
            assistant ? "markdown-content" : "whitespace-pre-wrap"
          }`}
        >
          {assistant ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => (
                  <h1 className="mb-3 mt-4 text-xl font-bold text-white">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="mb-2 mt-4 text-lg font-semibold text-white">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="mb-2 mt-3 text-base font-semibold text-white">
                    {children}
                  </h3>
                ),
                p: ({ children }) => (
                  <p className="mb-3 last:mb-0">{children}</p>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-white">
                    {children}
                  </strong>
                ),
                ul: ({ children }) => (
                  <ul className="mb-3 ml-5 list-disc space-y-1">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="mb-3 ml-5 list-decimal space-y-1">
                    {children}
                  </ol>
                ),
                li: ({ children }) => <li className="pl-1">{children}</li>,
                blockquote: ({ children }) => (
                  <blockquote className="my-3 border-l-2 border-cyan-300/40 pl-3 text-slate-400">
                    {children}
                  </blockquote>
                ),
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyan-300 underline underline-offset-2"
                  >
                    {children}
                  </a>
                ),
                code: ({ children, className }) => {
                  const isBlock = Boolean(className);

                  return isBlock ? (
                    <code className={`${className} font-mono text-xs`}>
                      {children}
                    </code>
                  ) : (
                    <code className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-xs text-cyan-200">
                      {children}
                    </code>
                  );
                },
                pre: ({ children }) => (
                  <pre className="my-3 max-w-full overflow-x-auto rounded-lg border border-white/10 bg-black/30 p-3">
                    {children}
                  </pre>
                ),
                table: ({ children }) => (
                  <div className="my-3 max-w-full overflow-x-auto">
                    <table className="w-full border-collapse text-left text-xs">
                      {children}
                    </table>
                  </div>
                ),
                th: ({ children }) => (
                  <th className="border border-white/10 bg-white/[0.06] px-3 py-2 font-semibold text-white">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="border border-white/10 px-3 py-2 align-top">
                    {children}
                  </td>
                ),
                hr: () => <hr className="my-4 border-white/10" />,
              }}
            >
              {text || ""}
            </ReactMarkdown>
          ) : (
            text
          )}
        </div>

        {assistant && chart && <div className="mt-4"><ChartRenderer chart={chart} /></div>}

        {assistant && route && (
          <div className="mt-3 text-[10px] uppercase tracking-wider text-slate-500">
            Source route: {route}
          </div>
        )}

        {assistant && warnings.length > 0 && (
          <div className="mt-3 text-xs text-amber-200">
            {warnings.join(" · ")}
          </div>
        )}

        {assistant && sources.length > 0 && (
          <div className="mt-3 space-y-2 border-t border-white/[0.07] pt-3">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              Sources
            </div>

            {sources.map((source, index) => (
              <div
                key={`${source.label}-${index}`}
                className="rounded-lg bg-white/[0.03] p-3"
              >
                <div className="flex items-center gap-2 text-xs font-medium text-cyan-100">
                  {source.type === "document" ? (
                    <FileText className="size-3.5" />
                  ) : (
                    <Database className="size-3.5" />
                  )}
                  {source.label}
                </div>

                {source.excerpt && (
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    {source.excerpt}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
