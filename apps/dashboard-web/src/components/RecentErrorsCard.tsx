"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, type RecentErrorsData } from "@/lib/api";
import StatusDot from "@/components/StatusDot";

export default function RecentErrorsCard() {
  const [data, setData] = useState<RecentErrorsData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<RecentErrorsData>("/api/health/errors")
      .then(setData)
      .catch((e) => setErr(e.message));
  }, []);

  const total = data ? data.total : null;
  const dot = total === null ? "idle" : total === 0 ? "ok" : "warn";
  const label = total === null ? "—" : total === 0 ? "無" : "有錯誤";

  return (
    <Link
      href="/health/errors"
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
          最近錯誤
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
              {total === null ? "…" : total}
            </span>
            <span
              className="text-[13px]"
              style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            >
              筆非空 error log
            </span>
          </div>
          <p
            className="mt-2 font-mono text-[10px] uppercase"
            style={{ color: "var(--text-subtle)", letterSpacing: "0.08em" }}
          >
            reports/*-error.log · 近 {data ? data.recent_days : 14} 天 · 明細 →
          </p>
        </>
      )}
    </Link>
  );
}
