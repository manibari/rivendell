import Sparkline from "@/components/Sparkline";
import type { BatteryReading } from "@/lib/api";
import { card, fmt, Stat } from "./ui";

// Battery, charge / discharge and adapter. Sign convention from the API:
// battery_watts / amperage_ma are + while charging, - while discharging.

type Ok = Extract<BatteryReading, { status: "ok" }>;

function duration(min: number | null): string | null {
  if (min === null) return null;
  const h = Math.floor(min / 60);
  return h ? `${h} 小時 ${min % 60} 分` : `${min} 分`;
}

function flowLabel(b: Ok): string {
  const w = b.battery_watts;
  if (w === null || Math.abs(w) < 0.05) return "電池無充放電";
  return w > 0 ? `充入電池 ${w.toFixed(1)} W` : `電池放電 ${(-w).toFixed(1)} W`;
}

export default function BatteryPanel({ b, series, stepSec }: {
  b: BatteryReading;
  series: Record<string, number[]>;
  stepSec: number;
}) {
  if (b.status !== "ok") {
    return <p className="text-xs" style={{ color: "var(--text-muted)" }}>● {b.error}</p>;
  }
  const eta = duration(b.minutes_to_full) ?? duration(b.minutes_to_empty);
  const pct = b.percent ?? 0;
  return (
    <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))" }}>
      <div className="p-4" style={card}>
        <div className="flex items-baseline justify-between">
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>電量</span>
          <span className="font-mono text-[11px]" style={{ color: b.permanent_failure ? "var(--status-err)" : "var(--text-muted)" }}>
            {b.permanent_failure ? "● 電池永久故障旗標" : b.state_label}
          </span>
        </div>
        <div className="mt-1 font-mono tabular-nums" style={{ fontSize: 32, color: "var(--text)", fontWeight: 500 }}>
          {fmt(b.percent, 0)}<span className="ml-1 text-sm" style={{ color: "var(--text-muted)" }}>%</span>
        </div>
        <div className="mt-2 h-2 w-full overflow-hidden" style={{ background: "var(--accent-bg)", borderRadius: 2 }}
          role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-label="電池電量">
          <div className="h-full" style={{ width: `${pct}%`, background: "var(--accent)" }} />
        </div>
        <div className="mt-2 font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
          {eta ? `${b.state === "charging" ? "預估充滿" : "預估可用"} ${eta}` : "無時間預估"}
          {b.daily_soc.min !== null && ` · 今日 ${b.daily_soc.min}–${b.daily_soc.max}%`}
        </div>
        <div className="mt-3">
          <Sparkline values={series["b:pct"] ?? []} unit="%" label="電量" stepSec={stepSec} />
        </div>
      </div>

      <div className="p-4" style={card}>
        <div className="text-xs" style={{ color: "var(--text-muted)" }}>充放電</div>
        <div className="mt-2 grid grid-cols-3 items-center gap-2 text-center">
          <Stat label={b.external_connected ? "電源輸入" : "未接電源"} value={fmt(b.adapter_in_watts, 1, " W")}
            sub={b.adapter?.watts ? `${b.adapter.watts} W 充電器` : undefined} />
          <Stat label="系統負載" value={fmt(b.system_watts, 1, " W")} />
          <Stat label="電池" value={fmt(b.battery_watts, 1, " W")} sub={flowLabel(b)} />
        </div>
        <div className="mt-3 grid grid-cols-3 gap-2">
          <Stat label="電流" value={fmt(b.amperage_ma, 0, " mA")} />
          <Stat label="電壓" value={fmt(b.voltage_v, 2, " V")} />
          <Stat label="電池溫度" value={fmt(b.temperature_c, 1, "°C")} />
        </div>
        <div className="mt-3">
          <Sparkline values={series["b:w"] ?? []} unit="W" label="電池充放電功率" stepSec={stepSec} />
        </div>
      </div>

      <div className="p-4" style={card}>
        <div className="text-xs" style={{ color: "var(--text-muted)" }}>健康度</div>
        <div className="mt-2 grid grid-cols-2 gap-3">
          <Stat label="滿電容量 / 設計容量" value={fmt(b.health_percent, 1, "%")}
            sub={`${b.full_capacity_mah ?? "—"} / ${b.design_capacity_mah ?? "—"} mAh`} />
          <Stat label="循環次數" value={`${b.cycle_count ?? "—"}`} sub={b.design_cycle_count ? `設計壽命 ${b.design_cycle_count} 次` : undefined} />
          <Stat label="目前容量" value={fmt(b.capacity_mah, 0, " mAh")} />
          <Stat label="充電器" value={b.adapter ? `${b.adapter.voltage_v ?? "—"} V · ${b.adapter.current_ma ?? "—"} mA` : "—"}
            sub={b.adapter?.description ?? undefined} />
        </div>
        {b.cell_voltages_v.length > 0 && (
          <div className="mt-3">
            <div className="text-[11px]" style={{ color: "var(--text-muted)" }}>電芯電壓（{b.cell_voltages_v.length} 串）</div>
            <div className="mt-1 flex gap-3 font-mono text-xs tabular-nums" style={{ color: "var(--text)" }}>
              {b.cell_voltages_v.map((v, i) => <span key={i}>{v.toFixed(3)} V</span>)}
            </div>
            <div className="font-mono text-[10px]" style={{ color: "var(--text-subtle)" }}>
              壓差 {((Math.max(...b.cell_voltages_v) - Math.min(...b.cell_voltages_v)) * 1000).toFixed(0)} mV
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
