"use client";

import Link from "next/link";

interface Reference {
  trackLabel: string;
  stepNum: number;
  role: "mandatory" | "optional";
}

interface CrossReferencePanelProps {
  selectedSkill: string | null;
  references: Reference[];
}

/**
 * Right-side aside panel. Shows the selected skill's references across the
 * workflow tracks: which track / step / role (mandatory or optional). When
 * no skill is selected, renders a placeholder.
 */
export default function CrossReferencePanel({
  selectedSkill,
  references,
}: CrossReferencePanelProps) {
  if (!selectedSkill) {
    return (
      <aside
        style={{
          background: "var(--surface)",
          borderLeft: "1px solid var(--border)",
          padding: "var(--space-5)",
          width: 320,
          minWidth: 320,
        }}
      >
        <p
          className="font-mono uppercase"
          style={{
            fontSize: 10,
            color: "var(--text-subtle)",
            letterSpacing: "0.12em",
            marginBottom: "var(--space-4)",
          }}
        >
          Cross-reference
        </p>
        <p
          style={{
            color: "var(--text-muted)",
            fontSize: 13,
            lineHeight: 1.5,
          }}
        >
          Pick a skill chip to see where it appears across tracks and steps.
        </p>
      </aside>
    );
  }

  const mandatoryCount = references.filter((r) => r.role === "mandatory").length;
  const optionalCount = references.filter((r) => r.role === "optional").length;
  const skillSlug = selectedSkill.replace(/^\//, "");
  const display = selectedSkill.startsWith("/")
    ? selectedSkill.slice(1)
    : selectedSkill;

  return (
    <aside
      style={{
        background: "var(--surface)",
        borderLeft: "1px solid var(--border)",
        padding: "var(--space-5)",
        width: 320,
        minWidth: 320,
      }}
    >
      <p
        className="font-mono uppercase"
        style={{
          fontSize: 10,
          color: "var(--text-subtle)",
          letterSpacing: "0.12em",
          marginBottom: "var(--space-2)",
        }}
      >
        Cross-reference
      </p>
      <h3
        className="tracking-tight"
        style={{
          fontSize: 22,
          fontWeight: 500,
          lineHeight: 1.1,
          color: "var(--text)",
          letterSpacing: "-0.02em",
          marginBottom: "var(--space-1)",
        }}
      >
        {display}
      </h3>
      <p
        className="font-mono"
        style={{
          fontSize: 12,
          color: "var(--text-muted)",
          marginBottom: "var(--space-5)",
        }}
      >
        in <strong style={{ color: "var(--text)", fontWeight: 500 }}>{references.length} {references.length === 1 ? "track" : "tracks"}</strong>
        {" · "}
        {mandatoryCount} mandatory · {optionalCount} optional
      </p>

      <p
        className="font-mono uppercase"
        style={{
          fontSize: 10,
          color: "var(--text-subtle)",
          letterSpacing: "0.12em",
          marginBottom: "var(--space-2)",
        }}
      >
        References
      </p>
      {references.length === 0 ? (
        <p
          style={{
            color: "var(--text-muted)",
            fontSize: 13,
            paddingTop: "var(--space-2)",
          }}
        >
          Not referenced by any track. (Skill may be in maintenance, situational, or domain flow — see lower sections.)
        </p>
      ) : (
        references.map((r, i) => (
          <div
            key={`${r.trackLabel}-${r.stepNum}-${i}`}
            style={{
              padding: "var(--space-3) 0",
              borderBottom:
                i === references.length - 1
                  ? "none"
                  : "1px solid var(--border)",
              fontSize: 13,
            }}
          >
            <div style={{ color: "var(--text)", fontWeight: 500, marginBottom: 2 }}>
              {r.trackLabel}
            </div>
            <div
              className="font-mono"
              style={{ color: "var(--text-muted)", fontSize: 11 }}
            >
              step {r.stepNum} · {r.role}
            </div>
          </div>
        ))
      )}

      <Link
        href={`/skills/${encodeURIComponent(skillSlug)}`}
        className="block mt-6 text-center transition-colors"
        style={{
          padding: "var(--space-2) var(--space-3)",
          border: "1px solid var(--border-strong)",
          borderRadius: "var(--radius-sm)",
          color: "var(--text)",
          background: "var(--surface)",
          fontSize: 12,
          fontWeight: 500,
          textDecoration: "none",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = "var(--accent)";
          e.currentTarget.style.borderColor = "var(--accent)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = "var(--text)";
          e.currentTarget.style.borderColor = "var(--border-strong)";
        }}
      >
        Open /skills/{display} →
      </Link>
    </aside>
  );
}
