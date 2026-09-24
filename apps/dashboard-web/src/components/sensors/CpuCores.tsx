import Sparkline from "@/components/Sparkline";
import type { CpuCluster, CpuCore } from "@/lib/api";
import { card, fmt } from "./ui";

// One card per cluster (Super / Performance 0 / Performance 1 ...), one cell
// per core: load bar, clock and power. Load comes from DVFS residency, so a
// core parked for the whole window reads 0 %, not "unknown".

function CoreCell({ core, series, stepSec }: { core: CpuCore; series: number[]; stepSec: number }) {
  const load = core.active ?? 0;
  return (
    <div className="px-3 py-2" style={{ border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-[10px]" style={{ color: "var(--text-subtle)" }}>{core.id}</span>
        <span className="font-mono tabular-nums text-sm" style={{ color: "var(--text)", fontWeight: 500 }}>
          {fmt(core.active, 0, "%")}
        </span>
      </div>
      <div className="mt-1 h-1.5 w-full overflow-hidden" style={{ background: "var(--accent-bg)", borderRadius: 2 }}
        role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={load} aria-label={`${core.id} 使用率`}>
        <div className="h-full" style={{ width: `${Math.min(100, load)}%`, background: "var(--accent)" }} />
      </div>
      <div className="mt-1 flex justify-between font-mono text-[10px] tabular-nums" style={{ color: "var(--text-muted)" }}>
        <span>{core.freq_mhz ? `${(core.freq_mhz / 1000).toFixed(2)} GHz` : core.active ? "頻率 —" : "閒置"}</span>
        <span>{fmt(core.watts, 2, " W")}</span>
      </div>
      <div className="mt-1">
        <Sparkline values={series} unit="%" label={`${core.id} 使用率`} stepSec={stepSec} height={22} />
      </div>
    </div>
  );
}

export default function CpuCores({ clusters, series, stepSec }: {
  clusters: CpuCluster[];
  series: Record<string, number[]>;
  stepSec: number;
}) {
  if (!clusters.length) {
    return <p className="text-xs" style={{ color: "var(--status-warn)" }}>● 讀不到每核心的效能狀態（IOReport CPU Core Performance States 無資料）</p>;
  }
  return (
    <div className="grid gap-3">
      {clusters.map((c) => {
        const maxMhz = c.cores.find((x) => x.freq_max_mhz)?.freq_max_mhz;
        return (
          <div key={c.id} className="p-4" style={card}>
            <div className="mb-3 flex flex-wrap items-baseline gap-x-4 gap-y-1">
              <span className="text-sm" style={{ color: "var(--text)", fontWeight: 500 }}>{c.label}</span>
              <span className="font-mono text-[11px] tabular-nums" style={{ color: "var(--text-muted)" }}>
                {c.cores.length} 核 · 平均 {fmt(c.active, 0, "%")} · 叢集 {fmt(c.watts, 2, " W")}
                {maxMhz ? ` · 最高 ${(maxMhz / 1000).toFixed(2)} GHz` : ""}
              </span>
            </div>
            <div className="grid gap-2" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(128px, 1fr))" }}>
              {c.cores.map((core) => (
                <CoreCell key={core.id} core={core} series={series[`c:${core.id}`] ?? []} stepSec={stepSec} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
