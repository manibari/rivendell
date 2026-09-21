"use client";

import { useEffect, useState } from "react";
import { apiFetch, type GitHealthData } from "@/lib/api";
import StatusDot from "@/components/StatusDot";

const TH =
  "py-2 px-4 text-left font-mono text-[10px] uppercase";
const thStyle = { color: "var(--text-subtle)", letterSpacing: "0.08em" } as const;

export default function GitHealthPage() {
  const [data, setData] = useState<GitHealthData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<GitHealthData>("/api/health/git")
      .then(setData)
      .catch((e) => setErr(e.message));
  }, []);

  const flagged = data ? data.dirty + data.unpushed : null;
  const dot = flagged === null ? "idle" : flagged === 0 ? "ok" : "warn";
  const label =
    flagged === null ? "—" : flagged === 0 ? "全部乾淨" : `${data!.dirty} 未提交 · ${data!.unpushed} 未推送`;

  return (
    <div>
      <div className="mb-2 flex items-center gap-3">
        <h1
          className="tracking-tight"
          style={{ fontSize: 28, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.02em" }}
        >
          Git 衛生
        </h1>
        {data && <StatusDot status={dot} label={label} />}
      </div>

      <p className="mb-5 max-w-3xl text-sm" style={{ color: "var(--text-muted)", lineHeight: 1.55 }}>
        掃描 <code className="font-mono">{data ? data.root : "~/code"}</code> 下所有 git repo 的未提交檔案數與
        ahead/behind。提醒哪些工作還沒 commit / push。
      </p>

      {err && <p style={{ color: "var(--status-err)" }}>Error: {err}</p>}
      {!err && !data && <p style={{ color: "var(--text-muted)" }}>載入中...</p>}

      {data && (
        <div
          className="overflow-x-auto"
          style={{ border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}
        >
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: "var(--surface-2)", borderBottom: "1px solid var(--border)" }}>
                <th className={TH} style={thStyle}>Repo</th>
                <th className={TH} style={thStyle}>分支</th>
                <th className={TH} style={thStyle}>未提交</th>
                <th className={TH} style={thStyle}>未推送</th>
                <th className={TH} style={thStyle}>落後</th>
              </tr>
            </thead>
            <tbody>
              {data.repos.map((r) => {
                const clean = r.dirty === 0 && r.ahead === 0;
                return (
                  <tr key={r.name} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td className="py-2 px-4 font-medium" style={{ color: "var(--text)" }}>
                      {r.name}
                    </td>
                    <td className="py-2 px-4 font-mono text-xs" style={{ color: "var(--text-muted)" }}>
                      {r.branch}
                      {!r.has_upstream && (
                        <span style={{ color: "var(--text-subtle)" }}> (無 upstream)</span>
                      )}
                    </td>
                    <td
                      className="py-2 px-4 font-mono tabular-nums"
                      style={{ color: r.dirty > 0 ? "var(--status-warn)" : "var(--text-subtle)" }}
                    >
                      {r.dirty || "—"}
                    </td>
                    <td
                      className="py-2 px-4 font-mono tabular-nums"
                      style={{ color: r.ahead > 0 ? "var(--status-warn)" : "var(--text-subtle)" }}
                    >
                      {r.ahead ? `↑${r.ahead}` : clean ? "✓" : "—"}
                    </td>
                    <td
                      className="py-2 px-4 font-mono tabular-nums"
                      style={{ color: "var(--text-subtle)" }}
                    >
                      {r.behind ? `↓${r.behind}` : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
