"use client";

import { useEffect, useState } from "react";
import { apiFetch, type OverviewData, type AgentInfo } from "@/lib/api";
import MetricsRow from "@/components/MetricsRow";
import PendingIssues from "@/components/PendingIssues";
import StatusDot from "@/components/StatusDot";
import DiskCapacity from "@/components/DiskCapacity";
import SsotDriftCard from "@/components/SsotDriftCard";
import ScheduleHealthCard from "@/components/ScheduleHealthCard";
import RecentErrorsCard from "@/components/RecentErrorsCard";
import CostAnomalyCard from "@/components/CostAnomalyCard";
import GitHealthCard from "@/components/GitHealthCard";

function AgentStatusRow({ agent }: { agent: AgentInfo }) {
  let dot: "ok" | "warn" | "err" | "idle";
  let label: string;
  if (!agent.installed) {
    dot = "idle";
    label = "未安裝";
  } else if (agent.exit_code !== null && agent.exit_code !== 0) {
    dot = "err";
    label = `exit=${agent.exit_code}`;
  } else if (agent.loaded) {
    dot = "ok";
    label = "已載入";
  } else {
    dot = "err";
    label = "未載入";
  }

  return (
    <tr style={{ borderBottom: "1px solid var(--border)" }}>
      <td className="py-2 pr-4 font-medium">
        {agent.project}/{agent.name}
      </td>
      <td className="py-2 pr-4">
        <StatusDot status={dot} label={label} />
      </td>
      <td
        className="py-2 pr-4 text-sm"
        style={{ color: "var(--text-muted)" }}
      >
        排程 {agent.schedule_display}
      </td>
      <td className="py-2 text-sm" style={{ color: "var(--text-muted)" }}>
        {agent.role_badge}
      </td>
    </tr>
  );
}

export default function OverviewPage() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<OverviewData>("/api/overview")
      .then(setData)
      .catch((e) => setErr(e.message));
  }, []);

  if (err)
    return (
      <p style={{ color: "var(--status-err)" }}>Error: {err}</p>
    );
  if (!data)
    // Skeleton instead of a bare 載入中 line — the overview aggregate takes a
    // few seconds cold (QA ISSUE-001) and a blank page reads as "broken".
    // Static placeholders (no pulse animation) per DESIGN.md minimal motion.
    return (
      <div aria-busy="true" aria-label="載入中">
        <div
          className="mb-6"
          style={{
            width: 160,
            height: 28,
            background: "var(--surface-2)",
            borderRadius: "var(--radius-sm)",
          }}
        />
        <div className="grid grid-cols-4 gap-4 mb-8">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              style={{
                height: 88,
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-md)",
              }}
            >
              <div
                className="m-4"
                style={{
                  width: "60%",
                  height: 12,
                  background: "var(--surface-2)",
                  borderRadius: "var(--radius-sm)",
                }}
              />
              <div
                className="mx-4"
                style={{
                  width: "40%",
                  height: 22,
                  background: "var(--surface-2)",
                  borderRadius: "var(--radius-sm)",
                }}
              />
            </div>
          ))}
        </div>
        {[0, 1].map((i) => (
          <div
            key={i}
            className="mb-6"
            style={{
              height: 180,
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
            }}
          />
        ))}
        <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
          載入中…（首次聚合約需數秒）
        </p>
      </div>
    );

  const { metrics, agents, hooks, projects_summary } = data;

  return (
    <div>
      <h1
        className="mb-6 tracking-tight"
        style={{
          fontSize: 28,
          fontWeight: 500,
          color: "var(--text)",
          letterSpacing: "-0.02em",
        }}
      >
        總覽
      </h1>

      <MetricsRow
        metrics={[
          { label: "Skill 總數", value: metrics.total_skills },
          { label: "執行中 Agent", value: metrics.running_agents },
          { label: "啟用 Hook", value: metrics.enabled_hooks },
          {
            label: "估算總花費",
            value: `$${metrics.total_cost_usd.toFixed(2)}`,
          },
          { label: "專案數", value: metrics.total_projects },
        ]}
      />

      {/* System health */}
      <section className="mt-8">
        <h2
          className="mb-3"
          style={{
            fontSize: 18,
            fontWeight: 500,
            color: "var(--text)",
            letterSpacing: "-0.01em",
          }}
        >
          系統健康
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <DiskCapacity />
          <SsotDriftCard />
          <ScheduleHealthCard />
          <RecentErrorsCard />
          <CostAnomalyCard />
          <GitHealthCard />
        </div>
      </section>

      {/* Projects status table */}
      {projects_summary && projects_summary.length > 0 && (
        <section className="mt-8">
          <h2
            className="mb-3"
            style={{
              fontSize: 18,
              fontWeight: 500,
              color: "var(--text)",
              letterSpacing: "-0.01em",
            }}
          >
            專案狀態
          </h2>
          <div
            className="overflow-x-auto"
            style={{
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
            }}
          >
            <table className="w-full text-sm">
              <thead>
                <tr
                  style={{
                    background: "var(--surface-2)",
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <th
                    className="py-2 px-4 text-left font-mono text-[10px] uppercase"
                    style={{
                      color: "var(--text-subtle)",
                      letterSpacing: "0.08em",
                    }}
                  >
                    專案
                  </th>
                  <th
                    className="py-2 px-4 text-left font-mono text-[10px] uppercase"
                    style={{
                      color: "var(--text-subtle)",
                      letterSpacing: "0.08em",
                    }}
                  >
                    Agent 數
                  </th>
                  <th
                    className="py-2 px-4 text-left font-mono text-[10px] uppercase"
                    style={{
                      color: "var(--text-subtle)",
                      letterSpacing: "0.08em",
                    }}
                  >
                    執行中
                  </th>
                  <th
                    className="py-2 px-4 text-left font-mono text-[10px] uppercase"
                    style={{
                      color: "var(--text-subtle)",
                      letterSpacing: "0.08em",
                    }}
                  >
                    描述
                  </th>
                </tr>
              </thead>
              <tbody>
                {projects_summary.map((p) => (
                  <tr
                    key={p.name}
                    style={{ borderBottom: "1px solid var(--border)" }}
                  >
                    <td className="py-2 px-4 font-medium">{p.name}</td>
                    <td className="py-2 px-4 tabular-nums">{p.agent_count}</td>
                    <td className="py-2 px-4">
                      <span
                        className="inline-flex items-center px-2 py-0.5 text-xs"
                        style={{
                          borderRadius: 99,
                          background:
                            p.agent_count_loaded > 0
                              ? "var(--accent-bg)"
                              : "var(--surface-2)",
                          color:
                            p.agent_count_loaded > 0
                              ? "var(--accent)"
                              : "var(--text-muted)",
                          fontFamily: "var(--font-mono)",
                          fontSize: 11,
                        }}
                      >
                        {p.agent_count_loaded} running
                      </span>
                    </td>
                    <td
                      className="py-2 px-4"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {p.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Agent status table */}
      <section className="mt-8">
        <h2
          className="mb-3"
          style={{
            fontSize: 18,
            fontWeight: 500,
            color: "var(--text)",
            letterSpacing: "-0.01em",
          }}
        >
          Agent 狀態
        </h2>
        {agents.length > 0 ? (
          <div
            className="overflow-x-auto"
            style={{
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
            }}
          >
            <table className="w-full text-sm">
              <tbody>
                {agents.map((a) => (
                  <AgentStatusRow key={a.label} agent={a} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p
            className="text-sm"
            style={{ color: "var(--text-muted)" }}
          >
            未找到 sk agent
          </p>
        )}
      </section>

      {/* Hook status table */}
      <section className="mt-8">
        <h2
          className="mb-3"
          style={{
            fontSize: 18,
            fontWeight: 500,
            color: "var(--text)",
            letterSpacing: "-0.01em",
          }}
        >
          Hook 狀態
        </h2>
        {hooks.length > 0 ? (
          <div
            className="overflow-x-auto"
            style={{
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
            }}
          >
            <table className="w-full text-sm">
              <tbody>
                {hooks.map((h, i) => (
                  <tr
                    key={i}
                    style={{ borderBottom: "1px solid var(--border)" }}
                  >
                    <td className="py-2 pr-4 font-medium">{h.event}</td>
                    <td
                      className="py-2 pr-4"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {h.matcher || "（全部）"}
                    </td>
                    <td className="py-2">
                      <code
                        className="rounded px-1.5 py-0.5 text-xs"
                        style={{
                          background: "var(--surface-2)",
                          color: "var(--text)",
                          fontFamily: "var(--font-mono)",
                        }}
                      >
                        {h.command}
                      </code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p
            className="text-sm"
            style={{ color: "var(--text-muted)" }}
          >
            未設定 hook（~/.claude/settings.json）
          </p>
        )}
      </section>

      <PendingIssues />
    </div>
  );
}
