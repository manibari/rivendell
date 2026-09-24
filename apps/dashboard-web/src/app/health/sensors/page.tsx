"use client";

import { useEffect, useRef, useState } from "react";
import { apiFetch, type SensorsData } from "@/lib/api";
import BatteryPanel from "@/components/sensors/BatteryPanel";
import CpuCores from "@/components/sensors/CpuCores";
import GpuPanel from "@/components/sensors/GpuPanel";
import HistoryPanel from "@/components/sensors/HistoryPanel";
import LaptopMap from "@/components/sensors/LaptopMap";
import { card, heat, RawList, Rows, Section, Tile } from "@/components/sensors/ui";

// System monitor (exelban/stats parity): live readings every POLL_SEC with
// in-page trend lines, plus persisted history from the metrics collector
// (agents/registry/metrics-collector.md) that keeps recording when this page
// is closed.
const POLL_SEC = 2;
const HISTORY = 90;

type Ok = Extract<SensorsData, { status: "ok" }>;
type Series = Record<string, number[]>;

function points(d: Ok): Record<string, number> {
  const p: Record<string, number> = {};
  for (const g of d.temperatures.groups) p[`t:${g.id}`] = g.avg;
  for (const x of [...d.power.system, ...d.power.components]) p[`p:${x.id}`] = x.watts;
  for (const f of d.fans) p[`f:${f.id}`] = f.rpm;
  for (const c of d.cpu.clusters) for (const core of c.cores) if (core.active !== null) p[`c:${core.id}`] = core.active;
  if (d.cpu.total_active !== null) p["cpu"] = d.cpu.total_active;
  if (d.gpu.device_util !== null) p["gpu"] = d.gpu.device_util;
  if (d.battery.status === "ok") {
    if (d.battery.percent !== null) p["b:pct"] = d.battery.percent;
    if (d.battery.battery_watts !== null) p["b:w"] = d.battery.battery_watts;
  }
  return p;
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
          const point = points(d);
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
        系統監控
      </h1>
      <p className="mb-5 font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
        AppleSMC + IOReport + AppleSmartBattery，免 root · 即時每 {POLL_SEC}s 更新 · 歷史由背景收集程式每 5s 記錄
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
  const bat = d.battery.status === "ok" ? d.battery : null;
  return (
    <>
      <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))" }}>
        <Tile title="CPU 使用率" value={d.cpu.total_active} unit="%" digits={0} stepSec={POLL_SEC}
          sub={`${d.cpu.core_count} 核平均`} series={series["cpu"] ?? []} />
        <Tile title="GPU 使用率" value={d.gpu.device_util} unit="%" digits={0} stepSec={POLL_SEC}
          sub={`${d.gpu.core_count ?? "?"} 核 · ${d.gpu.watts?.toFixed(2) ?? "—"} W`} series={series["gpu"] ?? []} />
        {groups.cpu && <Tile title="CPU 溫度" value={groups.cpu.avg} unit="°C" stepSec={POLL_SEC}
          sub={`最高 ${groups.cpu.max}°C`} series={series["t:cpu"] ?? []} flag={heat(groups.cpu.max)} />}
        {sys && <Tile title="系統總功耗" value={sys.watts} unit="W" stepSec={POLL_SEC} series={series["p:PSTR"] ?? []} />}
        {bat && <Tile title="電池" value={bat.percent} unit="%" digits={0} stepSec={POLL_SEC}
          sub={bat.state_label} series={series["b:pct"] ?? []} />}
      </div>

      <Section title="機身溫度分布" note="滑過方塊看感測器明細">
        <LaptopMap groups={d.temperatures.groups} fans={d.fans} otherCount={Object.keys(d.temperatures.other).length} />
      </Section>

      <Section title="CPU 每核心" note="IOReport DVFS 停留時間 → 使用率 / 頻率；Energy Model → 每核功耗">
        <CpuCores clusters={d.cpu.clusters} series={series} stepSec={POLL_SEC} />
      </Section>

      <Section title="GPU">
        <GpuPanel gpu={d.gpu} temps={groups.gpu} />
      </Section>

      <Section title="電池與充放電" note="AppleSmartBattery">
        <BatteryPanel b={d.battery} systemWatts={sys?.watts ?? null} series={series} stepSec={POLL_SEC} />
      </Section>

      <Section title="歷史紀錄" note="5 秒資料留 7 天 · 每分鐘彙整留 90 天 · 每小時彙整永久">
        <HistoryPanel clusters={d.cpu.clusters} />
      </Section>

      <Section title="溫度明細">
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
            `F${f.id}`, `${f.rpm} RPM (${f.percent ?? "—"}%)`, f.target ?? "—", `${f.min ?? "—"}–${f.max ?? "—"}`, f.mode === "auto" ? "自動" : "手動設定",
          ])} />
        )}
      </Section>

      <Section title="功耗明細">
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
