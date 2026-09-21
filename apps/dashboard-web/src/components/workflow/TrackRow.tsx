"use client";

import StepNode, { type StepData } from "./StepNode";

export interface TrackData {
  id: string;
  label: string;
  steps: StepData[];
}

interface TrackRowProps {
  track: TrackData;
  selectedSkill?: string | null;
  onSkillClick?: (name: string) => void;
  /** Index of the "current" step (1-based via step.num) — accents one connector */
  currentStepNum?: number;
}

/**
 * Renders one workflow track as a horizontal flow of step nodes connected by
 * Bezier curves. Connectors live in an absolutely-positioned SVG layer behind
 * the nodes (z-index 0), matching dashboard-next/mockups/workflow-map-v4.html.
 *
 * Layout math: each step node is 165px wide with 60px right-margin. Connectors
 * span the 60px gap. Total width = stepCount * 225 - 60.
 */
export default function TrackRow({
  track,
  selectedSkill,
  onSkillClick,
  currentStepNum,
}: TrackRowProps) {
  const stepCount = track.steps.length;
  const NODE_W = 165;
  const GAP = 60;
  const totalWidth = stepCount * NODE_W + (stepCount - 1) * GAP;

  // Connector geometry. Each path goes from x=NODE_W (end of node N) to
  // x=NODE_W+GAP (start of node N+1) in node N's local frame; we offset
  // by the cumulative left position. Y is centered (~65 in mockup viewBox).
  const connectors = Array.from({ length: stepCount - 1 }, (_, i) => {
    const x1 = (i + 1) * NODE_W + i * GAP;
    const x2 = x1 + GAP;
    const yMid = 65;
    // Slight alternating wobble for hand-drawn feel
    const c1y = i % 2 === 0 ? yMid - 13 : yMid + 13;
    const c2y = i % 2 === 0 ? yMid + 13 : yMid - 13;
    const isCurrent =
      currentStepNum !== undefined &&
      track.steps[i].num === currentStepNum &&
      track.steps[i + 1] !== undefined;
    return {
      key: i,
      d: `M ${x1} ${yMid} C ${x1 + 30} ${c1y}, ${x2 - 30} ${c2y}, ${x2} ${yMid}`,
      stroke: isCurrent ? "var(--accent)" : "var(--accent-soft)",
      strokeWidth: isCurrent ? 2 : 1.5,
    };
  });

  return (
    <div className="mb-12 relative">
      <h3
        className="mb-5 tracking-tight"
        style={{
          fontSize: 22,
          fontWeight: 500,
          lineHeight: 1,
          color: "var(--text)",
          letterSpacing: "-0.02em",
        }}
      >
        {track.label}
      </h3>
      <div
        className="relative"
        style={{
          paddingTop: "var(--space-3)",
          paddingBottom: "var(--space-3)",
          minWidth: totalWidth,
        }}
      >
        {/* Connectors layer */}
        {stepCount > 1 && (
          <svg
            aria-hidden
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              pointerEvents: "none",
              zIndex: 0,
            }}
            viewBox={`0 0 ${totalWidth} 130`}
            preserveAspectRatio="none"
          >
            {connectors.map((c) => (
              <path
                key={c.key}
                d={c.d}
                stroke={c.stroke}
                strokeWidth={c.strokeWidth}
                fill="none"
                strokeLinecap="round"
              />
            ))}
          </svg>
        )}

        {/* Nodes */}
        <div className="flex items-stretch" style={{ gap: GAP }}>
          {track.steps.map((step) => (
            <StepNode
              key={step.num}
              step={step}
              active={step.num === currentStepNum}
              selectedSkill={selectedSkill}
              onSkillClick={onSkillClick}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
