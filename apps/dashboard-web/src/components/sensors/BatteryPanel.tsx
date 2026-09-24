import Sparkline from "@/components/Sparkline";
import type { BatteryReading } from "@/lib/api";
import { card, fmt, Stat } from "./ui";

// Battery, charge / discharge and adapter, plus health and cycle count.
// Sign convention from the API: battery_watts / amperage_ma are + while
// charging, - while discharging. System load comes from the SMC total (PSTR),
// which is measured; the battery gauge's own SystemLoad field goes negative
// on battery and is not shown.

type Ok = Extract<BatteryReading, { status: "ok" }>;

function duration(min: number | null): string | null {
  if (min === null) return null;
  const h = Math.floor(min / 60);
  return h ? `${h} 小時 ${min % 60} 分` : `${min} 分`;
}

function flowLabel(b: Ok): string {
  const w = b.battery_watts;
  if (w === null || Math.abs(w) < 0.05) return "無充放電";
  return w > 0 ? "充入" : "放出";
}

function Meter({ value, max = 100, label }: { value: number; max?: number; label: string }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className="h-1.5 w-full overflow-hidden" style={{ background: "var(--accent-bg)", borderRadius: 2 }}
      role="meter" aria-valuemin={0} aria-valuemax={max} aria-valuenow={value} aria-label={label}>
      <div className="h-full" style={{ width: `${pct}%`, background: "var(--accent)" }} />
    </div>
  );
}

const big = { fontSize: 30, color: "var(--text)", fontWeight: 500 } as const;

export default function BatteryPanel({ b, systemWatts, series, stepSec }: {
  b: BatteryReading;
  systemWatts: number | null;
  series: Record<string, number[]>;
  stepSec: number;
}) {
  if (b.status !== "ok") {
    return <p className="text-xs" style={{ color: "var(--text-muted)" }}>● {b.error}</p>;
  }
  const eta = duration(b.minutes_to_full) ?? duration(b.minutes_to_empty);
  const cycles = b.cycle_count ?? 0;
  const life = b.design_cycle_count ?? 1000;
  return (
    <div className="grid md:grid-cols-3" style={card}>
      {/* charge */}
      <div className="p-4">
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>電量</span>
          <span className="text-right text-[11px]" style={{ color: b.permanent_failure ? "var(--status-err)" : "var(--text-muted)" }}>
            {b.permanent_failure ? "● 電池永久故障旗標" : b.state_label}
          </span>
        </div>
        <div className="mt-1 font-mono tabular-nums" style={big}>
          {fmt(b.percent, 0)}<span className="ml-1 text-sm" style={{ color: "var(--text-muted)" }}>%</span>
        </div>
        <Meter value={b.percent ?? 0} label="電池電量" />
        <div className="mt-2 font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
          {eta ? `${b.state === "charging" ? "預估充滿" : "預估可用"} ${eta}` : "無時間預估"}
          {b.daily_soc.min !== null && ` · 今日 ${b.daily_soc.min}–${b.daily_soc.max}%`}
        </div>
        <div className="mt-2 font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
          {fmt(b.capacity_mah, 0, " mAh")} · 電池 {fmt(b.temperature_c, 1, "°C")}
        </div>
      </div>

      {/* charge / discharge */}
      <div className="p-4 md:border-l" style={{ borderColor: "var(--border)" }}>
        <div className="text-xs" style={{ color: "var(--text-muted)" }}>充放電</div>
        <div className="mt-1 font-mono tabular-nums" style={big}>
          {b.battery_watts === null ? "—" : `${b.battery_watts > 0 ? "+" : ""}${b.battery_watts.toFixed(1)}`}
          <span className="ml-1 text-sm" style={{ color: "var(--text-muted)" }}>W {flowLabel(b)}</span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <Stat label="電源輸入" value={b.external_connected ? fmt(b.adapter_in_watts, 1, " W") : "未接"}
            sub={b.external_connected && b.adapter?.watts ? `${b.adapter.watts} W 充電器` : undefined} />
          <Stat label="系統負載" value={fmt(systemWatts, 1, " W")} />
          <Stat label="電流 / 電壓" value={`${fmt(b.amperage_ma, 0)} mA`} sub={fmt(b.voltage_v, 2, " V")} />
        </div>
        <div className="mt-2">
          <Sparkline values={series["b:w"] ?? []} unit="W" label="電池充放電功率" stepSec={stepSec} height={30} />
        </div>
      </div>

      {/* health */}
      <div className="p-4 md:border-l" style={{ borderColor: "var(--border)" }}>
        <div className="text-xs" style={{ color: "var(--text-muted)" }}>電池健康度</div>
        <div className="mt-1 font-mono tabular-nums" style={big}>
          {fmt(b.health_percent, 1)}<span className="ml-1 text-sm" style={{ color: "var(--text-muted)" }}>%</span>
        </div>
        <Meter value={Math.min(100, b.health_percent ?? 0)} label="電池健康度" />
        <div className="mt-2 font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
          滿電容量 {b.full_capacity_mah ?? "—"} / 設計 {b.design_capacity_mah ?? "—"} mAh
        </div>

        <div className="mt-4 flex items-baseline justify-between">
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>循環次數</span>
          <span className="font-mono text-sm tabular-nums" style={{ color: "var(--text)", fontWeight: 500 }}>
            {b.cycle_count ?? "—"}<span className="text-[11px]" style={{ color: "var(--text-subtle)" }}> / {life}</span>
          </span>
        </div>
        <div className="mt-1"><Meter value={cycles} max={life} label="循環次數" /></div>

        {b.cell_voltages_v.length > 0 && (
          <div className="mt-3 font-mono text-[11px] tabular-nums" style={{ color: "var(--text-subtle)" }}>
            電芯 {b.cell_voltages_v.map((v) => v.toFixed(3)).join(" / ")} V · 壓差{" "}
            {((Math.max(...b.cell_voltages_v) - Math.min(...b.cell_voltages_v)) * 1000).toFixed(0)} mV
          </div>
        )}
      </div>
    </div>
  );
}
