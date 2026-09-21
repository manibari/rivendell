"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { X } from "lucide-react";
import {
  workflows,
  skillDetails,
  type Chip as ChipData,
  type WorkflowId,
  type Step as StepData,
  type OptionalRow,
  type MaintenanceRow,
} from "./playbook-data";

// ─────────────────────────────────────────────────────────── Chip component
function ChipPill({
  chip,
  onClick,
}: {
  chip: ChipData;
  onClick: (key: string) => void;
}) {
  const { key, category } = chip;
  const isCritical = category === "critical";
  const isCore = category === "core";
  return (
    <button
      type="button"
      onClick={() => onClick(key)}
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: 11,
        padding: "2px 7px",
        borderRadius: 3,
        cursor: "pointer",
        background: "var(--surface)",
        border: isCritical
          ? "1px dashed var(--status-err)"
          : "1px solid var(--border-strong)",
        color: isCritical
          ? "var(--status-err)"
          : isCore
            ? "var(--accent)"
            : "var(--text-muted)",
        transition: "color 0.15s ease, border-color 0.15s ease",
      }}
      onMouseEnter={(e) => {
        if (!isCritical) {
          e.currentTarget.style.borderColor = "var(--accent)";
          e.currentTarget.style.color = "var(--accent)";
        }
      }}
      onMouseLeave={(e) => {
        if (!isCritical) {
          e.currentTarget.style.borderColor = "var(--border-strong)";
          e.currentTarget.style.color = isCore
            ? "var(--accent)"
            : "var(--text-muted)";
        }
      }}
    >
      /{key}
    </button>
  );
}

const labelStyle: React.CSSProperties = {
  fontSize: 12,
  color: "var(--text-subtle)",
  fontFamily: "var(--font-mono)",
};

function BranchLine({
  label,
  chips,
  inlineNote,
  onChipClick,
}: {
  label: string;
  chips: ChipData[];
  inlineNote?: string;
  onChipClick: (key: string) => void;
}) {
  return (
    <div
      className="flex flex-wrap items-baseline gap-2 mt-2.5"
      style={{ paddingLeft: 18, position: "relative", lineHeight: 1.6 }}
    >
      <span
        aria-hidden
        style={{
          position: "absolute",
          left: 0,
          top: 2,
          color: "var(--text-subtle)",
          fontSize: 13,
          fontFamily: "var(--font-mono)",
        }}
      >
        ↳
      </span>
      <span style={labelStyle}>{label}</span>
      {chips.map((c) => (
        <ChipPill key={c.key} chip={c} onClick={onChipClick} />
      ))}
      {inlineNote && (
        <span
          style={{
            color: "var(--text-subtle)",
            fontSize: 12,
            fontStyle: "italic",
            marginLeft: 4,
          }}
        >
          {inlineNote}
        </span>
      )}
    </div>
  );
}

function OptionalRowView({
  row,
  onChipClick,
}: {
  row: OptionalRow;
  onChipClick: (key: string) => void;
}) {
  // Each (label, chips) tuple becomes its own branch line so the
  // if/then nature of step optionals is visually unambiguous.
  return (
    <>
      <BranchLine
        label={row.label}
        chips={row.chips}
        inlineNote={row.inlineNote}
        onChipClick={onChipClick}
      />
      {row.secondLabel && (
        <BranchLine
          label={row.secondLabel}
          chips={row.secondChips ?? []}
          onChipClick={onChipClick}
        />
      )}
    </>
  );
}

function StepRow({
  step,
  onChipClick,
}: {
  step: StepData;
  onChipClick: (key: string) => void;
}) {
  const numStr = /^\d+$/.test(step.num) ? step.num.padStart(2, "0") : step.num;
  return (
    <div
      className="flex items-start gap-5 py-5"
      style={{ borderTop: "1px solid var(--border)" }}
    >
      <span
        className="shrink-0 pt-0.5"
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 12,
          color: "var(--text-subtle)",
          width: 28,
          fontFeatureSettings: "'tnum' 1",
        }}
      >
        {numStr}
      </span>
      <div className="min-w-0 flex-1">
        <div
          style={{
            color: "var(--text)",
            fontSize: 14,
            fontWeight: 500,
            lineHeight: 1.6,
          }}
        >
          {step.action}
        </div>
        {step.detail && (
          <div
            className="mt-1"
            style={{
              color: "var(--text-muted)",
              fontSize: 13,
              lineHeight: 1.6,
            }}
          >
            {step.detail}
          </div>
        )}
        {step.chips && step.chips.length > 0 && (
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {step.chips.map((c) => (
              <ChipPill key={c.key} chip={c} onClick={onChipClick} />
            ))}
            {step.inlineNote && (
              <span
                style={{
                  color: "var(--text-subtle)",
                  fontSize: 12,
                  fontStyle: "italic",
                  marginLeft: 4,
                }}
              >
                {step.inlineNote}
              </span>
            )}
          </div>
        )}
        {step.optionals?.map((row, i) => (
          <OptionalRowView key={i} row={row} onChipClick={onChipClick} />
        ))}
        {step.hardGate && (
          <div
            className="mt-3 pl-3"
            style={{
              borderLeft: "2px solid var(--status-warn)",
              color: "var(--text-muted)",
              fontSize: 13,
              fontStyle: "italic",
              lineHeight: 1.5,
            }}
          >
            {step.hardGate}
          </div>
        )}
      </div>
    </div>
  );
}

function MaintenanceList({
  rows,
  onChipClick,
}: {
  rows: MaintenanceRow[];
  onChipClick: (key: string) => void;
}) {
  return (
    <div>
      {rows.map((row, i) => (
        <div
          key={i}
          className="grid items-baseline gap-6 py-3"
          style={{
            gridTemplateColumns: "minmax(0, 1fr) minmax(0, 2fr)",
            borderTop: "1px solid var(--border)",
          }}
        >
          <span style={{ color: "var(--text-muted)", fontSize: 13 }}>
            {row.when}
          </span>
          <div className="flex flex-wrap items-center gap-2">
            {row.chips.map((c) => (
              <ChipPill key={c.key} chip={c} onClick={onChipClick} />
            ))}
            {row.sequence?.map((seg, j) => (
              <span key={j} className="flex items-center gap-2">
                <span
                  style={{
                    color: "var(--text-subtle)",
                    fontSize: 12,
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {seg.connector === "arrow" ? "→" : "→ then"}
                </span>
                {seg.chips.map((c) => (
                  <ChipPill key={c.key} chip={c} onClick={onChipClick} />
                ))}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function DetailBlock({
  label,
  body,
  muted,
}: {
  label: string;
  body: string;
  muted?: boolean;
}) {
  return (
    <div className="mt-3 pl-3" style={{ borderLeft: "2px solid var(--border)" }}>
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 10,
          textTransform: "uppercase",
          letterSpacing: "0.12em",
          color: "var(--text-subtle)",
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <p
        style={{
          color: muted ? "var(--text-muted)" : "var(--text)",
          fontSize: 13,
          lineHeight: 1.6,
        }}
      >
        {body}
      </p>
    </div>
  );
}

function SkillModal({
  skillKey,
  onClose,
}: {
  skillKey: string | null;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!skillKey) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [skillKey, onClose]);

  if (!skillKey) return null;
  const data = skillDetails[skillKey];

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center px-4"
      style={{ background: "rgba(10, 10, 10, 0.4)" }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-lg p-7"
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border-strong)",
          borderRadius: "var(--radius-lg)",
        }}
      >
        <button
          onClick={onClose}
          aria-label="close"
          className="absolute right-3 top-3 p-1.5 transition-colors"
          style={{ color: "var(--text-subtle)" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text)")}
          onMouseLeave={(e) =>
            (e.currentTarget.style.color = "var(--text-subtle)")
          }
        >
          <X size={14} />
        </button>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 16,
            fontWeight: 500,
            color: "var(--accent)",
            marginBottom: 14,
          }}
        >
          /{skillKey}
        </div>
        {data ? (
          <>
            <p
              style={{
                color: "var(--text)",
                fontSize: 14,
                lineHeight: 1.7,
                marginBottom: 16,
              }}
            >
              {data.desc}
            </p>
            {data.trigger && <DetailBlock label="trigger" body={data.trigger} />}
            {data.skip && <DetailBlock label="skip" body={data.skip} muted />}
          </>
        ) : (
          <p style={{ color: "var(--text-muted)", fontSize: 14 }}>
            (no description available)
          </p>
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────── Public FlowView
// useSearchParams() needs a <Suspense> boundary or every static page's
// prerender fails at build ("missing-suspense-with-csr-bailout" — see
// learnings 2026-05-16; this exact miss broke the 2026-07-05 06:00 build and
// took the dashboard down). Hook lives in the inner component; the default
// export only provides the boundary.
export default function FlowView(props: { flowId: WorkflowId }) {
  return (
    <Suspense fallback={null}>
      <FlowViewInner {...props} />
    </Suspense>
  );
}

function FlowViewInner({ flowId }: { flowId: WorkflowId }) {
  const [openSkill, setOpenSkill] = useState<string | null>(null);
  const searchParams = useSearchParams();
  // Slide branch is URL-driven now (sidebar children navigate via
  // ?branch=...). Default to the first branch when no param is set.
  const branchParam = searchParams.get("branch");

  const current = workflows.find((w) => w.id === flowId);
  if (!current) {
    return (
      <p style={{ color: "var(--text-muted)", fontSize: 14 }}>
        Unknown workflow id: <code>{flowId}</code>
      </p>
    );
  }
  const activeBranch =
    branchParam && current.branches?.some((b) => b.id === branchParam)
      ? branchParam
      : current.branches?.[0]?.id;
  const visibleBranch = current.branches?.find((b) => b.id === activeBranch);

  return (
    <>
      <h2
        style={{
          fontSize: 16,
          fontWeight: 500,
          color: "var(--text)",
          letterSpacing: "-0.01em",
        }}
      >
        {current.heading}
      </h2>

      {current.lead && (
        <p
          className="mt-3 pl-3"
          style={{
            borderLeft: `2px solid ${
              current.lead.tone === "warn"
                ? "var(--status-warn)"
                : "var(--border)"
            }`,
            color: "var(--text-muted)",
            fontSize: 13,
            fontStyle: "italic",
            lineHeight: 1.65,
          }}
        >
          {/Exception|→ ?跳/.test(current.lead.text) && (
            <span
              aria-hidden
              style={{
                fontFamily: "var(--font-mono)",
                color: "var(--text-subtle)",
                fontStyle: "normal",
                marginRight: 6,
              }}
            >
              ↪
            </span>
          )}
          {current.lead.text}
        </p>
      )}

      {current.branches && visibleBranch && (
        <>
          {/* Branch label as a heading -- sidebar provides the switcher,
              page just shows which branch is currently selected. */}
          <h3
            className="mt-6"
            style={{
              fontSize: 14,
              fontWeight: 500,
              color: "var(--accent)",
            }}
          >
            {visibleBranch.label}
          </h3>
          {visibleBranch.lead && (
            <p
              className="mt-1.5"
              style={{
                color: "var(--text-muted)",
                fontSize: 13,
                fontStyle: "italic",
              }}
            >
              {visibleBranch.lead}
            </p>
          )}

          <div className="mt-2">
            {visibleBranch.steps.map((s) => (
              <StepRow key={s.num} step={s} onChipClick={setOpenSkill} />
            ))}
          </div>
        </>
      )}

      {current.steps && (
        <div className="mt-2">
          {current.steps.map((s) => (
            <StepRow key={s.num} step={s} onChipClick={setOpenSkill} />
          ))}
        </div>
      )}

      {current.maintenance && (
        <div className="mt-4">
          <MaintenanceList
            rows={current.maintenance}
            onChipClick={setOpenSkill}
          />
        </div>
      )}

      <SkillModal skillKey={openSkill} onClose={() => setOpenSkill(null)} />
    </>
  );
}
