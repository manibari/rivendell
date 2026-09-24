import type { GpuReading, SensorGroup } from "@/lib/api";
import { card, fmt, ramp, Stat } from "./ui";

// Whole-GPU load (AGX driver + IOReport residency) and every GPU die
// temperature probe. macOS exposes no per-GPU-core load; the reason from the
// API is shown verbatim instead of a fake per-core grid.

const T_LO = 30;
const T_HI = 95;

export default function GpuPanel({ gpu, temps }: { gpu: GpuReading; temps?: SensorGroup }) {
  const probes = Object.entries(temps?.sensors ?? {});
  return (
    <div className="p-4" style={card}>
      <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))" }}>
        <Stat label="GPU 使用率" value={fmt(gpu.device_util, 0, "%")} sub="AGX Device Utilization" />
        <Stat label="Renderer / Tiler" value={`${fmt(gpu.renderer_util, 0, "%")} / ${fmt(gpu.tiler_util, 0, "%")}`} />
        <Stat label="作用時間" value={fmt(gpu.active, 1, "%")} sub="IOReport 非 OFF 狀態" />
        <Stat label="頻率" value={gpu.freq_mhz ? `${gpu.freq_mhz} MHz` : "—"} sub={gpu.freq_mhz ? undefined : "頻率表與狀態數對不上"} />
        <Stat label="功耗" value={fmt(gpu.watts, 2, " W")} />
        <Stat label="顯示記憶體使用" value={gpu.memory_in_use ? `${(gpu.memory_in_use / 2 ** 30).toFixed(2)} GB` : "—"} />
      </div>

      {probes.length > 0 && (
        <div className="mt-5">
          <div className="mb-1.5 flex flex-wrap justify-between gap-x-4 text-[11px]" style={{ color: "var(--text-muted)" }}>
            <span>GPU 晶片溫度（{probes.length} 個探針）</span>
            <span className="font-mono tabular-nums">
              最低 {Math.min(...probes.map(([, v]) => v)).toFixed(1)}° · 平均 {temps?.avg}° · 最高 {temps?.max}°
            </span>
          </div>
          <div className="flex h-4 gap-px overflow-hidden" style={{ borderRadius: 3 }}>
            {probes.map(([k, v]) => (
              <div key={k} title={`${k} ${v}°C`} className="flex-1" style={{ background: ramp((v - T_LO) / (T_HI - T_LO)) }} />
            ))}
          </div>
        </div>
      )}

      <p className="mt-4 text-[11px]" style={{ color: "var(--text-subtle)" }}>
        {gpu.core_count ?? "?"} 核 GPU。每核心使用率 macOS 不提供（系統只回報整顆 GPU），探針與核心的對應 Apple 也未公開。
      </p>
    </div>
  );
}
