import type { SensorFan, SensorGroup } from "@/lib/api";
import { card, heat, onRamp, ramp } from "./ui";

// Top-down x-ray of a 14" MacBook Pro base (hinge at the top), with each
// temperature group drawn where that part sits. Only placement is decided
// here; grouping and values come from the API. Left/right vents are read from
// the SMC key names (TaL* / TaR*); which fan, palm-rest probe and battery
// probe is on which side is not published, so those are labelled by key.

const T_LO = 30;
const T_HI = 95;
const t = (c: number) => (c - T_LO) / (T_HI - T_LO);

function Spot({ x, y, w, h, label, value, sub }: {
  x: number; y: number; w: number; h: number; label: string; value?: number; sub?: string;
}) {
  if (value === undefined) {
    return (
      <g>
        <rect x={x} y={y} width={w} height={h} rx={8} fill="var(--surface)" stroke="var(--border-strong)" strokeDasharray="4 4" />
        <text x={x + w / 2} y={y + h / 2 + 6} textAnchor="middle" fontSize={16} fill="var(--text-subtle)">{label} 無讀數</text>
      </g>
    );
  }
  const k = t(value);
  const flag = heat(value);
  const ink = onRamp(k);
  return (
    <g>
      <title>{`${label} ${value.toFixed(1)}°C${sub ? `\n${sub}` : ""}`}</title>
      <rect x={x} y={y} width={w} height={h} rx={8} fill={ramp(k)}
        stroke={flag ? flag.color : "var(--border-strong)"} strokeWidth={flag ? 4 : 1} />
      <text x={x + w / 2} y={y + h / 2 - (sub ? 8 : 0)} textAnchor="middle" fontSize={16} fill={ink}>{label}</text>
      <text x={x + w / 2} y={y + h / 2 + (sub ? 16 : 22)} textAnchor="middle" fontSize={22} fontWeight={600} fill={ink}
        style={{ fontVariantNumeric: "tabular-nums" }}>
        {value.toFixed(1)}°{flag ? ` ${flag.label}` : ""}
      </text>
      {sub && <text x={x + w / 2} y={y + h / 2 + 38} textAnchor="middle" fontSize={13} fill={ink}>{sub}</text>}
    </g>
  );
}

function Fan({ cx, cy, fan }: { cx: number; cy: number; fan?: SensorFan }) {
  return (
    <g>
      <circle cx={cx} cy={cy} r={92} fill="var(--surface)" stroke="var(--border-strong)" />
      <circle cx={cx} cy={cy} r={22} fill="none" stroke="var(--border-strong)" />
      {[0, 60, 120, 180, 240, 300].map((a) => (
        <path key={a} d={`M${cx},${cy - 24} Q${cx + 34},${cy - 52} ${cx + 8},${cy - 88}`} fill="none"
          stroke="var(--border)" strokeWidth={2} transform={`rotate(${a} ${cx} ${cy})`} />
      ))}
      <text x={cx} y={cy - 4} textAnchor="middle" fontSize={15} fill="var(--text-muted)">
        {fan ? `風扇 F${fan.id}` : "風扇"}
      </text>
      <text x={cx} y={cy + 18} textAnchor="middle" fontSize={18} fontWeight={600} fill="var(--text)"
        style={{ fontVariantNumeric: "tabular-nums" }}>
        {fan ? `${fan.rpm} RPM` : "—"}
      </text>
    </g>
  );
}

export default function LaptopMap({ groups, fans, otherCount }: {
  groups: SensorGroup[];
  fans: SensorFan[];
  otherCount: number;
}) {
  const g = Object.fromEntries(groups.map((x) => [x.id, x]));
  const bat = g.battery;
  const palm = Object.entries(g.palm?.sensors ?? {});
  return (
    <div className="p-4" style={card}>
      <svg viewBox="0 0 1000 720" width="100%" role="img" aria-label="機身溫度分布圖（14 吋 MacBook Pro 俯視示意）"
        style={{ display: "block", maxWidth: 880, margin: "0 auto", fontFamily: "var(--font-sans)" }}>
        {/* chassis and trackpad outline for orientation */}
        <rect x={20} y={30} width={960} height={670} rx={40} fill="var(--bg)" stroke="var(--border-strong)" strokeWidth={2} />
        <text x={500} y={22} textAnchor="middle" fontSize={14} fill="var(--text-subtle)">↑ 螢幕轉軸（後側）</text>
        <rect x={330} y={440} width={340} height={230} rx={14} fill="none" stroke="var(--border)" strokeDasharray="6 6" />
        <text x={660} y={662} textAnchor="end" fontSize={12} fill="var(--text-subtle)">觸控板範圍</text>

        {/* logic board with SoC, SSD and Wi-Fi */}
        <rect x={275} y={55} width={450} height={250} rx={12} fill="var(--accent-bg)" stroke="var(--border-strong)" />
        <text x={285} y={296} fontSize={12} fill="var(--text-subtle)">主機板</text>
        <Spot x={420} y={85} w={170} h={98} label="CPU" value={g.cpu?.max}
          sub={g.cpu ? `平均 ${g.cpu.avg}° · ${Object.keys(g.cpu.sensors).length} 探針` : undefined} />
        <Spot x={420} y={190} w={170} h={98} label="GPU" value={g.gpu?.max}
          sub={g.gpu ? `平均 ${g.gpu.avg}° · ${Object.keys(g.gpu.sensors).length} 探針` : undefined} />
        <Spot x={600} y={85} w={115} h={98} label="SSD" value={g.ssd?.max} />
        <Spot x={290} y={85} w={120} h={98} label="Wi-Fi" value={g.wifi?.max} />

        <Fan cx={165} cy={175} fan={fans[0]} />
        <Fan cx={835} cy={175} fan={fans[1]} />
        <Spot x={70} y={276} w={190} h={84} label="左出風口" value={g.airflow_l?.avg}
          sub={g.airflow_l ? `最高 ${g.airflow_l.max}°` : undefined} />
        <Spot x={740} y={276} w={190} h={84} label="右出風口" value={g.airflow_r?.avg}
          sub={g.airflow_r ? `最高 ${g.airflow_r.max}°` : undefined} />

        {/* battery cells under palm rests and trackpad */}
        {[[60, 250], [335, 330], [690, 250]].map(([x, w], i) => (
          <rect key={i} x={x} y={370} width={w} height={300} rx={10}
            fill={bat ? ramp(t(bat.avg)) : "var(--surface)"} fillOpacity={0.55} stroke="var(--border-strong)" />
        ))}
        <text x={500} y={410} textAnchor="middle" fontSize={16} fill="var(--text)">
          電池 {bat ? `平均 ${bat.avg}° · 最高 ${bat.max}°` : "無讀數"}
        </text>
        <text x={500} y={434} textAnchor="middle" fontSize={13} fill="var(--text-muted)">
          {bat ? Object.entries(bat.sensors).map(([k, v]) => `${k} ${v}°`).join(" · ") : ""}
        </text>

        {/* palm rest surface probes */}
        {palm.slice(0, 2).map(([k, v], i) => (
          <Spot key={k} x={i ? 740 : 70} y={560} w={190} h={80} label={`掌托 ${k}`} value={v} />
        ))}
        {!palm.length && <Spot x={70} y={560} w={190} h={80} label="掌托" />}
      </svg>

      <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px]" style={{ color: "var(--text-muted)" }}>
        <span className="flex items-center gap-2">
          <span className="font-mono">{T_LO}°</span>
          <span className="inline-block h-2 w-28" style={{ background: `linear-gradient(90deg, ${ramp(0)}, ${ramp(0.5)}, ${ramp(1)})`, borderRadius: 2 }} />
          <span className="font-mono">{T_HI}°</span>
        </span>
        <span><span style={{ color: "var(--status-warn)" }}>●</span> ≥85° 偏高　<span style={{ color: "var(--status-err)" }}>●</span> ≥95° 過熱</span>
      </div>
      <p className="mt-2 text-[11px] leading-relaxed" style={{ color: "var(--text-subtle)" }}>
        位置依 14 吋 MacBook Pro 內部配置示意。CPU / GPU 方塊顯示該區最高溫；左右出風口依 SMC 鍵名（TaL / TaR）判定；
        風扇 F0/F1、掌托 Ts0P/Ts1P、三個電池探針各在哪一側 Apple 未公開，圖上以鍵名標示、左右僅為排版。
        另有 {otherCount} 個感測器位置不明，列在下方「未分類溫度鍵」。
      </p>
    </div>
  );
}
