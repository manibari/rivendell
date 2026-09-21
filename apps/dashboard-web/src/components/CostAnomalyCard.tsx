"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, type TokensData } from "@/lib/api";
import StatusDot from "@/components/StatusDot";

const SPIKE_RATIO = 1.5; // last day > 1.5× trailing-7d avg → flag

export default function CostAnomalyCard() {
  const [daily, setDaily] = useState<{ date: string; cost: number }[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<TokensData>("/api/tokens")
      .then((d) => {
        const rows = [...d.daily]
          .map((r) => ({ date: r.date, cost: r.cost_usd }))
          .sort((a, b) => a.date.localeCompare(b.date));
        setDaily(rows);
      })
      .catch((e) => setErr(e.message));
  }, []);

  const last = daily && daily.length > 0 ? daily[daily.length - 1] : null;
  const prior = daily ? daily.slice(0, -1).slice(-7) : [];
  const avg = prior.length > 0 ? prior.reduce((s, r) => s + r.cost, 0) / prior.length : 0;
  const enough = daily !== null && daily.length >= 3;
  const spike = enough && avg > 0 && last !== null && last.cost > SPIKE_RATIO * avg;

  const dot = daily === null ? "idle" : !enough ? "idle" : spike ? "warn" : "ok";
  const label = daily === null ? "—" : !enough ? "資料不足" : spike ? "偏高" : "正常";

  // Sparkline over the last 14 days
  const spark = daily ? daily.slice(-14) : [];
  const maxCost = spark.length > 0 ? Math.max(...spark.map((r) => r.cost), 0.0001) : 1;
  const W = 120;
  const H = 28;
  const pts = spark
    .map((r, i) => {
      const x = spark.length > 1 ? (i / (spark.length - 1)) * W : 0;
      const y = H - (r.cost / maxCost) * (H - 2) - 1;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <Link
      href="/tokens"
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
          成本趨勢
        </p>
        <StatusDot status={dot} label={label} />
      </div>

      {err ? (
        <p className="mt-2 text-sm" style={{ color: "var(--status-err)" }}>
          無法讀取
        </p>
      ) : (
        <>
          <div className="mt-1 flex items-end justify-between gap-2">
            <div className="flex items-baseline gap-2">
              <span
                className="tabular-nums"
                style={{
                  color: "var(--text)",
                  fontSize: 24,
                  fontWeight: 500,
                  fontFamily: "var(--font-mono)",
                }}
              >
                {last ? `$${last.cost.toFixed(2)}` : "…"}
              </span>
              <span
                className="text-[13px]"
                style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
              >
                近7日均 ${avg.toFixed(2)}
              </span>
            </div>
            {spark.length > 1 && (
              <svg width={W} height={H} style={{ overflow: "visible", flexShrink: 0 }} aria-hidden>
                <polyline
                  points={pts}
                  fill="none"
                  stroke={spike ? "var(--status-warn)" : "var(--accent)"}
                  strokeWidth={1.5}
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />
              </svg>
            )}
          </div>
          <p
            className="mt-2 font-mono text-[10px] uppercase"
            style={{ color: "var(--text-subtle)", letterSpacing: "0.08em" }}
          >
            最近一日 · 近 14 日趨勢 · Token 用量 →
          </p>
        </>
      )}
    </Link>
  );
}
