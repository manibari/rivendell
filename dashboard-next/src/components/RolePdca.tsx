"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ExternalLink, FileText } from "lucide-react";
import { apiFetch, type SkillRolesData, type RoleJob, type RoleStage } from "@/lib/api";

// 角色 → 工作 → PDCA. Data comes from docs/skills-by-role.md via /api/skills/roles;
// this component only lays it out: pick a role on the left, each job on the
// right is one card with four columns (Plan / Do / Check / Act). Skill chips
// link to /skills/<name>; a ★ row is a step that has no skill yet.

const STAGE_LABEL: Record<string, string> = {
  Plan: "想清楚",
  Do: "做出來",
  Check: "驗證",
  Act: "收尾 · 下一輪",
};

type ChipKind = "core" | "conditional" | "automatic";

function Chip({ name, external, kind = "core" }: { name: string; external?: boolean; kind?: ChipKind }) {
  const muted = kind !== "core";
  return (
    <Link
      href={`/skills/${encodeURIComponent(name)}`}
      className="inline-block font-mono transition-colors"
      title={`${name}${external ? "（外部 gstack）" : ""}${kind === "conditional" ? " · 視情況" : kind === "automatic" ? " · 自動觸發" : ""}`}
      style={{
        fontSize: 11,
        lineHeight: "16px",
        padding: "1px 6px",
        borderRadius: kind === "automatic" ? 99 : 3,
        border: `1px ${kind === "conditional" || external ? "dashed" : "solid"} ${kind === "core" ? "var(--border-strong)" : "var(--border)"}`,
        background: kind === "automatic" ? "var(--surface-2)" : muted ? "transparent" : "var(--surface)",
        color: muted ? "var(--text-muted)" : "var(--text)",
        fontWeight: kind === "core" ? 500 : 400,
        whiteSpace: "nowrap",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--accent-soft)")}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
    >
      {name}
    </Link>
  );
}

function GapRow({ text }: { text: string }) {
  return (
    <div
      className="flex items-start gap-1.5 text-[11px] leading-snug"
      style={{ color: "var(--status-warn)", background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 3, padding: "3px 6px" }}
    >
      <span aria-hidden style={{ flexShrink: 0 }}>★</span>
      <span>{text}</span>
    </div>
  );
}

function StageCell({ stage }: { stage: RoleStage }) {
  const empty = stage.empty || (stage.skills.length === 0 && stage.gaps.length === 0 && !stage.text);
  return (
    <div className="min-w-0 flex flex-col gap-1.5 p-3" style={{ borderLeft: "1px solid var(--border)" }}>
      <div className="flex items-baseline gap-1.5">
        <span className="font-mono text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-subtle)" }}>
          {stage.stage}
        </span>
        <span className="text-[10px]" style={{ color: "var(--text-subtle)" }}>
          {STAGE_LABEL[stage.stage]}
        </span>
      </div>
      {empty ? (
        <span className="font-mono text-xs" style={{ color: "var(--text-subtle)" }}>
          —
        </span>
      ) : (
        <>
          {stage.core.length > 0 && (
            <div className="flex flex-wrap items-center gap-1">
              {stage.core.map((s, i) => (
                <span key={s} className="inline-flex items-center gap-1">
                  {i > 0 && (
                    <span aria-hidden className="text-[10px]" style={{ color: "var(--text-subtle)" }}>
                      →
                    </span>
                  )}
                  <Chip name={s} external={stage.external.includes(s)} kind="core" />
                </span>
              ))}
            </div>
          )}
          {stage.conditional.length > 0 && (
            <div className="flex flex-wrap items-center gap-1">
              <span className="text-[10px]" style={{ color: "var(--text-subtle)" }}>
                視情況
              </span>
              {stage.conditional.map((s) => (
                <Chip key={s} name={s} external={stage.external.includes(s)} kind="conditional" />
              ))}
            </div>
          )}
          {stage.automatic.length > 0 && (
            <div className="flex flex-wrap items-center gap-1">
              <span className="text-[10px]" style={{ color: "var(--text-subtle)" }}>
                自動
              </span>
              {stage.automatic.map((s) => (
                <Chip key={s} name={s} external={stage.external.includes(s)} kind="automatic" />
              ))}
            </div>
          )}
          {stage.gaps.map((g, i) => (
            <GapRow key={i} text={g} />
          ))}
          {stage.skills.length === 0 && stage.gaps.length === 0 && stage.text && (
            <p className="text-[11px] leading-snug" style={{ color: "var(--text-muted)" }}>
              {stage.text}
            </p>
          )}
          {stage.note && (
            <p className="text-[11px] leading-snug" style={{ color: "var(--text-muted)" }}>
              {stage.note}
            </p>
          )}
        </>
      )}
    </div>
  );
}

function JobCard({ job }: { job: RoleJob }) {
  const deep = job.deep_dive;
  const deepHref = deep ? `/docs/${deep.href.replace(/\.md$/, "")}` : null;
  return (
    <section
      id={`job-${job.id}`}
      style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}
    >
      <header className="flex flex-wrap items-center gap-2 px-3 py-2" style={{ borderBottom: "1px solid var(--border)" }}>
        <span className="font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
          {job.id}
        </span>
        <h3 className="text-sm" style={{ color: "var(--text)", fontWeight: 500 }}>
          {job.title}
        </h3>
        {job.gap_count > 0 && (
          <span
            className="font-mono text-[10px] px-1.5 py-0.5"
            style={{ color: "var(--status-warn)", background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 99 }}
          >
            ★ 缺 {job.gap_count}
          </span>
        )}
        {deepHref && (
          <Link
            href={deepHref}
            className="ml-auto inline-flex items-center gap-1 text-[11px]"
            style={{ color: "var(--accent)" }}
          >
            <FileText size={12} /> 展開 {deep!.label}
          </Link>
        )}
      </header>
      <div className="grid" style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}>
        {job.stages.map((s) => (
          <StageCell key={s.stage} stage={s} />
        ))}
      </div>
    </section>
  );
}

export default function RolePdca({ initialRole }: { initialRole?: string }) {
  const [data, setData] = useState<SkillRolesData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [roleId, setRoleId] = useState<string>(initialRole ?? "1");

  useEffect(() => {
    apiFetch<SkillRolesData>("/api/skills/roles").then(setData).catch((e) => setErr(e.message));
  }, []);

  const role = useMemo(() => data?.roles.find((r) => r.id === roleId) ?? data?.roles[0] ?? null, [data, roleId]);

  if (err) return <p style={{ color: "var(--status-err)" }}>Error: {err}</p>;
  if (!data || !role) return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs" style={{ color: "var(--text-muted)" }}>
        <span className="font-mono">
          {data.totals.roles} 角色 · {data.totals.jobs} 工作 · <span style={{ color: "var(--status-warn)" }}>★ {data.totals.gaps} 缺環</span>
        </span>
        <span className="font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
          source: docs/skills-by-role.md · {data.updated}
        </span>
        <span className="inline-flex items-center gap-1.5 text-[11px]" style={{ color: "var(--text-subtle)" }}>
          <span style={{ border: "1px solid var(--border-strong)", borderRadius: 3, padding: "0 5px", color: "var(--text)", fontWeight: 500 }}>主線</span>
          <span style={{ border: "1px dashed var(--border)", borderRadius: 3, padding: "0 5px" }}>視情況</span>
          <span style={{ background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 99, padding: "0 6px" }}>自動</span>
        </span>
        <Link href="/skills/roles?raw=1" className="inline-flex items-center gap-1 text-[11px]" style={{ color: "var(--text-subtle)" }}>
          <ExternalLink size={11} /> 原文
        </Link>
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: "220px minmax(0, 1fr)" }}>
        {/* Role list */}
        <nav className="flex flex-col gap-0.5 self-start" style={{ position: "sticky", top: 16 }}>
          {data.roles.map((r) => {
            const on = r.id === role.id;
            return (
              <button
                key={r.id}
                type="button"
                onClick={() => setRoleId(r.id)}
                className="flex items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors"
                style={{
                  background: on ? "var(--surface)" : "transparent",
                  color: on ? "var(--text)" : "var(--text-muted)",
                  boxShadow: on ? "0 0 0 1px var(--border)" : "none",
                  fontWeight: on ? 500 : 400,
                }}
              >
                <span className="font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
                  {r.id}
                </span>
                <span className="min-w-0 truncate">{r.title}</span>
                <span className="ml-auto font-mono text-[10px] tabular-nums" style={{ color: "var(--text-subtle)" }}>
                  {r.job_count}
                  {r.gap_count > 0 && <span style={{ color: "var(--status-warn)" }}> ★{r.gap_count}</span>}
                </span>
              </button>
            );
          })}
          {data.shared.length > 0 && (
            <div className="mt-3 px-3 text-[11px] leading-relaxed" style={{ color: "var(--text-subtle)" }}>
              {data.shared.map((s, i) => (
                <p key={i} className="mb-2">
                  {s}
                </p>
              ))}
            </div>
          )}
        </nav>

        {/* Jobs of the selected role */}
        <div className="min-w-0">
          <div className="mb-3">
            <h2 className="text-lg" style={{ color: "var(--text)", fontWeight: 500, letterSpacing: "-0.01em" }}>
              {role.id}. {role.title}
            </h2>
            {role.intro && (
              <p className="mt-1 text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                {role.intro}
              </p>
            )}
            {role.notes.map((n, i) => (
              <p key={i} className="mt-1 text-[11px] leading-relaxed" style={{ color: "var(--text-subtle)" }}>
                {n}
              </p>
            ))}
            <div className="mt-2 flex flex-wrap gap-1.5">
              {role.jobs.map((j) => (
                <a
                  key={j.id}
                  href={`#job-${j.id}`}
                  className="font-mono text-[11px] px-2 py-0.5"
                  style={{ border: "1px solid var(--border)", borderRadius: 99, color: "var(--text-muted)" }}
                >
                  {j.id} {j.title}
                  {j.gap_count > 0 && <span style={{ color: "var(--status-warn)" }}> ★</span>}
                </a>
              ))}
            </div>
          </div>
          <div className="flex flex-col gap-3">
            {role.jobs.map((j) => (
              <JobCard key={j.id} job={j} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
