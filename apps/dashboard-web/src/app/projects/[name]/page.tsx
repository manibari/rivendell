"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  apiFetch,
  type ProjectDetailData,
  type AgentInfo,
  type GitCommit,
  type GitLogData,
} from "@/lib/api";
import {
  ArrowLeft,
  FolderOpen,
  Clock,
  Activity,
  ChevronRight,
  GitBranch,
  GitCommit as GitCommitIcon,
} from "lucide-react";
import StatusDot from "@/components/StatusDot";

const cardStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
};

function AgentDot({ agent }: { agent: AgentInfo }) {
  if (agent.pid) return <StatusDot status="ok" />;
  if (agent.exit_code !== null && agent.exit_code !== 0)
    return <StatusDot status="err" />;
  if (agent.loaded) return <StatusDot status="ok" />;
  return <StatusDot status="idle" />;
}

function AgentRow({ agent }: { agent: AgentInfo }) {
  return (
    <Link
      href={`/agents/${encodeURIComponent(agent.label)}`}
      className="flex items-center gap-4 p-4 transition-colors"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-md)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "var(--accent-soft)";
        e.currentTarget.style.background = "var(--accent-bg)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--border)";
        e.currentTarget.style.background = "var(--surface)";
      }}
    >
      <AgentDot agent={agent} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span
            className="font-medium font-mono"
            style={{ color: "var(--text)" }}
          >
            {agent.name}
          </span>
          {agent.role_badge && (
            <span
              className="px-2 py-0.5 text-[10px] font-mono"
              style={{
                borderRadius: 99,
                background: "var(--surface-2)",
                color: "var(--text-muted)",
              }}
            >
              {agent.role_badge}
            </span>
          )}
        </div>
        {agent.description && (
          <p
            className="mt-0.5 text-xs truncate"
            style={{ color: "var(--text-muted)" }}
          >
            {agent.description}
          </p>
        )}
      </div>
      <div
        className="hidden sm:flex items-center gap-1.5 text-xs font-mono"
        style={{ color: "var(--text-muted)" }}
      >
        <Clock size={12} />
        <span>{agent.schedule_display || "—"}</span>
      </div>
      <div className="text-xs font-mono tabular-nums">
        {agent.exit_code === null || agent.exit_code === undefined ? (
          <span style={{ color: "var(--text-subtle)" }}>—</span>
        ) : agent.exit_code === 0 ? (
          <span style={{ color: "var(--status-ok)" }}>✓</span>
        ) : (
          <span style={{ color: "var(--status-err)" }}>
            Exit {agent.exit_code}
          </span>
        )}
      </div>
      {agent.current_activity && (
        <div
          className="hidden md:flex items-center gap-1.5 max-w-48 text-xs truncate"
          style={{ color: "var(--accent)" }}
        >
          <Activity size={12} />
          <span>{agent.current_activity.label}</span>
          {agent.current_activity.detail && (
            <span
              className="truncate"
              style={{ color: "var(--text-subtle)" }}
            >
              {agent.current_activity.detail}
            </span>
          )}
        </div>
      )}
      <ChevronRight
        size={16}
        style={{ color: "var(--text-subtle)" }}
      />
    </Link>
  );
}

function GitStatusSection({ git }: { git: ProjectDetailData["git"] }) {
  if (!git || !git.is_git) return null;

  const syncColor =
    git.behind > 0
      ? "var(--status-err)"
      : git.ahead > 0
        ? "var(--status-warn)"
        : "var(--status-ok)";
  const syncLabel =
    git.behind > 0
      ? `↓${git.behind} behind origin`
      : git.ahead > 0
        ? `↑${git.ahead} unpushed`
        : "synced with origin";

  return (
    <div
      className="mt-4 p-4"
      style={{
        background: "var(--surface-2)",
        borderRadius: "var(--radius-sm)",
      }}
    >
      <div className="flex items-center gap-2 text-sm">
        <GitBranch
          size={14}
          style={{ color: "var(--text-muted)" }}
        />
        <span
          className="font-mono font-medium"
          style={{ color: "var(--text)" }}
        >
          {git.branch}
        </span>
        <span
          className="text-xs font-mono font-medium tabular-nums"
          style={{ color: syncColor }}
        >
          {syncLabel}
        </span>
      </div>
      {git.last_commit_msg && (
        <p
          className="mt-1.5 text-xs"
          style={{ color: "var(--text-muted)" }}
        >
          {git.last_commit_ago} — {git.last_commit_msg}
        </p>
      )}
      {git.recent_files.length > 0 && (
        <p
          className="mt-1 font-mono text-xs"
          style={{ color: "var(--text-subtle)" }}
        >
          最近修改：{git.recent_files.join(", ")}
        </p>
      )}
    </div>
  );
}

function MissionSection({
  mission,
}: {
  mission: ProjectDetailData["mission"];
}) {
  if (!mission) return null;
  const hasContent =
    mission.goal ||
    mission.commercial_value ||
    mission.situation_analysis ||
    mission.expected_revenue ||
    mission.potential_clients.length ||
    mission.blockers.length ||
    mission.next_steps.length ||
    mission.resources_needed ||
    mission.deadline;
  if (!hasContent) return null;

  const row = (label: string, value: string | string[]) => {
    if (!value || (Array.isArray(value) && value.length === 0))
      return null;
    const text = Array.isArray(value) ? value.join("、") : value;
    return (
      <div key={label} className="flex gap-2 text-sm">
        <span
          className="w-24 shrink-0 text-right text-xs font-mono"
          style={{ color: "var(--text-subtle)" }}
        >
          {label}
        </span>
        <span style={{ color: "var(--text)" }}>{text}</span>
      </div>
    );
  };

  return (
    <div className="mt-6">
      <h2
        className="mb-3"
        style={{
          fontSize: 18,
          fontWeight: 500,
          color: "var(--text)",
          letterSpacing: "-0.01em",
        }}
      >
        使命
      </h2>
      <div
        className="p-4"
        style={{
          background: "var(--accent-bg)",
          border: "1px solid var(--accent-soft)",
          borderRadius: "var(--radius-md)",
        }}
      >
        <div className="space-y-2">
          {row("目標", mission.goal)}
          {row("期限", mission.deadline)}
          {row("預期收益", mission.expected_revenue)}
          {row("潛在客戶", mission.potential_clients)}
          {row("商業價值", mission.commercial_value)}
          {row("局勢", mission.situation_analysis)}
          {row("阻礙", mission.blockers)}
          {row("下一步", mission.next_steps)}
          {row("所需資源", mission.resources_needed)}
        </div>
      </div>
    </div>
  );
}

function CommitRow({ commit }: { commit: GitCommit }) {
  return (
    <div
      className="flex items-start gap-3 py-2 last:border-0"
      style={{ borderBottom: "1px solid var(--border)" }}
    >
      <GitCommitIcon
        size={13}
        className="mt-0.5 shrink-0"
        style={{ color: "var(--text-muted)" }}
      />
      <div className="min-w-0 flex-1">
        <p
          className="truncate text-sm"
          style={{ color: "var(--text)" }}
        >
          {commit.message}
        </p>
        <p
          className="text-xs font-mono"
          style={{ color: "var(--text-subtle)" }}
        >
          {commit.author} · {commit.ago}
        </p>
      </div>
      <span
        className="shrink-0 font-mono text-xs tabular-nums"
        style={{ color: "var(--text-muted)" }}
      >
        {commit.hash}
      </span>
    </div>
  );
}

export default function ProjectDetailPage() {
  const params = useParams();
  const name = decodeURIComponent(params.name as string);
  const [data, setData] = useState<ProjectDetailData | null>(null);
  const [commits, setCommits] = useState<GitCommit[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    apiFetch<ProjectDetailData>(
      `/api/projects/${encodeURIComponent(name)}`
    )
      .then(setData)
      .catch((e) =>
        setError(e instanceof Error ? e.message : String(e))
      );
    apiFetch<GitLogData>(
      `/api/projects/${encodeURIComponent(name)}/git-log`
    )
      .then((d) => setCommits(d.commits))
      .catch(() => setCommits([]));
  }, [name]);

  useEffect(() => {
    apiFetch<ProjectDetailData>(
      `/api/projects/${encodeURIComponent(name)}`
    )
      .then(setData)
      .catch((e) =>
        setError(e instanceof Error ? e.message : String(e))
      );
    apiFetch<GitLogData>(
      `/api/projects/${encodeURIComponent(name)}/git-log`
    )
      .then((d) => setCommits(d.commits))
      .catch(() => setCommits([]));
  }, [name]);

  useEffect(() => {
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  if (error)
    return (
      <p style={{ color: "var(--status-err)" }}>Error: {error}</p>
    );
  if (!data)
    return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;

  const agents = data.agent_details || [];
  const running = agents.filter((a) => a.pid);
  const healthy = agents.filter(
    (a) => a.loaded && (a.exit_code === 0 || a.exit_code === null)
  );
  const failing = agents.filter(
    (a) => a.exit_code !== null && a.exit_code !== 0
  );

  return (
    <div className="mx-auto max-w-4xl">
      <Link
        href="/projects"
        className="mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        style={{ color: "var(--text-muted)" }}
        onMouseEnter={(e) =>
          (e.currentTarget.style.color = "var(--text)")
        }
        onMouseLeave={(e) =>
          (e.currentTarget.style.color = "var(--text-muted)")
        }
      >
        <ArrowLeft size={16} /> 返回專案列表
      </Link>

      {/* Header */}
      <div className="p-6" style={cardStyle}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <FolderOpen
              size={24}
              style={{ color: "var(--accent)" }}
            />
            <div>
              <h1
                className="tracking-tight"
                style={{
                  fontSize: 24,
                  fontWeight: 500,
                  color: "var(--text)",
                  letterSpacing: "-0.02em",
                  fontFamily: "var(--font-mono)",
                }}
              >
                {data.name}
              </h1>
              {data.description && (
                <p
                  className="mt-0.5 text-sm"
                  style={{ color: "var(--text-muted)" }}
                >
                  {data.description}
                </p>
              )}
              <p
                className="mt-1 font-mono text-xs"
                style={{ color: "var(--text-subtle)" }}
              >
                {data.repo}
              </p>
            </div>
          </div>
          {data.name === "rivendell" && (
            <Link
              href={`/projects/${encodeURIComponent(data.name)}/workflow`}
              className="shrink-0 inline-flex items-center gap-2 px-3 py-2 text-sm transition-colors"
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border-strong)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text)",
                fontFamily: "var(--font-sans)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--accent)";
                e.currentTarget.style.color = "var(--accent)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border-strong)";
                e.currentTarget.style.color = "var(--text)";
              }}
            >
              Workflow Map
              <ChevronRight size={14} />
            </Link>
          )}
        </div>

        <div className="mt-4 flex gap-6 text-sm">
          {[
            {
              label: "Agents",
              value: agents.length,
              color: "var(--text)",
            },
            {
              label: "Running",
              value: running.length,
              color: "var(--accent)",
            },
            {
              label: "Healthy",
              value: healthy.length,
              color: "var(--status-ok)",
            },
            ...(failing.length > 0
              ? [
                  {
                    label: "Failing",
                    value: failing.length,
                    color: "var(--status-err)",
                  },
                ]
              : []),
            ...(data.total_cost_usd > 0
              ? [
                  {
                    label: "Cost",
                    value: `$${data.total_cost_usd.toFixed(2)}`,
                    color: "var(--text)",
                  },
                ]
              : []),
          ].map((m) => (
            <div key={m.label}>
              <span
                className="font-mono text-[10px] uppercase"
                style={{
                  color: "var(--text-subtle)",
                  letterSpacing: "0.1em",
                }}
              >
                {m.label}
              </span>
              <p
                className="font-mono tabular-nums"
                style={{ color: m.color, fontWeight: 500, fontSize: 16 }}
              >
                {m.value}
              </p>
            </div>
          ))}
        </div>

        <GitStatusSection git={data.git} />
      </div>

      <MissionSection mission={data.mission} />

      {/* Agents */}
      <div className="mt-6 space-y-2">
        <h2
          className="mb-3"
          style={{
            fontSize: 18,
            fontWeight: 500,
            color: "var(--text)",
            letterSpacing: "-0.01em",
          }}
        >
          Agents
        </h2>
        {agents.length > 0 ? (
          agents.map((agent) => (
            <AgentRow key={agent.label} agent={agent} />
          ))
        ) : (
          <p
            className="text-sm"
            style={{ color: "var(--text-muted)" }}
          >
            此專案尚無 agent。
          </p>
        )}
      </div>

      {/* Recent commits */}
      {commits.length > 0 && (
        <div className="mt-6">
          <h2
            className="mb-3"
            style={{
              fontSize: 18,
              fontWeight: 500,
              color: "var(--text)",
              letterSpacing: "-0.01em",
            }}
          >
            最近 Commits
          </h2>
          <div className="px-4" style={cardStyle}>
            {commits.map((c) => (
              <CommitRow key={c.hash} commit={c} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
