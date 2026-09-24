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
        <text x={x + w / 2} y={y + h / 2 + 7} textAnchor="middle" fontSize={20} fill="var(--text-subtle)">{label} 無讀數</text>
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
      <text x={x + w / 2} y={y + h / 2 - (sub ? 14 : 6)} textAnchor="middle" fontSize={20} fill={ink}>{label}</text>
      <text x={x + w / 2} y={y + h / 2 + (sub ? 16 : 24)} textAnchor="middle" fontSize={28} fontWeight={600} fill={ink}
        style={{ fontVariantNumeric: "tabular-nums" }}>
        {value.toFixed(1)}°{flag ? ` ${flag.label}` : ""}
      </text>
      {sub && <text x={x + w / 2} y={y + h / 2 + 40} textAnchor="middle" fontSize={17} fill={ink}>{sub}</text>}
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
      <text x={cx} y={cy - 6} textAnchor="middle" fontSize={20} fill="var(--text-muted)">
        {fan ? `風扇 F${fan.id}` : "風扇"}
      </text>
      <text x={cx} y={cy + 22} textAnchor="middle" fontSize={24} fontWeight={600} fill="var(--text)"
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
  const ranked = [...groups].sort((a, b) => b.max - a.max);
  return (
    <div className="grid gap-6 p-4 lg:grid-cols-[minmax(0,1.7fr)_minmax(220px,1fr)]" style={card}>
      <svg viewBox="0 0 1000 580" width="100%" role="img" aria-label="機身溫度分布圖（14 吋 MacBook Pro 俯視示意）"
        style={{ display: "block", fontFamily: "var(--font-sans)" }}>
        {/* chassis and trackpad outline for orientation */}
        <rect x={20} y={30} width={960} height={530} rx={40} fill="var(--bg)" stroke="var(--border-strong)" strokeWidth={2} />
        <text x={500} y={20} textAnchor="middle" fontSize={18} fill="var(--text-subtle)">↑ 螢幕轉軸（後側）</text>

        {/* logic board with SoC, SSD and Wi-Fi */}
        <rect x={275} y={55} width={450} height={250} rx={12} fill="var(--accent-bg)" stroke="var(--border-strong)" />
        <text x={285} y={297} fontSize={16} fill="var(--text-subtle)">主機板</text>
        <Spot x={420} y={85} w={170} h={98} label="CPU" value={g.cpu?.max}
          sub={g.cpu ? `平均 ${g.cpu.avg}°` : undefined} />
        <Spot x={420} y={190} w={170} h={98} label="GPU" value={g.gpu?.max}
          sub={g.gpu ? `平均 ${g.gpu.avg}°` : undefined} />
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
          <rect key={i} x={x} y={375} width={w} height={165} rx={10}
            fill={bat ? ramp(t(bat.avg)) : "var(--surface)"} fillOpacity={0.45} stroke="var(--border-strong)" />
        ))}
        <rect x={345} y={420} width={310} height={110} rx={12} fill="none" stroke="var(--border-strong)" strokeDasharray="6 6" />
        <text x={500} y={406} textAnchor="middle" fontSize={22} fill="var(--text)">
          電池 {bat ? `${bat.avg}°` : "無讀數"}
        </text>
        <text x={500} y={482} textAnchor="middle" fontSize={17} fill="var(--text-subtle)">觸控板</text>

        {/* palm rest surface probes */}
        {palm.slice(0, 2).map(([k, v], i) => (
          <Spot key={k} x={i ? 740 : 70} y={420} w={190} h={84} label={`掌托 ${k}`} value={v} />
        ))}
        {!palm.length && <Spot x={70} y={420} w={190} h={84} label="掌托" />}
      </svg>

      <div className="flex flex-col">
        <div className="mb-2 text-[11px]" style={{ color: "var(--text-muted)" }}>各區最高溫</div>
        <ul className="flex flex-col gap-1.5">
          {ranked.map((x) => {
            const flag = heat(x.max);
            return (
              <li key={x.id} className="grid grid-cols-[5.5rem_1fr_3.5rem] items-center gap-2 text-xs"
                title={Object.entries(x.sensors).map(([k, v]) => `${k} ${v}°`).join(" · ")}>
                <span style={{ color: "var(--text-muted)" }}>{x.label}</span>
                <span className="h-1.5 overflow-hidden" style={{ background: "var(--accent-bg)", borderRadius: 2 }}>
                  <span className="block h-full" style={{ width: `${Math.max(2, Math.min(100, t(x.max) * 100))}%`, background: flag ? flag.color : ramp(t(x.max)) }} />
                </span>
                <span className="text-right font-mono tabular-nums" style={{ color: flag ? flag.color : "var(--text)" }}>{x.max.toFixed(1)}°</span>
              </li>
            );
          })}
        </ul>
        <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px]" style={{ color: "var(--text-muted)" }}>
          <span className="flex items-center gap-2">
            <span className="font-mono">{T_LO}°</span>
            <span className="inline-block h-2 w-20" style={{ background: `linear-gradient(90deg, ${ramp(0)}, ${ramp(0.5)}, ${ramp(1)})`, borderRadius: 2 }} />
            <span className="font-mono">{T_HI}°</span>
          </span>
          <span><span style={{ color: "var(--status-warn)" }}>●</span> ≥85°　<span style={{ color: "var(--status-err)" }}>●</span> ≥95°</span>
        </div>
        <p className="mt-auto pt-4 text-[11px] leading-relaxed" style={{ color: "var(--text-subtle)" }}>
          位置為 14 吋 MacBook Pro 示意。左右出風口依鍵名判定；風扇、掌托、電池探針的左右 Apple 未公開，僅為排版。
          另有 {otherCount} 個位置不明的感測器列在下方明細。
        </p>
      </div>
    </div>
  );
}
