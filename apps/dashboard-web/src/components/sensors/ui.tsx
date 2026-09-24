import Sparkline from "@/components/Sparkline";

// Shared building blocks for the system monitor page (/health/sensors).

export const card = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
} as const;

export type Flag = { label: string; color: string } | null;

// Status colors are reserved for state and always ship with a text label.
export function heat(c: number): Flag {
  if (c >= 95) return { label: "過熱", color: "var(--status-err)" };
  if (c >= 85) return { label: "偏高", color: "var(--status-warn)" };
  return null;
}

// Sequential greens from DESIGN.md (#d1ddd5 / #8aa399 / #2d4a3e) for ordinal
// encoding: t in [0, 1] -> light to forest.
const RAMP = [
  [0xd1, 0xdd, 0xd5],
  [0x8a, 0xa3, 0x99],
  [0x2d, 0x4a, 0x3e],
];
export function ramp(t: number): string {
  const x = Math.max(0, Math.min(1, t)) * (RAMP.length - 1);
  const i = Math.min(RAMP.length - 2, Math.floor(x));
  const f = x - i;
  const c = RAMP[i].map((a, k) => Math.round(a + (RAMP[i + 1][k] - a) * f));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}
/** text color that stays readable on ramp(t) */
export const onRamp = (t: number) => (t > 0.55 ? "#ffffff" : "var(--text)");

export function fmt(v: number | null | undefined, digits = 1, unit = ""): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${v.toFixed(digits)}${unit}`;
}

export function Tile({ title, value, unit, sub, series, stepSec, flag, digits = 1 }: {
  title: string;
  value: number | null;
  unit: string;
  sub?: string;
  series: number[];
  stepSec: number;
  flag?: Flag;
  digits?: number;
}) {
  return (
    <div className="p-4" style={card}>
      <div className="flex items-center justify-between text-xs" style={{ color: "var(--text-muted)" }}>
        <span>{title}</span>
        {flag && <span className="font-mono text-[10px]" style={{ color: flag.color }}>● {flag.label}</span>}
      </div>
      <div className="mt-1 font-mono tabular-nums" style={{ fontSize: 26, color: "var(--text)", fontWeight: 500 }}>
        {value === null ? "—" : value.toFixed(digits)}
        <span className="ml-1 text-sm" style={{ color: "var(--text-muted)" }}>{unit}</span>
      </div>
      <div className="mb-2 h-4 truncate font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>{sub}</div>
      <Sparkline values={series} unit={unit} label={title} stepSec={stepSec} />
    </div>
  );
}

export function Section({ title, note, children }: { title: string; note?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="mt-8">
      <div className="mb-2 flex flex-wrap items-baseline gap-x-3">
        <h2 className="text-base" style={{ color: "var(--text)", fontWeight: 500, letterSpacing: "-0.01em" }}>{title}</h2>
        {note && <span className="font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>{note}</span>}
      </div>
      {children}
    </section>
  );
}

export function Rows({ head, rows }: { head: string[]; rows: (string | number)[][] }) {
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

export function RawList({ title, values, unit }: { title: string; values: Record<string, number>; unit: string }) {
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

export function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div>
      <div className="text-[11px]" style={{ color: "var(--text-muted)" }}>{label}</div>
      <div className="font-mono tabular-nums text-sm" style={{ color: "var(--text)", fontWeight: 500 }}>{value}</div>
      {sub && <div className="font-mono text-[10px]" style={{ color: "var(--text-subtle)" }}>{sub}</div>}
    </div>
  );
}
