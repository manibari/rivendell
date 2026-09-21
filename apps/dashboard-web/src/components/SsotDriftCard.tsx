"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, type HealthData, type SsotDriftInfo } from "@/lib/api";
import StatusDot from "@/components/StatusDot";

type Dot = "ok" | "warn" | "err" | "idle";

function statusOf(drift: number | null): { dot: Dot; label: string } {
  if (drift === null) return { dot: "idle", label: "—" };
  if (drift < 0) return { dot: "err", label: "檢查失敗" };
  if (drift === 0) return { dot: "ok", label: "一致" };
  return { dot: "warn", label: "有漂移" };
}

export default function SsotDriftCard() {
  const [ssot, setSsot] = useState<SsotDriftInfo | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<HealthData>("/api/health")
      .then((d) => setSsot(d.ssot_drift))
      .catch((e) => setErr(e.message));
  }, []);

  const drift = ssot ? ssot.total_drift : null;
  const meta = statusOf(drift);

  return (
    <Link
      href="/health/ssot"
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
          SSOT 漂移
        </p>
        <StatusDot status={meta.dot} label={meta.label} />
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
              {drift === null ? "…" : drift < 0 ? "!" : drift}
            </span>
            <span
              className="text-[13px]"
              style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            >
              {drift !== null && drift > 0 ? "筆不一致" : "筆"}
            </span>
          </div>
          <p
            className="mt-2 font-mono text-[10px] uppercase"
            style={{ color: "var(--text-subtle)", letterSpacing: "0.08em" }}
          >
            agents.conf ↔ projects.json · 明細 →
          </p>
        </>
      )}
    </Link>
  );
}
