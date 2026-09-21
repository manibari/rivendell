"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch, type AgentsData } from "@/lib/api";
import MetricsRow from "@/components/MetricsRow";
import AgentCard from "@/components/AgentCard";

export default function AgentsPage() {
  const [data, setData] = useState<AgentsData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(() => {
    apiFetch<AgentsData>("/api/agents")
      .then(setData)
      .catch((e) => setErr(e.message));
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [load]);

  if (err)
    return <p style={{ color: "var(--status-err)" }}>Error: {err}</p>;
  if (!data)
    return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;

  const { metrics, agents, by_project } = data;

  const projectNames = Object.keys(by_project).sort();
  const agentsByProject = new Map<string, typeof agents>();
  for (const name of projectNames) {
    agentsByProject.set(
      name,
      agents.filter((a) => a.project === name),
    );
  }
  const grouped = new Set(projectNames);
  const ungrouped = agents.filter((a) => !grouped.has(a.project));

  const projectBadge = (count: number, accent = true) => (
    <span
      className="px-2 py-0.5 text-xs font-mono tabular-nums"
      style={{
        borderRadius: 99,
        background: accent ? "var(--accent-bg)" : "var(--surface-2)",
        color: accent ? "var(--accent)" : "var(--text-muted)",
        fontSize: 11,
      }}
    >
      {count} agent{count > 1 ? "s" : ""}
    </span>
  );

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
        Agent 管理
      </h1>

      <MetricsRow
        metrics={[
          { label: "總 Agent 數", value: metrics.total },
          { label: "執行中", value: metrics.running },
          { label: "上次成功", value: metrics.last_success || "—" },
          { label: "今日花費", value: `$${metrics.today_cost.toFixed(4)}` },
        ]}
      />

      {agents.length === 0 ? (
        <p
          className="mt-6 text-sm"
          style={{ color: "var(--text-muted)" }}
        >
          未找到 sk agent
        </p>
      ) : (
        <div className="mt-6 space-y-6">
          {projectNames.map((projName) => {
            const projAgents = agentsByProject.get(projName) || [];
            if (projAgents.length === 0) return null;
            return (
              <div key={projName}>
                <h2
                  className="mb-3 flex items-center gap-2 text-sm font-medium"
                  style={{ color: "var(--text)" }}
                >
                  {projName}
                  {projectBadge(projAgents.length)}
                </h2>
                <div className="flex flex-col gap-4">
                  {projAgents.map((agent) => (
                    <AgentCard
                      key={agent.label}
                      agent={agent}
                      onRefresh={load}
                    />
                  ))}
                </div>
              </div>
            );
          })}
          {ungrouped.length > 0 && (
            <div>
              <h2
                className="mb-3 flex items-center gap-2 text-sm font-medium"
                style={{ color: "var(--text-muted)" }}
              >
                未分類
                {projectBadge(ungrouped.length, false)}
              </h2>
              <div className="flex flex-col gap-4">
                {ungrouped.map((agent) => (
                  <AgentCard
                    key={agent.label}
                    agent={agent}
                    onRefresh={load}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
