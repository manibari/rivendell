import type { GpuReading, SensorGroup } from "@/lib/api";
import { card, fmt, onRamp, ramp, Stat } from "./ui";

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

      <p className="mt-4 text-xs" style={{ color: "var(--text-muted)" }}>
        {gpu.core_count ?? "?"} 核 GPU · 每核心使用率：<span style={{ color: "var(--status-warn)" }}>●</span> {gpu.per_core_reason}
      </p>

      {probes.length > 0 && (
        <div className="mt-3">
          <div className="mb-1 font-mono text-[10px]" style={{ color: "var(--text-subtle)" }}>
            GPU 晶片溫度探針 {probes.length} 個（SMC Tg**，平均 {temps?.avg}°C · 最高 {temps?.max}°C；探針與核心的對應 Apple 未公開）
          </div>
          <div className="grid gap-1" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(52px, 1fr))" }}>
            {probes.map(([k, v]) => {
              const t = (v - T_LO) / (T_HI - T_LO);
              return (
                <div key={k} title={`${k} ${v}°C`} className="px-1 py-0.5 text-center font-mono text-[10px] tabular-nums"
                  style={{ background: ramp(t), color: onRamp(t), borderRadius: 2 }}>
                  {v.toFixed(0)}°
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
