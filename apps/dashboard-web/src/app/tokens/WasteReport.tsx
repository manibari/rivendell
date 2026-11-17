"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { apiFetch } from "@/lib/api";

interface ReportSummary {
  name: string;
  day: string;
  host: string;
  updated_at: string;
  window: [string, string] | null;
  failed: boolean;
}

interface ReportDetail {
  name: string;
  updated_at: string;
  markdown: string;
}

const sectionH2: React.CSSProperties = {
  fontSize: 18,
  fontWeight: 500,
  color: "var(--text)",
  letterSpacing: "-0.01em",
};

export default function WasteReport() {
  const [reports, setReports] = useState<ReportSummary[] | null>(null);
  const [selected, setSelected] = useState("");
  const [detail, setDetail] = useState<ReportDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    apiFetch<{ reports: ReportSummary[] }>("/api/tokens/waste-reports")
      .then(({ reports: items }) => {
        if (!active) return;
        setReports(items);
        setSelected(items[0]?.name ?? "");
      })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : String(cause));
      });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!selected) return;
    let active = true;
    apiFetch<ReportDetail>(`/api/tokens/waste-reports/${encodeURIComponent(selected)}`)
      .then((report) => {
        if (!active) return;
        setDetail(report);
        setError(null);
      })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : String(cause));
      });
    return () => { active = false; };
  }, [selected]);

  const current = reports?.find((report) => report.name === selected);

  return (
    <section className="mt-8">
      <h2 className="mb-3" style={sectionH2}>疑似浪費報告</h2>
      <p className="mb-4 text-sm" style={{ color: "var(--text-muted)" }}>
        Gemini 依各 session 的 token 數字標出疑似浪費；數字是估計上限。
      </p>

      {reports && reports.length > 0 && (
        <div className="mb-4">
          <label htmlFor="waste-report-select" className="mr-2 text-sm" style={{ color: "var(--text-muted)" }}>
            選擇報告
          </label>
          <select
            id="waste-report-select"
            value={selected}
            onChange={(event) => {
              setDetail(null);
              setError(null);
              setSelected(event.target.value);
            }}
            className="max-w-full rounded px-2 py-1 text-sm"
            style={{ background: "var(--surface)", border: "1px solid var(--border)", color: "var(--text)" }}
          >
            {reports.map((report) => (
              <option key={report.name} value={report.name}>
                {report.day} · {report.host}{report.failed ? "（判讀失敗）" : ""}
              </option>
            ))}
          </select>
        </div>
      )}

      {error ? (
        <p style={{ color: "var(--status-err)" }}>讀不到報告：{error}</p>
      ) : reports === null || (reports.length > 0 && !detail) ? (
        <p style={{ color: "var(--text-muted)" }}>載入中...</p>
      ) : reports.length === 0 ? (
        <p style={{ color: "var(--text-muted)" }}>還沒有報告。對 Claude 說「監控 token」就會開始產生。</p>
      ) : detail && current ? (
        <>
          <p className="mb-3 text-xs" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            更新時間 {detail.updated_at}
            {current.window && <> · 資料區間 {current.window[0]} 到 {current.window[1]}</>}
          </p>
          <article
            className="prose prose-sm max-w-none p-4 sm:p-6 prose-p:[overflow-wrap:anywhere] prose-li:[overflow-wrap:anywhere] prose-code:before:content-none prose-code:after:content-none"
            style={{ color: "var(--text)", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)", minWidth: 0 }}
          >
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // `node` is react-markdown's AST node; it must not reach the DOM.
                // A fixed minimum width keeps cells readable; the box scrolls instead.
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
                table: ({ node: _node, children, ...props }) => (
                  <div className="max-w-full overflow-x-auto">
                    <table {...props} style={{ minWidth: 720 }}>{children}</table>
                  </div>
                ),
              }}
            >
              {detail.markdown}
            </ReactMarkdown>
          </article>
        </>
      ) : null}
    </section>
  );
}
