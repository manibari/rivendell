"use client";

import { useId, useState } from "react";

// Single-series trend line for a stat tile. One series means one color (the
// accent token) and no legend; the tile title names the series. Hover shows
// the value at the nearest sample, so the line never has to carry labels.
export default function Sparkline({
  values,
  unit,
  label,
  stepSec,
  height = 36,
}: {
  values: number[];
  unit: string;
  label: string;
  /** seconds between samples, for the hover readout */
  stepSec: number;
  height?: number;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const gradId = useId();
  const W = 200;
  if (values.length < 2) {
    return <div style={{ height }} aria-hidden />;
  }
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const span = hi - lo || 1;
  const pad = 3;
  const x = (i: number) => (i / (values.length - 1)) * W;
  const y = (v: number) => pad + (1 - (v - lo) / span) * (height - pad * 2);
  const d = values.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
  const last = values.length - 1;
  const at = hover ?? last;

  return (
    <div className="relative">
      <svg
        viewBox={`0 0 ${W} ${height}`}
        width="100%"
        height={height}
        preserveAspectRatio="none"
        role="img"
        aria-label={`${label} 最近 ${values.length} 次取樣，${lo.toFixed(1)}–${hi.toFixed(1)} ${unit}`}
        onMouseMove={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          const i = Math.round(((e.clientX - r.left) / r.width) * last);
          setHover(Math.max(0, Math.min(last, i)));
        }}
        onMouseLeave={() => setHover(null)}
        style={{ display: "block", cursor: "crosshair" }}
      >
        <defs>
          <linearGradient id={gradId} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.18} />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <path d={`${d}L${W},${height}L0,${height}Z`} fill={`url(#${gradId})`} stroke="none" />
        <path d={d} fill="none" stroke="var(--accent)" strokeWidth={2} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
        {hover !== null && (
          <line x1={x(at)} x2={x(at)} y1={0} y2={height} stroke="var(--border-strong)" strokeWidth={1} vectorEffect="non-scaling-stroke" />
        )}
      </svg>
      {hover !== null && (
        <span
          className="pointer-events-none absolute -top-5 font-mono text-[10px] tabular-nums"
          style={{
            left: `${(at / last) * 100}%`,
            transform: "translateX(-50%)",
            color: "var(--text)",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 4,
            padding: "0 4px",
            whiteSpace: "nowrap",
          }}
        >
          {values[at].toFixed(1)} {unit} · {last - at === 0 ? "現在" : `${(last - at) * stepSec}s 前`}
        </span>
      )}
    </div>
  );
}
