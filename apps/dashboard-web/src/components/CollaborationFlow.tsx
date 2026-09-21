"use client";

import { useEffect, useState } from "react";
import { apiFetch, type CollaborationData } from "@/lib/api";

const cardStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
};

const preStyle: React.CSSProperties = {
  background: "var(--surface-2)",
  color: "var(--text)",
  borderRadius: "var(--radius-sm)",
  padding: "12px",
  fontSize: 12,
  fontFamily: "var(--font-mono)",
  border: "1px solid var(--border)",
};

const h2Style: React.CSSProperties = {
  fontSize: 18,
  fontWeight: 500,
  color: "var(--text)",
  letterSpacing: "-0.01em",
};

export default function CollaborationFlow() {
  const [data, setData] = useState<CollaborationData | null>(null);

  useEffect(() => {
    apiFetch<CollaborationData>("/api/collaboration")
      .then(setData)
      .catch(() => {});
  }, []);

  if (!data) return null;

  if (!data.found) {
    return (
      <div className="mt-6">
        <h2 style={h2Style}>Agent 協作流</h2>
        <p
          className="mt-2 text-sm"
          style={{ color: "var(--text-muted)" }}
        >
          尚無 .learnings/ERRORS.md 資料。Agent 執行後會自動產生。
        </p>
        <pre className="mt-2" style={preStyle}>
{`tester 發現 bug → .learnings/ERRORS.md → maintainer 修復 → resolved`}
        </pre>
      </div>
    );
  }

  return (
    <div className="mt-6">
      <h2 style={h2Style}>Agent 協作流</h2>
      <div className="mt-3 grid grid-cols-3 gap-4">
        {[
          { label: "Pending 問題", value: data.pending },
          { label: "已解決", value: data.resolved },
          { label: "解決率", value: `${data.resolution_rate}%` },
        ].map((m) => (
          <div key={m.label} className="p-3" style={cardStyle}>
            <p
              className="font-mono text-[10px] uppercase"
              style={{
                color: "var(--text-subtle)",
                letterSpacing: "0.1em",
              }}
            >
              {m.label}
            </p>
            <p
              className="mt-1 tabular-nums"
              style={{
                color: "var(--text)",
                fontSize: 22,
                fontWeight: 500,
                fontFamily: "var(--font-mono)",
              }}
            >
              {m.value}
            </p>
          </div>
        ))}
      </div>
      <pre className="mt-3" style={preStyle}>
{`tester 發現 bug (${data.pending} pending)
      ↓
.learnings/ERRORS.md
      ↓
maintainer 修復 (${data.resolved} resolved)`}
      </pre>
    </div>
  );
}
