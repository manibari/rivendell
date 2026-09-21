"use client";

import { useEffect, useState } from "react";
import { apiFetch, type IssuesData, type IssueItem } from "@/lib/api";
import {
  AlertTriangle,
  XCircle,
  Bot,
  FileText,
  Sparkles,
  FileKey,
} from "lucide-react";

const sourceIcon: Record<string, typeof Bot> = {
  agent: Bot,
  learnings: FileText,
  skill: Sparkles,
  env: FileKey,
};

const sourceLabel: Record<string, string> = {
  agent: "Agent",
  learnings: "Learnings",
  skill: "Skill",
  env: "Env",
};

function IssueBadge({ severity }: { severity: string }) {
  const isError = severity === "error";
  const Icon = isError ? XCircle : AlertTriangle;
  const color = isError ? "var(--status-err)" : "var(--status-warn)";

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium font-mono"
      style={{
        borderRadius: 99,
        background: "var(--surface-2)",
        color,
        border: `1px solid ${color}`,
      }}
    >
      <Icon size={12} />
      {isError ? "Error" : "Warning"}
    </span>
  );
}

function IssueRow({ issue }: { issue: IssueItem }) {
  const Icon = sourceIcon[issue.source] || FileText;
  return (
    <tr style={{ borderBottom: "1px solid var(--border)" }}>
      <td className="py-2.5 px-4">
        <IssueBadge severity={issue.severity} />
      </td>
      <td className="py-2.5 px-4">
        <span
          className="inline-flex items-center gap-1.5 text-xs"
          style={{ color: "var(--text-muted)" }}
        >
          <Icon size={13} />
          {sourceLabel[issue.source] || issue.source}
        </span>
      </td>
      <td
        className="py-2.5 px-4 font-medium text-sm"
        style={{ color: "var(--text)" }}
      >
        {issue.title}
      </td>
      <td
        className="py-2.5 px-4 text-xs"
        style={{ color: "var(--text-muted)" }}
      >
        {issue.detail}
      </td>
    </tr>
  );
}

export default function PendingIssues() {
  const [data, setData] = useState<IssuesData | null>(null);

  useEffect(() => {
    apiFetch<IssuesData>("/api/issues")
      .then(setData)
      .catch(() => {});
  }, []);

  if (!data || data.total === 0) return null;

  return (
    <section className="mt-8">
      <div className="flex items-center gap-3 mb-3">
        <h2
          style={{
            fontSize: 18,
            fontWeight: 500,
            color: "var(--text)",
            letterSpacing: "-0.01em",
          }}
        >
          Pending Issues
        </h2>
        <div className="flex gap-2">
          {data.errors > 0 && (
            <span
              className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium font-mono tabular-nums"
              style={{
                borderRadius: 99,
                background: "var(--surface-2)",
                color: "var(--status-err)",
                border: "1px solid var(--status-err)",
              }}
            >
              <XCircle size={12} />
              {data.errors}
            </span>
          )}
          {data.warnings > 0 && (
            <span
              className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium font-mono tabular-nums"
              style={{
                borderRadius: 99,
                background: "var(--surface-2)",
                color: "var(--status-warn)",
                border: "1px solid var(--status-warn)",
              }}
            >
              <AlertTriangle size={12} />
              {data.warnings}
            </span>
          )}
        </div>
      </div>
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
                className="py-2 px-4 text-left font-mono text-[10px] uppercase w-24"
                style={{
                  color: "var(--text-subtle)",
                  letterSpacing: "0.08em",
                }}
              >
                嚴重度
              </th>
              <th
                className="py-2 px-4 text-left font-mono text-[10px] uppercase w-24"
                style={{
                  color: "var(--text-subtle)",
                  letterSpacing: "0.08em",
                }}
              >
                來源
              </th>
              <th
                className="py-2 px-4 text-left font-mono text-[10px] uppercase"
                style={{
                  color: "var(--text-subtle)",
                  letterSpacing: "0.08em",
                }}
              >
                問題
              </th>
              <th
                className="py-2 px-4 text-left font-mono text-[10px] uppercase"
                style={{
                  color: "var(--text-subtle)",
                  letterSpacing: "0.08em",
                }}
              >
                詳情
              </th>
            </tr>
          </thead>
          <tbody>
            {data.issues.map((issue, i) => (
              <IssueRow
                key={`${issue.source}-${issue.label}-${i}`}
                issue={issue}
              />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
