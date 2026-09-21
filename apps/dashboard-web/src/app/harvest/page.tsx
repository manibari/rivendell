"use client";

import { useEffect, useState } from "react";
import {
  apiFetch,
  apiPost,
  type HarvestData,
  type HarvestCandidate,
} from "@/lib/api";
import MetricsRow from "@/components/MetricsRow";
import {
  Check,
  X,
  RotateCcw,
  ChevronDown,
  ChevronRight,
  Zap,
  TrendingUp,
  AlertTriangle,
} from "lucide-react";

// Strength → semantic status. We don't introduce new colors; we re-map to
// existing status tokens (ok/warn/idle).
const strengthConfig: Record<
  HarvestCandidate["strength"],
  { label: string; icon: typeof Zap; color: string }
> = {
  strong: { label: "Strong", icon: Zap, color: "var(--status-ok)" },
  moderate: {
    label: "Moderate",
    icon: TrendingUp,
    color: "var(--status-warn)",
  },
  weak: {
    label: "Weak",
    icon: AlertTriangle,
    color: "var(--text-subtle)",
  },
};

function StrengthBadge({
  strength,
}: {
  strength: HarvestCandidate["strength"];
}) {
  const cfg = strengthConfig[strength];
  const Icon = cfg.icon;
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium font-mono"
      style={{
        borderRadius: 99,
        background: "var(--surface-2)",
        color: cfg.color,
        border: `1px solid ${cfg.color}`,
      }}
    >
      <Icon size={12} />
      {cfg.label}
    </span>
  );
}

function DecisionBadge({ decision }: { decision: string }) {
  if (decision === "accepted")
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium font-mono"
        style={{
          borderRadius: 99,
          background: "var(--accent-bg)",
          color: "var(--accent)",
        }}
      >
        <Check size={12} /> Accepted
      </span>
    );
  if (decision === "dismissed")
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium font-mono line-through"
        style={{
          borderRadius: 99,
          background: "var(--surface-2)",
          color: "var(--text-subtle)",
        }}
      >
        <X size={12} /> Dismissed
      </span>
    );
  return null;
}

function CandidateCard({
  candidate,
  onDecide,
}: {
  candidate: HarvestCandidate;
  onDecide: (key: string, decision: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const isDismissed = candidate.decision === "dismissed";

  return (
    <div
      className="p-4 transition-opacity"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-md)",
        opacity: isDismissed ? 0.5 : 1,
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <code
              className="text-sm"
              style={{
                fontFamily: "var(--font-mono)",
                fontWeight: 600,
                color: "var(--text)",
              }}
            >
              {candidate.name}
            </code>
            <StrengthBadge strength={candidate.strength} />
            <DecisionBadge decision={candidate.decision} />
            {candidate.category && (
              <span
                className="px-1.5 py-0.5 text-[10px] font-mono"
                style={{
                  background: "var(--surface-2)",
                  color: "var(--text-muted)",
                  borderRadius: "var(--radius-sm)",
                }}
              >
                {candidate.category}
              </span>
            )}
          </div>
          {candidate.purpose && (
            <p
              className="mt-1.5 text-sm"
              style={{ color: "var(--text-muted)" }}
            >
              {candidate.purpose}
            </p>
          )}
          <p
            className="mt-1 text-[11px] font-mono tabular-nums"
            style={{ color: "var(--text-subtle)" }}
          >
            {candidate.report_date}
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex shrink-0 gap-1.5">
          {candidate.decision !== "accepted" && (
            <button
              onClick={() => onDecide(candidate.key, "accepted")}
              className="p-1.5 transition-colors"
              style={{
                background: "var(--accent)",
                color: "var(--surface)",
                borderRadius: "var(--radius-sm)",
              }}
              title="Accept — create this skill"
            >
              <Check size={14} />
            </button>
          )}
          {candidate.decision !== "dismissed" && (
            <button
              onClick={() => onDecide(candidate.key, "dismissed")}
              className="p-1.5 transition-colors"
              style={{
                background: "var(--surface-2)",
                color: "var(--text-muted)",
                borderRadius: "var(--radius-sm)",
              }}
              title="Dismiss — not needed"
            >
              <X size={14} />
            </button>
          )}
          {candidate.decision !== "pending" && (
            <button
              onClick={() => onDecide(candidate.key, "pending")}
              className="p-1.5 transition-colors"
              style={{
                background: "transparent",
                border: "1px solid var(--border-strong)",
                color: "var(--text-muted)",
                borderRadius: "var(--radius-sm)",
              }}
              title="Reset to pending"
            >
              <RotateCcw size={14} />
            </button>
          )}
        </div>
      </div>

      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-2 inline-flex items-center gap-1 text-xs"
        style={{ color: "var(--text-muted)" }}
      >
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        詳細分析
      </button>

      {expanded && (
        <div
          className="mt-2 space-y-2 p-3 text-xs"
          style={{
            background: "var(--surface-2)",
            borderRadius: "var(--radius-sm)",
          }}
        >
          {candidate.trigger && (
            <p>
              <strong style={{ color: "var(--text)" }}>觸發：</strong>{" "}
              <span style={{ color: "var(--text-muted)" }}>
                {candidate.trigger}
              </span>
            </p>
          )}
          {candidate.reasoning && (
            <div>
              <strong style={{ color: "var(--text)" }}>理由：</strong>
              <p
                className="mt-0.5 whitespace-pre-line"
                style={{ color: "var(--text-muted)" }}
              >
                {candidate.reasoning}
              </p>
            </div>
          )}
          {candidate.conclusion && (
            <p>
              <strong style={{ color: "var(--text)" }}>結論：</strong>{" "}
              <span style={{ color: "var(--text-muted)" }}>
                {candidate.conclusion}
              </span>
            </p>
          )}
        </div>
      )}
    </div>
  );
}

type FilterTab = "all" | "pending" | "accepted" | "dismissed";

export default function HarvestPage() {
  const [data, setData] = useState<HarvestData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<FilterTab>("pending");

  useEffect(() => {
    apiFetch<HarvestData>("/api/harvest")
      .then(setData)
      .catch((e) => setErr(e.message));
  }, []);

  function reload() {
    apiFetch<HarvestData>("/api/harvest")
      .then(setData)
      .catch((e) => setErr(e.message));
  }

  async function handleDecide(key: string, decision: string) {
    const result = await apiPost<{
      ok: boolean;
      skill_created?: {
        created: boolean;
        already_exists?: boolean;
        skill_path?: string;
        slug?: string;
      };
    }>("/api/harvest/decide", { key, decision });
    if (decision === "accepted" && result.skill_created?.created) {
      const slug = result.skill_created.slug ?? key.split(":")[1];
      toast(`Skill 已建立：${slug}`, "ok");
    } else if (decision === "accepted" && result.skill_created?.already_exists) {
      toast(`Skill 已存在`, "warn");
    }
    reload();
  }

  function toast(msg: string, kind: "ok" | "warn" = "ok") {
    const el = document.createElement("div");
    el.style.cssText = `
      position: fixed; bottom: 16px; right: 16px; z-index: 50;
      padding: 8px 16px; font-size: 13px; font-family: var(--font-mono);
      border-radius: var(--radius-md);
      background: var(--surface); color: var(--text);
      border: 1px solid ${kind === "ok" ? "var(--status-ok)" : "var(--status-warn)"};
      box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    `;
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3000);
  }

  if (err)
    return <p style={{ color: "var(--status-err)" }}>Error: {err}</p>;
  if (!data)
    return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;

  const filtered =
    tab === "all"
      ? data.candidates
      : data.candidates.filter((c) => c.decision === tab);

  const strong = filtered.filter((c) => c.strength === "strong");
  const moderate = filtered.filter((c) => c.strength === "moderate");
  const weak = filtered.filter((c) => c.strength === "weak");

  const tabs: { key: FilterTab; label: string; count: number }[] = [
    { key: "pending", label: "待決定", count: data.pending_count },
    { key: "accepted", label: "已接受", count: data.accepted_count },
    { key: "dismissed", label: "已忽略", count: data.dismissed_count },
    { key: "all", label: "全部", count: data.total },
  ];

  return (
    <div>
      <h1
        className="mb-2 tracking-tight"
        style={{
          fontSize: 28,
          fontWeight: 500,
          color: "var(--text)",
          letterSpacing: "-0.02em",
        }}
      >
        Skill Harvest
      </h1>
      <p
        className="mb-6 text-sm"
        style={{ color: "var(--text-muted)" }}
      >
        從 session harvest 報告中萃取的 skill 候選。審閱後決定是否建立。
      </p>

      <MetricsRow
        metrics={[
          { label: "候選總數", value: data.total },
          { label: "待決定", value: data.pending_count },
          { label: "已接受", value: data.accepted_count },
          { label: "已忽略", value: data.dismissed_count },
        ]}
      />

      {/* Filter tabs */}
      <div
        className="mt-6 flex gap-1 p-1"
        style={{
          background: "var(--surface-2)",
          borderRadius: "var(--radius-md)",
        }}
      >
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className="flex-1 px-3 py-1.5 text-xs font-medium transition-colors tabular-nums"
            style={{
              background: tab === t.key ? "var(--surface)" : "transparent",
              color: tab === t.key ? "var(--text)" : "var(--text-muted)",
              borderRadius: "var(--radius-sm)",
              boxShadow:
                tab === t.key ? "0 0 0 1px var(--border)" : "none",
              fontFamily: "var(--font-mono)",
            }}
          >
            {t.label} ({t.count})
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <p
          className="mt-8 text-center text-sm"
          style={{ color: "var(--text-muted)" }}
        >
          {tab === "pending" ? "沒有待決定的候選" : "沒有符合的候選"}
        </p>
      ) : (
        <div className="mt-6 space-y-8">
          {[
            { items: strong, label: "Strong", icon: Zap, color: "var(--status-ok)" },
            {
              items: moderate,
              label: "Moderate",
              icon: TrendingUp,
              color: "var(--status-warn)",
            },
            {
              items: weak,
              label: "Weak",
              icon: AlertTriangle,
              color: "var(--text-subtle)",
            },
          ].map(({ items, label, icon: Icon, color }) =>
            items.length > 0 ? (
              <section key={label}>
                <h2
                  className="mb-3 flex items-center gap-2 text-sm"
                  style={{ color: "var(--text)", fontWeight: 500 }}
                >
                  <Icon size={16} style={{ color }} />
                  {label}{" "}
                  <span
                    className="font-mono tabular-nums"
                    style={{ color: "var(--text-muted)" }}
                  >
                    ({items.length})
                  </span>
                </h2>
                <div className="space-y-3">
                  {items.map((c) => (
                    <CandidateCard
                      key={c.key}
                      candidate={c}
                      onDecide={handleDecide}
                    />
                  ))}
                </div>
              </section>
            ) : null
          )}
        </div>
      )}
    </div>
  );
}
