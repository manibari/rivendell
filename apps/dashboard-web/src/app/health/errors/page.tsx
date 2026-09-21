"use client";

import { useEffect, useState } from "react";
import { apiFetch, type RecentErrorsData } from "@/lib/api";
import StatusDot from "@/components/StatusDot";

function humanBytes(n: number): string {
  if (n >= 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
  if (n >= 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${n} B`;
}

export default function RecentErrorsPage() {
  const [data, setData] = useState<RecentErrorsData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<RecentErrorsData>("/api/health/errors")
      .then(setData)
      .catch((e) => setErr(e.message));
  }, []);

  const total = data ? data.total : null;
  const dot = total === null ? "idle" : total === 0 ? "ok" : "warn";
  const label = total === null ? "—" : total === 0 ? "無錯誤" : `${total} 筆`;

  return (
    <div>
      <div className="mb-2 flex items-center gap-3">
        <h1
          className="tracking-tight"
          style={{ fontSize: 28, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.02em" }}
        >
          最近錯誤
        </h1>
        {data && <StatusDot status={dot} label={label} />}
      </div>

      <p className="mb-5 max-w-3xl text-sm" style={{ color: "var(--text-muted)", lineHeight: 1.55 }}>
        近 {data ? data.recent_days : 14} 天內<u>非空</u>的 agent error log（<code className="font-mono">reports/*-error.log</code>，
        排程任務捕捉的 stderr）。與 Pending Issues 互補：那裡顯示 exit code，這裡顯示實際錯誤文字。空清單代表每次排程都沒寫出 stderr。
      </p>

      {err && <p style={{ color: "var(--status-err)" }}>Error: {err}</p>}
      {!err && !data && <p style={{ color: "var(--text-muted)" }}>載入中...</p>}

      {data && data.total === 0 && (
        <div
          className="p-6"
          style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}
        >
          <p style={{ color: "var(--status-ok)" }}>✓ 近 {data.recent_days} 天無 agent 錯誤輸出。</p>
        </div>
      )}

      {data && data.errors.length > 0 && (
        <div className="space-y-4">
          {data.errors.map((e) => (
            <div
              key={e.name}
              style={{ border: "1px solid var(--border)", borderRadius: "var(--radius-md)", overflow: "hidden" }}
            >
              <div
                className="flex items-center justify-between px-4 py-2"
                style={{ background: "var(--surface-2)", borderBottom: "1px solid var(--border)" }}
              >
                <span className="font-mono text-sm" style={{ color: "var(--text)" }}>
                  {e.name}
                </span>
                <span className="font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
                  {humanBytes(e.size)} · {new Date(e.mtime).toLocaleString("zh-TW")}
                </span>
              </div>
              <pre
                className="overflow-x-auto px-4 py-3 text-xs"
                style={{
                  background: "var(--surface)",
                  color: "var(--text-muted)",
                  fontFamily: "var(--font-mono)",
                  lineHeight: 1.5,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {e.tail || "(內容過大，已截斷)"}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
