interface CycleEstimate {
  per_percent: number;
  week_tokens: number;
  steps: number;
  rough: boolean;
  model: string | null;
}

interface CycleWindow {
  resets_at: number;
  reset_exact: number | null;
  first_at: number;
  last_at: number;
  week_estimate: CycleEstimate | null;
}

interface CycleRow {
  key: string;
  label: string;
  cycles: CycleWindow[];
}

const millions = (value: number) => `${(value / 1e6).toFixed(1)}M`;
const modelName = (model: string | null) => {
  if (!model) return "未知";
  return model.startsWith("claude-") ? model.slice(7) : model;
};
const resetTime = (cycle: CycleWindow) => cycle.reset_exact ?? cycle.resets_at;
const pad = (n: number) => String(n).padStart(2, "0");
const shortDate = (epoch: number) => {
  const date = new Date(epoch * 1000);
  return `${pad(date.getMonth() + 1)}/${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
};
const MONO = { fontFamily: "var(--font-mono)", fontVariantNumeric: "tabular-nums" };
const CURRENT = "var(--accent)";
const CLOSED = "#8aa399";
const CONNECTOR = "#d1ddd5";
const SLOT_WIDTH = 132;
const SLOT_GAP = 10;
const BASELINE = 128;

function LegendLine({ color, text, dashed = false }: { color: string; text: string; dashed?: boolean }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, marginRight: 12 }}>
      <svg width={20} height={8} aria-hidden="true">
        <line x1={1} y1={4} x2={19} y2={4} stroke={color} strokeWidth={3}
          strokeLinecap="round" strokeDasharray={dashed ? "5 4" : undefined} />
      </svg>
      {text}
    </span>
  );
}

export default function QuotaCycleChart({ rows, now }: { rows: CycleRow[]; now: number }) {
  const visible = rows.map((row) => ({
    ...row,
    // Cycle order, not start order: Claude windows of one account can overlap
    // in time, and the current cycle must stay at the right end.
    cycles: row.cycles.filter((cycle) => cycle.week_estimate)
      .sort((a, b) => resetTime(a) - resetTime(b) || a.first_at - b.first_at)
      .slice(-12),
  })).filter((row) => row.cycles.length > 0);
  if (visible.length === 0) return null;

  return (
    <div className="mt-4" style={{ border: "1px solid var(--border)", borderRadius: 6, padding: 16, background: "var(--surface)" }}>
      <h3 style={{ fontSize: 18, fontWeight: 500, color: "var(--text)" }}>每個使用區段的用滿一週預估</h3>
      <p style={{ fontSize: 11, color: "var(--text-subtle)", marginTop: 4 }}>
        <LegendLine color={CURRENT} text="目前區段" />
        <LegendLine color={CLOSED} text="已結束的區段" />
        <LegendLine color={CURRENT} text="虛線＝粗估（不到 10 筆）" dashed />
        每列各自比例尺
      </p>
      {visible.map((row) => {
        const max = Math.max(...row.cycles.map((cycle) => cycle.week_estimate!.week_tokens));
        const chartWidth = row.cycles.length * SLOT_WIDTH;
        const yFor = (tokens: number) => BASELINE - (max > 0 ? Math.max(3, tokens / max * 80) : 3);
        return (
          <div key={row.key} style={{ marginTop: 20 }}>
            <div style={{ fontSize: 12, color: "var(--text)", marginBottom: 4 }}>{row.label}</div>
            <div style={{ overflowX: "auto" }}>
              <svg width={chartWidth} height={192} viewBox={`0 0 ${chartWidth} 192`} role="img" aria-label={`${row.label}每個使用區段的用滿一週預估`}>
                <line x1={0} y1={BASELINE} x2={chartWidth} y2={BASELINE} stroke={CONNECTOR} strokeWidth={1} />
                {row.cycles.map((cycle, index) => {
                  const estimate = cycle.week_estimate!;
                  const reset = resetTime(cycle);
                  const x1 = index * SLOT_WIDTH + SLOT_GAP;
                  const x2 = (index + 1) * SLOT_WIDTH - SLOT_GAP;
                  const center = (x1 + x2) / 2;
                  const y = yFor(estimate.week_tokens);
                  const color = reset > now ? CURRENT : CLOSED;
                  const next = row.cycles[index + 1];
                  return (
                    <g key={`${cycle.first_at}:${reset}:${cycle.last_at}`}>
                      {next && <line x1={x2} y1={y} x2={(index + 1) * SLOT_WIDTH + SLOT_GAP}
                        y2={yFor(next.week_estimate!.week_tokens)} stroke={CONNECTOR} strokeWidth={1} />}
                      <line x1={x1} y1={y} x2={x2} y2={y} stroke={color} strokeWidth={3}
                        strokeLinecap="round" strokeDasharray={estimate.rough ? "5 4" : undefined}>
                        <title>{`使用區段 ${shortDate(cycle.first_at)} → ${shortDate(cycle.last_at)}；週期重置 ${shortDate(reset)}；模型 ${modelName(estimate.model)}；每 1% 約 ${millions(estimate.per_percent)}；取 ${estimate.steps} 筆${estimate.rough ? "；粗估" : ""}`}</title>
                      </line>
                      <text x={center} y={y - 9} textAnchor="middle" fill="var(--text-subtle)" fontSize={10} style={MONO}>{millions(estimate.week_tokens)}</text>
                      <text x={center} y={BASELINE + 19} textAnchor="middle" fill="var(--text-subtle)" fontSize={10} style={MONO}>{shortDate(cycle.first_at)}</text>
                      <text x={center} y={BASELINE + 34} textAnchor="middle" fill="var(--text-subtle)" fontSize={10} style={MONO}>→ {shortDate(cycle.last_at)}</text>
                      <text x={center} y={BASELINE + 49} textAnchor="middle" fill="var(--text-subtle)" fontSize={10} style={MONO}>{modelName(estimate.model)}</text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>
        );
      })}
    </div>
  );
}
