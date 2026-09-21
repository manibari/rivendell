"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, type GitHealthData } from "@/lib/api";
import StatusDot from "@/components/StatusDot";

export default function GitHealthCard() {
  const [data, setData] = useState<GitHealthData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<GitHealthData>("/api/health/git")
      .then(setData)
      .catch((e) => setErr(e.message));
  }, []);

  const flagged = data ? data.dirty + data.unpushed : null;
  const dot = flagged === null ? "idle" : flagged === 0 ? "ok" : "warn";
  const label = flagged === null ? "—" : flagged === 0 ? "乾淨" : "待處理";

  return (
    <Link
      href="/health/git"
      className="block p-4 transition-colors"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-md)",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--border-strong)")}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
    >
      <div className="flex items-center justify-between">
        <p
          className="font-mono text-[10px] uppercase"
          style={{ color: "var(--text-subtle)", letterSpacing: "0.1em" }}
        >
          Git 衛生
        </p>
        <StatusDot status={dot} label={label} />
      </div>

      {err ? (
        <p className="mt-2 text-sm" style={{ color: "var(--status-err)" }}>
          無法讀取
        </p>
      ) : (
        <>
          <div className="mt-1 flex items-baseline gap-2">
            <span
              className="tabular-nums"
              style={{
                color: "var(--text)",
                fontSize: 24,
                fontWeight: 500,
                fontFamily: "var(--font-mono)",
              }}
            >
              {data ? data.dirty : "…"}
            </span>
            <span
              className="text-[13px]"
              style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            >
              未提交{data && data.unpushed > 0 ? ` · ${data.unpushed} 未推送` : ""}
            </span>
          </div>
          <p
            className="mt-2 font-mono text-[10px] uppercase"
            style={{ color: "var(--text-subtle)", letterSpacing: "0.08em" }}
          >
            {data ? `${data.total} repos` : "~/code"} · 明細 →
          </p>
        </>
      )}
    </Link>
  );
}
