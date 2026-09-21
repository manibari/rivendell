"use client";

import SkillChip from "@/components/SkillChip";

export interface StepData {
  num: number;
  label: string;
  desc?: string;
  mandatory?: string[];
  optional?: string[];
}

interface StepNodeProps {
  step: StepData;
  /** When true, render with active outline (e.g. "current step") */
  active?: boolean;
  /** Skill name currently selected in cross-ref panel */
  selectedSkill?: string | null;
  /** Click handler for skill chips — wired by page to lift state */
  onSkillClick?: (name: string) => void;
}

export default function StepNode({
  step,
  active = false,
  selectedSkill,
  onSkillClick,
}: StepNodeProps) {
  const allMandatory = step.mandatory ?? [];
  const allOptional = step.optional ?? [];

  return (
    <div
      style={{
        background: "var(--surface)",
        border: active ? "1.5px solid var(--accent)" : "1px solid var(--border-strong)",
        borderRadius: "var(--radius-md)",
        padding: "var(--space-3) var(--space-4)",
        width: 165,
        flexShrink: 0,
        position: "relative",
        zIndex: 1,
      }}
    >
      <div
        className="font-mono uppercase"
        style={{
          fontSize: 10,
          color: "var(--text-subtle)",
          letterSpacing: "0.12em",
          marginBottom: 2,
        }}
      >
        step {step.num}
      </div>
      <div
        style={{
          fontSize: 14,
          fontWeight: 500,
          lineHeight: 1.2,
          color: "var(--text)",
          margin: "4px 0 var(--space-2)",
          letterSpacing: "-0.01em",
        }}
      >
        {step.label}
      </div>
      <div className="flex flex-col gap-1">
        {allMandatory.map((s) => (
          <SkillChip
            key={`m-${s}`}
            name={s}
            variant={selectedSkill === s ? "highlighted" : "default"}
            asLink={false}
            onClick={onSkillClick}
          />
        ))}
        {allOptional.map((s) => (
          <SkillChip
            key={`o-${s}`}
            name={s}
            variant={selectedSkill === s ? "highlighted" : "optional"}
            asLink={false}
            onClick={onSkillClick}
          />
        ))}
      </div>
    </div>
  );
}
