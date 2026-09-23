"use client";

import { useEffect, useRef, useState } from "react";
import { apiFetch, type SensorsData } from "@/lib/api";
import Sparkline from "@/components/Sparkline";

// Live temperatures, fans and power — phase 1 of exelban/stats parity.
// History lives in the browser only (last HISTORY samples while the page is
// open); persistent history comes with the CPU/memory/network modules.
const POLL_SEC = 2;
const HISTORY = 90;

type Ok = Extract<SensorsData, { status: "ok" }>;
type Series = Record<string, number[]>;

// Status colors are reserved for state and always ship with a text label.
function heat(c: number): { label: string; color: string } | null {
  if (c >= 95) return { label: "過熱", color: "var(--status-err)" };
  if (c >= 85) return { label: "偏高", color: "var(--status-warn)" };
  return null;
}

const card = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
} as const;

function Tile({ title, value, unit, sub, series, flag }: {
  title: string;
  value: number;
  unit: string;
  sub?: string;
  series: number[];
  flag?: { label: string; color: string } | null;
}) {
  return (
    <div className="p-4" style={card}>
      <div className="flex items-center justify-between text-xs" style={{ color: "var(--text-muted)" }}>
        <span>{title}</span>
        {flag && <span className="font-mono text-[10px]" style={{ color: flag.color }}>● {flag.label}</span>}
      </div>
      <div className="mt-1 font-mono tabular-nums" style={{ fontSize: 26, color: "var(--text)", fontWeight: 500 }}>
        {value.toFixed(unit === "RPM" ? 0 : 1)}
        <span className="ml-1 text-sm" style={{ color: "var(--text-muted)" }}>{unit}</span>
      </div>
      <div className="mb-2 h-4 font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>{sub}</div>
      <Sparkline values={series} unit={unit} label={title} stepSec={POLL_SEC} />
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-6">
      <h2 className="mb-2 text-sm" style={{ color: "var(--text)", fontWeight: 500 }}>{title}</h2>
      {children}
    </section>
  );
}

function Rows({ head, rows }: { head: string[]; rows: (string | number)[][] }) {
  return (
    <div className="overflow-x-auto" style={card}>
      <table className="w-full text-sm">
        <thead>
          <tr style={{ borderBottom: "1px solid var(--border)" }}>
            {head.map((h) => (
              <th key={h} className="px-4 py-2 text-left font-mono text-[10px] uppercase" style={{ color: "var(--text-subtle)", letterSpacing: "0.08em" }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} style={{ borderBottom: i < rows.length - 1 ? "1px solid var(--border)" : undefined }}>
              {r.map((c, j) => (
                <td key={j} className={`px-4 py-2 text-xs ${j ? "font-mono tabular-nums" : ""}`} style={{ color: j ? "var(--text)" : "var(--text-muted)" }}>{c}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RawList({ title, values, unit }: { title: string; values: Record<string, number>; unit: string }) {
  const entries = Object.entries(values);
  if (!entries.length) return null;
  return (
    <details className="mt-2 px-4 py-2 text-xs" style={card}>
      <summary className="cursor-pointer" style={{ color: "var(--text-muted)" }}>{title}（{entries.length}）</summary>
      <div className="mt-2 grid gap-x-4 gap-y-1 font-mono tabular-nums" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))", color: "var(--text)" }}>
        {entries.map(([k, v]) => <span key={k}><span style={{ color: "var(--text-subtle)" }}>{k}</span> {v}{unit}</span>)}
      </div>
    </details>
  );
}

export default function SensorsPage() {
  const [data, setData] = useState<SensorsData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [series, setSeries] = useState<Series>({});
  const busy = useRef(false);

  useEffect(() => {
    const tick = async () => {
      if (busy.current || document.hidden) return;
      busy.current = true;
      try {
        const d = await apiFetch<SensorsData>("/api/health/sensors");
        setData(d);
        setErr(null);
        if (d.status === "ok") {
          const point: Record<string, number> = {};
          for (const g of d.temperatures.groups) point[`t:${g.id}`] = g.avg;
          for (const p of [...d.power.system, ...d.power.components]) point[`p:${p.id}`] = p.watts;
          for (const f of d.fans) point[`f:${f.id}`] = f.rpm;
          setSeries((prev) => {
            const next: Series = {};
            for (const [k, v] of Object.entries(point)) next[k] = [...(prev[k] ?? []), v].slice(-HISTORY);
            return next;
          });
        }
      } catch (e) {
        setErr((e as Error).message);
      } finally {
        busy.current = false;
      }
    };
    tick();
    const id = setInterval(tick, POLL_SEC * 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div>
      <h1 className="mb-1 tracking-tight" style={{ fontSize: 28, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.02em" }}>
        溫度與功耗
      </h1>
      <p className="mb-5 font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
        AppleSMC + IOReport，免 root · 每 {POLL_SEC}s 更新 · 趨勢線保留本頁最近 {HISTORY} 次取樣
      </p>

      {err && <p style={{ color: "var(--status-err)" }}>API 錯誤：{err}</p>}
      {!err && !data && <p style={{ color: "var(--text-muted)" }}>載入中...</p>}
      {data?.status === "unavailable" && (
        <div className="p-6" style={card}>
          <p style={{ color: "var(--status-warn)" }}>● 感測器無法讀取</p>
          <p className="mt-1 font-mono text-xs" style={{ color: "var(--text-muted)" }}>{data.error}</p>
        </div>
      )}
      {data?.status === "ok" && <Readings d={data} series={series} />}
    </div>
  );
}

function Readings({ d, series }: { d: Ok; series: Series }) {
  const groups = Object.fromEntries(d.temperatures.groups.map((g) => [g.id, g]));
  const sys = d.power.system.find((p) => p.id === "PSTR");
  const comp = Object.fromEntries(d.power.components.map((p) => [p.id, p]));
  return (
    <>
      <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))" }}>
        {(["cpu", "gpu"] as const).map((id) => groups[id] && (
          <Tile key={id} title={`${groups[id].label} 溫度`} value={groups[id].avg} unit="°C"
            sub={`最高 ${groups[id].max}°C · ${Object.keys(groups[id].sensors).length} 個感測器`}
            series={series[`t:${id}`] ?? []} flag={heat(groups[id].max)} />
        ))}
        {sys && <Tile title="系統總功耗" value={sys.watts} unit="W" series={series["p:PSTR"] ?? []} />}
        {(["CPU Energy", "GPU Energy"] as const).map((id) => comp[id] && (
          <Tile key={id} title={`${comp[id].label} 功耗`} value={comp[id].watts} unit="W" series={series[`p:${id}`] ?? []} />
        ))}
        {d.fans.map((f) => (
          <Tile key={f.id} title={`風扇 ${f.id + 1}`} value={f.rpm} unit="RPM"
            sub={`${f.percent ?? "—"}% · ${f.mode === "auto" ? "自動" : "手動設定"}`} series={series[`f:${f.id}`] ?? []} />
        ))}
      </div>

      <Section title="溫度">
        <Rows head={["部位", "平均", "最高", "感測器"]} rows={d.temperatures.groups.map((g) => {
          const h = heat(g.max);
          return [g.label, `${g.avg}°C`, `${g.max}°C${h ? ` ${h.label}` : ""}`, Object.keys(g.sensors).length];
        })} />
        <RawList title="已分組感測器明細" values={Object.assign({}, ...d.temperatures.groups.map((g) => g.sensors))} unit="°" />
        <RawList title="未分類溫度鍵（原始 SMC 名稱）" values={d.temperatures.other} unit="°" />
      </Section>

      <Section title="風扇">
        {d.fans.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>這台機器沒有回報風扇（FNum = 0）。</p>
        ) : (
          <Rows head={["風扇", "轉速", "目標", "範圍", "模式"]} rows={d.fans.map((f) => [
            `風扇 ${f.id + 1}`, `${f.rpm} RPM (${f.percent ?? "—"}%)`, f.target ?? "—", `${f.min ?? "—"}–${f.max ?? "—"}`, f.mode === "auto" ? "自動" : "手動設定",
          ])} />
        )}
      </Section>

      <Section title="功耗">
        <Rows head={["來源", "項目", "瓦數"]} rows={[
          ...d.power.system.map((p) => ["SMC", p.label, `${p.watts} W`]),
          ...d.power.components.map((p) => ["IOReport", p.label, `${p.watts} W`]),
          ...Object.entries(d.power.clusters).map(([k, v]) => ["IOReport 叢集", k, `${v} W`]),
        ]} />
        {d.power.energy_error && (
          <p className="mt-2 font-mono text-xs" style={{ color: "var(--status-warn)" }}>● 元件功耗無法讀取：{d.power.energy_error}</p>
        )}
        <RawList title="其他 SMC 功耗鍵（原始名稱）" values={d.power.rails} unit="W" />
      </Section>
    </>
  );
}
