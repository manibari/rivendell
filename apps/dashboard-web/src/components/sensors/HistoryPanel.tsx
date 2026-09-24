"use client";

import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiFetch, type CpuCluster, type MetricsHistory } from "@/lib/api";
import { card, ramp } from "./ui";

// Persisted history from the metrics collector (5 s / 1 m / 1 h tiers, chosen
// server-side). One metric per chart in the accent green; solid = bucket
// average, dashed = bucket peak. Per-core load is a heatmap (one row per core)
// rather than 18 overlapping lines.

// recharts needs literal colors (see tokens/page.tsx); these mirror globals.css.
const ACCENT = "#2d4a3e";
const ACCENT_SOFT = "#5b7a6a";
const BORDER = "#e5e7eb";
const TEXT_SUBTLE = "#9ca3af";

const RANGES = ["15m", "1h", "6h", "24h", "7d", "30d", "90d", "1y"] as const;
type Range = (typeof RANGES)[number];
const RANGE_LABEL: Record<Range, string> = {
  "15m": "15 分", "1h": "1 小時", "6h": "6 小時", "24h": "24 小時", "7d": "7 天", "30d": "30 天", "90d": "90 天", "1y": "1 年",
};
const TIER_LABEL = { "5s": "5 秒原始資料", "1m": "每分鐘彙整", "1h": "每小時彙整" } as const;
const HEAT_COLS = 120;
const tick = (v: number) => (Math.abs(v) >= 100 ? v.toFixed(0) : String(Number(v.toFixed(1))));

const CHARTS: { key: string; title: string; unit: string; peak?: boolean; zero?: boolean; second?: string; pct?: boolean }[] = [
  { key: "cpu.total", title: "CPU 總使用率", unit: "%", peak: true, pct: true },
  { key: "gpu.util", title: "GPU 使用率", unit: "%", peak: true, pct: true },
  { key: "temp.cpu", title: "CPU 溫度（平均 / 峰值）", unit: "°C", peak: true },
  { key: "temp.gpu", title: "GPU 溫度（平均 / 峰值）", unit: "°C", peak: true },
  { key: "power.PSTR", title: "系統總功耗", unit: "W", peak: true },
  { key: "power.CPU Energy", title: "CPU 功耗", unit: "W", peak: true },
  { key: "bat.pct", title: "電池電量", unit: "%", pct: true },
  { key: "bat.w", title: "電池充放電（+ 充入 / − 放電）", unit: "W", zero: true },
  { key: "bat.temp", title: "電池溫度", unit: "°C" },
  { key: "fan.0", title: "風扇 F0 實線 / F1 虛線", unit: "RPM", second: "fan.1" },
];

type Ok = Extract<MetricsHistory, { status: "ok" | "empty" }>;

function timeFmt(range: Range) {
  const long = ["7d", "30d", "90d", "1y"].includes(range);
  return (ts: number) => {
    const d = new Date(ts * 1000);
    const hm = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
    return long ? `${d.getMonth() + 1}/${d.getDate()}${range === "7d" ? ` ${hm}` : ""}` : hm;
  };
}

function MetricChart({ h, spec, range }: { h: Ok; spec: (typeof CHARTS)[number]; range: Range }) {
  const avg = h.avg[spec.key];
  if (!avg || avg.every((v) => v === null)) {
    return (
      <div className="p-3" style={card}>
        <div className="text-xs" style={{ color: "var(--text-muted)" }}>{spec.title}</div>
        <div className="flex h-[140px] items-center justify-center text-[11px]" style={{ color: "var(--text-subtle)" }}>此區間無資料</div>
      </div>
    );
  }
  const peak = spec.peak ? h.max[spec.key.startsWith("temp.") ? `${spec.key}.max` : spec.key] : undefined;
  const second = spec.second ? h.avg[spec.second] : undefined;
  const rows = h.ts.map((ts, i) => ({ ts, v: avg[i], p: peak?.[i] ?? null, s: second?.[i] ?? null }));
  const vals = avg.filter((v): v is number => v !== null);
  const last = vals[vals.length - 1];
  const all = [...vals, ...(peak ?? []).filter((v): v is number => v !== null)];
  const lo = Math.min(...all);
  const hi = Math.max(...all);
  // A near-flat series (full battery, idle temp) would otherwise zoom into noise.
  const domain: [number | string, number | string] = spec.pct ? [0, 100]
    : hi - lo < 2 ? [Math.floor(lo - 1), Math.ceil(hi + 1)] : ["auto", "auto"];
  const fmt = timeFmt(range);
  return (
    <div className="p-3" style={card}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-3">
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>{spec.title}</span>
        <span className="font-mono text-[11px] tabular-nums" style={{ color: "var(--text-subtle)" }}>
          區間 {Math.min(...vals).toFixed(1)}–{Math.max(...vals).toFixed(1)} · 最新 {last.toFixed(1)} {spec.unit}
        </span>
      </div>
      <div style={{ height: 140 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={rows} margin={{ top: 8, right: 4, bottom: 0, left: -18 }}>
            <CartesianGrid stroke={BORDER} vertical={false} />
            <XAxis dataKey="ts" tickFormatter={fmt} tick={{ fontSize: 9, fill: TEXT_SUBTLE }} minTickGap={40} stroke={BORDER} />
            <YAxis tick={{ fontSize: 9, fill: TEXT_SUBTLE }} stroke={BORDER} width={48} tickFormatter={tick}
              domain={domain} />
            {spec.zero && <ReferenceLine y={0} stroke={TEXT_SUBTLE} />}
            <Tooltip
              labelFormatter={(ts) => new Date(Number(ts) * 1000).toLocaleString("zh-TW")}
              formatter={(v, name) => [`${Number(v).toFixed(2)} ${spec.unit}`,
                name === "v" ? (spec.second ? "F0" : "平均") : name === "p" ? "峰值" : "F1"]}
              contentStyle={{ fontSize: 11, border: `1px solid ${BORDER}` }}
            />
            <Area type="monotone" dataKey="v" stroke={ACCENT} strokeWidth={1.5} fill={ACCENT} fillOpacity={0.08}
              connectNulls={false} isAnimationActive={false} dot={false} />
            {peak && <Line type="monotone" dataKey="p" stroke={ACCENT_SOFT} strokeDasharray="3 3" strokeWidth={1}
              dot={false} connectNulls={false} isAnimationActive={false} />}
            {second && <Line type="monotone" dataKey="s" stroke={ACCENT_SOFT} strokeDasharray="5 3" strokeWidth={1.5}
              dot={false} connectNulls={false} isAnimationActive={false} />}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function CoreHeatmap({ h, clusters, range }: { h: Ok; clusters: CpuCluster[]; range: Range }) {
  const cores = clusters.flatMap((c) => c.cores.map((x) => ({ id: x.id, label: c.label })));
  const n = h.ts.length;
  const per = Math.max(1, Math.ceil(n / HEAT_COLS));
  const cols = Math.ceil(n / per);
  const cell = (key: string, j: number) => {
    const s = h.avg[key];
    if (!s) return null;
    const vs = s.slice(j * per, (j + 1) * per).filter((v): v is number => v !== null);
    return vs.length ? vs.reduce((a, b) => a + b, 0) / vs.length : null;
  };
  const fmt = timeFmt(range);
  const W = 1000;
  const rowH = 14;
  const labelW = 70;
  const cw = (W - labelW) / cols;
  const H = cores.length * rowH + 18;
  return (
    <div className="p-3" style={card}>
      <div className="flex items-baseline justify-between">
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>每核心使用率熱圖（每列一顆核心，顏色越深越忙）</span>
        <span className="flex items-center gap-2 font-mono text-[10px]" style={{ color: "var(--text-subtle)" }}>
          0%
          <span className="inline-block h-2 w-20" style={{ background: `linear-gradient(90deg, ${ramp(0)}, ${ramp(0.5)}, ${ramp(1)})`, borderRadius: 2 }} />
          100% · 空白 = 無資料
        </span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="每核心使用率熱圖" style={{ display: "block", marginTop: 6 }}>
        {cores.map((c, i) => (
          <g key={c.id}>
            <text x={0} y={i * rowH + 11} fontSize={10} fill={TEXT_SUBTLE} fontFamily="var(--font-mono)">{c.id}</text>
            {Array.from({ length: cols }, (_, j) => {
              const v = cell(`core.${c.id}`, j);
              if (v === null) return null;
              const k = v / 100;
              return (
                <rect key={j} x={labelW + j * cw} y={i * rowH} width={cw + 0.3} height={rowH - 2} fill={ramp(k)}>
                  <title>{`${c.id}（${c.label}）${fmt(h.ts[j * per])} 平均 ${v.toFixed(1)}%`}</title>
                </rect>
              );
            })}
          </g>
        ))}
        {[0, Math.floor(cols / 2), cols - 1].map((j) => (
          <text key={j} x={labelW + j * cw} y={H - 2} fontSize={10} fill={TEXT_SUBTLE}
            textAnchor={j === 0 ? "start" : j === cols - 1 ? "end" : "middle"}>{fmt(h.ts[j * per])}</text>
        ))}
      </svg>
    </div>
  );
}

export default function HistoryPanel({ clusters }: { clusters: CpuCluster[] }) {
  const [range, setRange] = useState<Range>("1h");
  const [h, setH] = useState<MetricsHistory | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const d = await apiFetch<MetricsHistory>(`/api/health/metrics/history?range=${range}&points=600`);
        if (alive) { setH(d); setErr(null); }
      } catch (e) {
        if (alive) setErr((e as Error).message);
      }
    };
    load();
    // Short ranges move visibly; refresh them while the page is open.
    const every = ["15m", "1h"].includes(range) ? 15000 : ["6h", "24h"].includes(range) ? 60000 : 0;
    const id = every ? setInterval(() => { if (!document.hidden) load(); }, every) : undefined;
    return () => { alive = false; if (id) clearInterval(id); };
  }, [range]);

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {RANGES.map((r) => (
          <button key={r} onClick={() => setRange(r)} className="px-2.5 py-1 font-mono text-[11px]"
            style={{
              borderRadius: "var(--radius-sm)",
              border: `1px solid ${r === range ? "var(--accent)" : "var(--border)"}`,
              background: r === range ? "var(--accent-bg)" : "var(--surface)",
              color: r === range ? "var(--accent)" : "var(--text-muted)",
            }}>
            {RANGE_LABEL[r]}
          </button>
        ))}
        {h && h.status !== "unavailable" && (
          <span className="ml-auto font-mono text-[11px]" style={{ color: h.collector.running ? "var(--text-subtle)" : "var(--status-warn)" }}>
            {h.collector.running ? "收集中" : "● 收集程式未運作"} · {TIER_LABEL[h.tier]} · 每點 {h.step >= 3600 ? `${h.step / 3600} 小時` : h.step >= 60 ? `${h.step / 60} 分` : `${h.step} 秒`}
            {h.collector.last_sample && ` · 最後取樣 ${new Date(h.collector.last_sample * 1000).toLocaleTimeString("zh-TW")}`}
          </span>
        )}
      </div>

      {err && <p className="text-xs" style={{ color: "var(--status-err)" }}>歷史 API 錯誤：{err}</p>}
      {h?.status === "unavailable" && (
        <div className="p-4 text-xs" style={card}>
          <p style={{ color: "var(--status-warn)" }}>● 沒有歷史資料</p>
          <p className="mt-1 font-mono" style={{ color: "var(--text-muted)" }}>{h.error}</p>
        </div>
      )}
      {h?.status === "empty" && (
        <p className="mb-2 text-xs" style={{ color: "var(--text-muted)" }}>這段期間沒有任何取樣（收集程式當時未運作或電腦休眠）。</p>
      )}
      {h && h.status !== "unavailable" && (
        <>
          <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))" }}>
            {CHARTS.map((spec) => <MetricChart key={spec.key} h={h} spec={spec} range={range} />)}
          </div>
          <div className="mt-3">
            <CoreHeatmap h={h} clusters={clusters} range={range} />
          </div>
        </>
      )}
    </div>
  );
}
