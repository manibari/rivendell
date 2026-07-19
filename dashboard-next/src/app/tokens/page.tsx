"use client";

import { useEffect, useState } from "react";
import { apiFetch, type FilteredTokensData } from "@/lib/api";
import MetricsRow from "@/components/MetricsRow";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

// Re-color recharts to use our token system. We can't use CSS variables
// directly inside recharts props (it expects literal hex), so we read the
// computed root style at render time.
const ACCENT = "#2d4a3e";
const ACCENT_SOFT = "#5b7a6a";
// Palest step of the sequential-green ramp (DESIGN.md Color rules) — used for the
// context/cache_read mass, which dwarfs real output ~280×, so it must recede.
const CACHE_GREEN = "#d1ddd5";
const BORDER = "#e5e7eb";
const TEXT_SUBTLE = "#9ca3af";
const SURFACE = "#ffffff";

const tableHeader = (label: string, align: "left" | "right" = "left") => (
  <th
    className="px-4 py-2 font-mono text-[10px] uppercase"
    style={{
      color: "var(--text-subtle)",
      letterSpacing: "0.08em",
      textAlign: align,
    }}
  >
    {label}
  </th>
);

const headerRowStyle: React.CSSProperties = {
  background: "var(--surface-2)",
  borderBottom: "1px solid var(--border)",
};

const tableWrap: React.CSSProperties = {
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
  background: "var(--surface)",
};

const sectionH2: React.CSSProperties = {
  fontSize: 18,
  fontWeight: 500,
  color: "var(--text)",
  letterSpacing: "-0.01em",
};

// Default view = the last 30 days (2026-07-05, Peter): the all-time chart packs
// 90+ daily bars into one row and the x-axis labels collide (破圖). Clearing
// both date fields still shows all-time.
const isoDaysAgo = (days: number) => {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
};

export default function TokensPage() {
  const [dateStart, setDateStart] = useState(() => isoDaysAgo(30));
  const [dateEnd, setDateEnd] = useState(() => isoDaysAgo(0));
  const [data, setData] = useState<FilteredTokensData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    // Route default load to /api/tokens (cached, all-time). Only hit /filtered
    // when user actually picks a date — that path re-parses JSONL.
    let endpoint: string;
    if (dateStart || dateEnd) {
      const params = new URLSearchParams();
      if (dateStart) params.set("date_start", dateStart);
      if (dateEnd) params.set("date_end", dateEnd);
      endpoint = `/api/tokens/filtered?${params.toString()}`;
    } else {
      endpoint = `/api/tokens`;
    }
    apiFetch<FilteredTokensData>(endpoint)
      .then(setData)
      .catch((e) => setErr(e.message));
  }, [dateStart, dateEnd]);

  if (err)
    return <p style={{ color: "var(--status-err)" }}>Error: {err}</p>;
  if (!data)
    return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;

  const dateInputStyle: React.CSSProperties = {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    color: "var(--text)",
    fontFamily: "var(--font-mono)",
    borderRadius: "var(--radius-sm)",
    padding: "4px 8px",
  };

  const tooltipStyle: React.CSSProperties = {
    background: SURFACE,
    border: `1px solid ${BORDER}`,
    borderRadius: 4,
    fontFamily: "var(--font-mono)",
    fontSize: 12,
  };

  return (
    <div>
      <h1
        className="mb-6 tracking-tight"
        style={{
          fontSize: 28,
          fontWeight: 500,
          color: "var(--text)",
          letterSpacing: "-0.02em",
        }}
      >
        Token 用量
      </h1>

      {/* Date filter */}
      <div className="mb-6 flex items-center gap-3 text-sm">
        <label style={{ color: "var(--text-muted)" }}>
          從{" "}
          <input
            type="date"
            value={dateStart}
            onChange={(e) => setDateStart(e.target.value)}
            style={dateInputStyle}
          />
        </label>
        <label style={{ color: "var(--text-muted)" }}>
          到{" "}
          <input
            type="date"
            value={dateEnd}
            onChange={(e) => setDateEnd(e.target.value)}
            style={dateInputStyle}
          />
        </label>
        {(dateStart || dateEnd) && (
          <button
            onClick={() => {
              setDateStart("");
              setDateEnd("");
            }}
            className="text-xs hover:underline"
            style={{ color: "var(--accent)" }}
          >
            清除
          </button>
        )}
      </div>

      <MetricsRow
        metrics={[
          {
            label: "總 Session",
            value: data.total_sessions.toLocaleString(),
          },
          {
            label: "總 Messages",
            value: data.total_messages.toLocaleString(),
          },
          {
            label: "產出 Tokens (in+out)",
            value: data.total_tokens.toLocaleString(),
          },
          {
            label: "Context 重讀 (cache)",
            value: (data.total_cache_tokens ?? 0).toLocaleString(),
          },
          {
            label: "估算花費 (API 等值·非實付)",
            value: `$${data.total_cost_usd.toFixed(2)}`,
          },
        ]}
      />

      {/* Daily usage chart — recharts re-colored with token palette */}
      {data.daily.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3" style={sectionH2}>
            每日 Token 吞吐（產出 vs context 重讀）
          </h2>
          <p className="mb-2" style={{ fontSize: 11, color: TEXT_SUBTLE, fontFamily: "monospace" }}>
            雙軸：深綠＝產出 (左軸·百萬)，淺綠＝context 重讀 (右軸·十億)。
            兩者各自刻度，因 context 是產出的 ~280×，不能共用一軸。
          </p>
          <div className="h-64 w-full" style={tableWrap}>
            <ResponsiveContainer width="100%" height={256}>
              <BarChart
                data={data.daily}
                margin={{ top: 16, right: 8, bottom: 16, left: 0 }}
                barGap={1}
              >
                <CartesianGrid stroke={BORDER} strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10, fill: TEXT_SUBTLE, fontFamily: "monospace" }}
                  tickFormatter={(v: string) => v.slice(5)}
                  stroke={BORDER}
                />
                <YAxis
                  yAxisId="out"
                  orientation="left"
                  tick={{ fontSize: 10, fill: ACCENT, fontFamily: "monospace" }}
                  stroke={ACCENT}
                  tickFormatter={(v: number) =>
                    v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : `${(v / 1e3).toFixed(0)}K`
                  }
                />
                <YAxis
                  yAxisId="cache"
                  orientation="right"
                  tick={{ fontSize: 10, fill: ACCENT_SOFT, fontFamily: "monospace" }}
                  stroke={ACCENT_SOFT}
                  tickFormatter={(v: number) =>
                    v >= 1e9 ? `${(v / 1e9).toFixed(1)}B` : `${(v / 1e6).toFixed(0)}M`
                  }
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(value) => Number(value).toLocaleString()}
                  cursor={{ fill: "var(--surface-2)" }}
                />
                <Legend wrapperStyle={{ fontSize: 11, fontFamily: "monospace" }} />
                {/* Dual-axis grouped (NOT stacked): output and context are ~280×
                    apart, so a shared linear axis buries output as a 1px sliver.
                    Each series rides its own axis — output on the left (millions),
                    context on the right (billions) — so both show real height and
                    you can read the daily work rhythm AND the context mass. */}
                <Bar
                  yAxisId="out"
                  dataKey="tokens_total"
                  fill={ACCENT}
                  name="產出 (in+out) ·左軸"
                  isAnimationActive={false}
                />
                <Bar
                  yAxisId="cache"
                  dataKey="cache_tokens"
                  fill={CACHE_GREEN}
                  name="Context 重讀 (cache) ·右軸"
                  isAnimationActive={false}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* Daily cost chart removed 2026-07-19: the $ was fiction for a Max
          flat-fee user (cache_read × opus-default pricing, no per-token bill).
          Dollar figures now survive only as labeled "API 等值·非實付" reference
          columns in the tables below. See the dual-axis throughput chart above
          for the honest daily picture. */}

      {/* Model breakdown */}
      <section className="mt-8">
        <h2 className="mb-3" style={sectionH2}>
          模型用量
        </h2>
        <div className="overflow-x-auto" style={tableWrap}>
          <table className="w-full text-sm">
            <thead>
              <tr style={headerRowStyle}>
                {tableHeader("Model")}
                {tableHeader("Input", "right")}
                {tableHeader("Output", "right")}
                {tableHeader("Cost", "right")}
              </tr>
            </thead>
            <tbody>
              {data.models.map((m) => (
                <tr
                  key={m.model}
                  style={{ borderBottom: "1px solid var(--border)" }}
                >
                  <td className="px-4 py-2 font-mono text-xs" style={{ color: "var(--text)" }}>
                    {m.model}
                  </td>
                  <td className="px-4 py-2 text-right font-mono tabular-nums" style={{ color: "var(--text)" }}>
                    {m.input_tokens.toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-right font-mono tabular-nums" style={{ color: "var(--text)" }}>
                    {m.output_tokens.toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-right font-mono tabular-nums" style={{ color: "var(--text)" }}>
                    ${m.cost_usd.toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Project breakdown */}
      <section className="mt-8">
        <h2 className="mb-3" style={sectionH2}>
          專案用量
        </h2>
        <div className="overflow-x-auto" style={tableWrap}>
          <table className="w-full text-sm">
            <thead>
              <tr style={headerRowStyle}>
                {tableHeader("Project")}
                {tableHeader("Sessions", "right")}
                {tableHeader("Messages", "right")}
                {tableHeader("Tokens", "right")}
                {tableHeader("Cost", "right")}
              </tr>
            </thead>
            <tbody>
              {data.projects.map((p) => (
                <tr
                  key={p.project}
                  style={{ borderBottom: "1px solid var(--border)" }}
                >
                  <td className="px-4 py-2 font-medium" style={{ color: "var(--text)" }}>
                    {p.project}
                  </td>
                  <td className="px-4 py-2 text-right font-mono tabular-nums" style={{ color: "var(--text)" }}>
                    {p.sessions}
                  </td>
                  <td className="px-4 py-2 text-right font-mono tabular-nums" style={{ color: "var(--text)" }}>
                    {p.messages.toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-right font-mono tabular-nums" style={{ color: "var(--text)" }}>
                    {p.tokens_total.toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-right font-mono tabular-nums" style={{ color: "var(--text)" }}>
                    ${p.cost_usd.toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
