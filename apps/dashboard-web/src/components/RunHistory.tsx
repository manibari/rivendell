"use client";

import { Fragment, useState, useEffect } from "react";
import {
  apiFetch,
  type AgentRun,
  type AgentFile,
  type AgentFileContent,
  type TimelineEvent,
} from "@/lib/api";
import {
  ChevronDown,
  ChevronRight,
  FileText,
  X,
  Wrench,
  MessageSquare,
  Brain,
  BarChart3,
  GitCommit,
  Rocket,
  XCircle,
  Ban,
  AlertCircle,
} from "lucide-react";

const ICON_FOR_EVENT: Record<string, typeof Wrench> = {
  tool: Wrench,
  text: MessageSquare,
  thinking: Brain,
  result: BarChart3,
  auto_commit: GitCommit,
  auto_push: Rocket,
  qa_gate_failed: XCircle,
  path_filter_rejected: Ban,
  log: FileText,
  log_error: XCircle,
  log_warn: AlertCircle,
  log_header: FileText,
};

function eventIcon(type: string) {
  const Icon = ICON_FOR_EVENT[type];
  if (!Icon) {
    return <span style={{ color: "var(--text-subtle)" }}>•</span>;
  }
  let color = "var(--text-muted)";
  if (type === "log_error" || type === "qa_gate_failed") {
    color = "var(--status-err)";
  } else if (
    type === "log_warn" ||
    type === "auto_commit" ||
    type === "auto_push"
  ) {
    color = "var(--status-warn)";
  } else if (type === "result") {
    color = "var(--status-ok)";
  } else if (type === "tool") {
    color = "var(--accent)";
  }
  return <Icon size={12} style={{ color }} />;
}

function InlineTimeline({
  label,
  startedAt,
}: {
  label: string;
  startedAt: string;
}) {
  const [events, setEvents] = useState<TimelineEvent[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  useEffect(() => {
    apiFetch<TimelineEvent[]>(
      `/api/agents/${encodeURIComponent(label)}/timeline?started_at=${encodeURIComponent(startedAt)}`
    )
      .then(setEvents)
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, [label, startedAt]);

  if (loading)
    return (
      <p
        className="py-2 text-xs"
        style={{ color: "var(--text-subtle)" }}
      >
        載入時間線...
      </p>
    );
  if (!events || events.length === 0)
    return (
      <p
        className="py-2 text-xs"
        style={{ color: "var(--text-muted)" }}
      >
        無時間線資料（下次執行將自動記錄 tool calls）
      </p>
    );

  return (
    <div className="relative space-y-0 py-2">
      <div
        className="absolute left-3 top-4 bottom-4 w-px"
        style={{ background: "var(--border)" }}
      />
      {events.map((ev, i) => {
        const time = ev.ts ? ev.ts.split("T")[1]?.slice(0, 8) || ev.ts : "";
        const isExpanded = expandedIdx === i;

        return (
          <div
            key={i}
            className="relative flex items-start gap-2 py-1 pl-0.5"
          >
            <div
              className="z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full"
              style={{ background: "var(--surface)" }}
            >
              {eventIcon(ev.type)}
            </div>
            <div className="min-w-0 flex-1">
              <button
                onClick={() => setExpandedIdx(isExpanded ? null : i)}
                className="flex w-full items-start gap-2 text-left text-xs"
              >
                <span
                  className="shrink-0 font-mono text-[10px] tabular-nums"
                  style={{ color: "var(--text-subtle)" }}
                >
                  {time}
                </span>
                <span className="min-w-0 flex-1">
                  {ev.type === "tool" && (
                    <code
                      className="px-1 py-0.5 text-[11px] font-medium font-mono"
                      style={{
                        background: "var(--accent-bg)",
                        color: "var(--accent)",
                        borderRadius: 2,
                      }}
                    >
                      {ev.name}
                    </code>
                  )}
                  {ev.type === "text" && (
                    <span style={{ color: "var(--text-muted)" }}>
                      {(ev.text || "").slice(0, 100)}
                      {(ev.len || 0) > 100 ? "..." : ""}
                    </span>
                  )}
                  {ev.type === "thinking" && (
                    <span
                      className="italic"
                      style={{ color: "var(--text-subtle)" }}
                    >
                      thinking ({ev.len} chars)
                    </span>
                  )}
                  {ev.type === "result" && (
                    <span style={{ color: "var(--status-ok)" }}>
                      完成 |{" "}
                      <span className="font-mono tabular-nums">
                        {(ev.input_tokens || 0).toLocaleString()} in /{" "}
                        {(ev.output_tokens || 0).toLocaleString()} out | $
                        {ev.cost_usd?.toFixed(4)}
                      </span>
                    </span>
                  )}
                  {ev.type === "auto_commit" && (
                    <span style={{ color: "var(--status-warn)" }}>
                      Commit: {ev.detail}
                    </span>
                  )}
                  {ev.type === "auto_push" && (
                    <span style={{ color: "var(--status-warn)" }}>
                      Push: {ev.detail}
                    </span>
                  )}
                  {ev.type === "log" && (
                    <span style={{ color: "var(--text-muted)" }}>
                      {ev.text}
                    </span>
                  )}
                  {ev.type === "log_error" && (
                    <span
                      className="font-medium"
                      style={{ color: "var(--status-err)" }}
                    >
                      {ev.text}
                    </span>
                  )}
                  {ev.type === "log_warn" && (
                    <span style={{ color: "var(--status-warn)" }}>
                      {ev.text}
                    </span>
                  )}
                  {ev.type === "log_header" && (
                    <span
                      className="font-semibold"
                      style={{ color: "var(--text)" }}
                    >
                      {ev.text}
                    </span>
                  )}
                </span>
              </button>
              {isExpanded && ev.type === "tool" && ev.input && (
                <pre
                  className="mt-1 max-h-40 overflow-auto p-2 text-[10px] font-mono"
                  style={{
                    background: "var(--surface-2)",
                    color: "var(--text)",
                    borderRadius: 2,
                  }}
                >
                  {JSON.stringify(ev.input, null, 2)}
                </pre>
              )}
              {isExpanded && ev.type === "text" && (
                <pre
                  className="mt-1 max-h-48 overflow-auto p-2 text-[10px] whitespace-pre-wrap font-mono"
                  style={{
                    background: "var(--surface-2)",
                    color: "var(--text)",
                    borderRadius: 2,
                  }}
                >
                  {ev.text}
                </pre>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function RunArtifacts({
  label,
  startedAt,
}: {
  label: string;
  startedAt: string;
}) {
  const [artifacts, setArtifacts] = useState<AgentFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewingFile, setViewingFile] = useState<AgentFileContent | null>(
    null
  );
  const [fileLoading, setFileLoading] = useState(false);

  useEffect(() => {
    apiFetch<AgentFile[]>(
      `/api/agents/${encodeURIComponent(label)}/artifacts?started_at=${encodeURIComponent(startedAt)}`
    )
      .then(setArtifacts)
      .catch(() => setArtifacts([]))
      .finally(() => setLoading(false));
  }, [label, startedAt]);

  async function openFile(path: string) {
    setFileLoading(true);
    try {
      const data = await apiFetch<AgentFileContent>(
        `/api/agents/${encodeURIComponent(label)}/file?path=${encodeURIComponent(path)}`
      );
      setViewingFile(data);
    } catch {
      setViewingFile({
        name: "error",
        content: "Failed to load file",
        size: 0,
      });
    } finally {
      setFileLoading(false);
    }
  }

  if (loading) return null;
  if (artifacts.length === 0) return null;

  return (
    <>
      <div className="flex flex-wrap items-center gap-2 py-2">
        <span
          className="font-mono text-[10px] uppercase"
          style={{
            color: "var(--text-subtle)",
            letterSpacing: "0.1em",
          }}
        >
          成果
        </span>
        {artifacts.map((f) => (
          <button
            key={f.path}
            onClick={(e) => {
              e.stopPropagation();
              openFile(f.path);
            }}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium font-mono transition-colors"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              color: "var(--text)",
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
            <FileText
              size={12}
              style={{ color: "var(--accent)" }}
            />
            {f.name}
            <span
              className="text-[10px] tabular-nums"
              style={{ color: "var(--text-subtle)" }}
            >
              {f.size > 1024
                ? `${(f.size / 1024).toFixed(1)}K`
                : `${f.size}B`}
            </span>
          </button>
        ))}
      </div>

      {/* Full-screen markdown viewer overlay */}
      {(viewingFile || fileLoading) && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.5)" }}
          onClick={() => setViewingFile(null)}
        >
          <div
            className="relative flex max-h-[90vh] w-full max-w-4xl flex-col"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-lg)",
              boxShadow:
                "0 20px 60px rgba(0,0,0,0.15), 0 8px 20px rgba(0,0,0,0.08)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              className="flex items-center justify-between px-6 py-3"
              style={{ borderBottom: "1px solid var(--border)" }}
            >
              <div className="flex items-center gap-2">
                <FileText
                  size={16}
                  style={{ color: "var(--accent)" }}
                />
                <span
                  className="font-mono text-sm"
                  style={{ color: "var(--text)", fontWeight: 500 }}
                >
                  {viewingFile?.name || "Loading..."}
                </span>
                {viewingFile && (
                  <span
                    className="text-xs font-mono tabular-nums"
                    style={{ color: "var(--text-subtle)" }}
                  >
                    ({(viewingFile.size / 1024).toFixed(1)} KB)
                  </span>
                )}
              </div>
              <button
                onClick={() => setViewingFile(null)}
                className="p-1 transition-colors"
                style={{
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-muted)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--surface-2)";
                  e.currentTarget.style.color = "var(--text)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "var(--text-muted)";
                }}
              >
                <X size={18} />
              </button>
            </div>

            <div className="flex-1 overflow-auto">
              {fileLoading ? (
                <p
                  className="p-6 text-sm"
                  style={{ color: "var(--text-muted)" }}
                >
                  載入中...
                </p>
              ) : viewingFile ? (
                <div className="p-6">
                  <MarkdownContent content={viewingFile.content} />
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function MarkdownContent({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;
  let tableRows: string[][] = [];
  let inTable = false;

  function flushTable() {
    if (tableRows.length === 0) return;
    const headerRow = tableRows[0];
    const dataRows = tableRows.slice(2);
    elements.push(
      <div
        key={`table-${elements.length}`}
        className="my-4 overflow-x-auto"
      >
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-strong)" }}>
              {headerRow.map((cell, ci) => (
                <th
                  key={ci}
                  className="px-3 py-1.5 text-left font-mono text-[10px] uppercase"
                  style={{
                    color: "var(--text-subtle)",
                    letterSpacing: "0.08em",
                  }}
                >
                  {cell.trim()}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dataRows.map((row, ri) => (
              <tr
                key={ri}
                style={{ borderBottom: "1px solid var(--border)" }}
              >
                {row.map((cell, ci) => (
                  <td
                    key={ci}
                    className="px-3 py-1.5"
                    style={{ color: "var(--text)" }}
                  >
                    {cell.trim()}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableRows = [];
    inTable = false;
  }

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("|") && line.endsWith("|")) {
      const cells = line.split("|").slice(1, -1);
      if (!inTable) inTable = true;
      tableRows.push(cells);
      i++;
      continue;
    } else if (inTable) {
      flushTable();
    }

    if (line.startsWith("# ")) {
      elements.push(
        <h1
          key={i}
          className="mb-3 mt-6 first:mt-0"
          style={{
            fontSize: 22,
            fontWeight: 500,
            color: "var(--text)",
            letterSpacing: "-0.02em",
          }}
        >
          {line.slice(2)}
        </h1>
      );
    } else if (line.startsWith("## ")) {
      elements.push(
        <h2
          key={i}
          className="mb-2 mt-5"
          style={{
            fontSize: 18,
            fontWeight: 500,
            color: "var(--text)",
            letterSpacing: "-0.01em",
          }}
        >
          {line.slice(3)}
        </h2>
      );
    } else if (line.startsWith("### ")) {
      elements.push(
        <h3
          key={i}
          className="mb-1 mt-4"
          style={{
            fontSize: 15,
            fontWeight: 500,
            color: "var(--text)",
          }}
        >
          {line.slice(4)}
        </h3>
      );
    } else if (line.startsWith("---")) {
      elements.push(
        <hr
          key={i}
          className="my-4"
          style={{ border: "none", borderTop: "1px solid var(--border)" }}
        />
      );
    } else if (line.startsWith("> ")) {
      elements.push(
        <blockquote
          key={i}
          className="my-2 pl-4 text-sm italic"
          style={{
            borderLeft: "4px solid var(--accent-soft)",
            color: "var(--text-muted)",
          }}
        >
          {line.slice(2)}
        </blockquote>
      );
    } else if (line.startsWith("- [") || line.startsWith("  - [")) {
      const indent = line.startsWith("  ") ? "ml-4" : "";
      const checked = line.includes("[x]") || line.includes("[X]");
      const text = line.replace(/^[\s]*- \[.\]\s*/, "");
      elements.push(
        <div
          key={i}
          className={`flex items-start gap-2 py-0.5 text-sm ${indent}`}
        >
          <input
            type="checkbox"
            checked={checked}
            readOnly
            className="mt-0.5"
          />
          <span style={{ color: "var(--text)" }}>{text}</span>
        </div>
      );
    } else if (line.startsWith("- ") || line.startsWith("  - ")) {
      const indent = line.startsWith("  ") ? "ml-4" : "";
      const text = line.replace(/^[\s]*- /, "");
      elements.push(
        <div key={i} className={`py-0.5 text-sm ${indent}`}>
          <span
            className="mr-2"
            style={{ color: "var(--text-subtle)" }}
          >
            •
          </span>
          <span style={{ color: "var(--text)" }}>{text}</span>
        </div>
      );
    } else if (line.trim() === "") {
      elements.push(<div key={i} className="h-2" />);
    } else if (line.startsWith("_") && line.endsWith("_")) {
      elements.push(
        <p
          key={i}
          className="text-xs italic"
          style={{ color: "var(--text-muted)" }}
        >
          {line.slice(1, -1)}
        </p>
      );
    } else {
      elements.push(
        <p
          key={i}
          className="py-0.5 text-sm leading-relaxed"
          style={{ color: "var(--text)" }}
        >
          {line}
        </p>
      );
    }
    i++;
  }
  if (inTable) flushTable();

  return <div>{elements}</div>;
}

export default function RunHistory({
  runs,
  agentLabel,
}: {
  runs: AgentRun[];
  agentLabel?: string;
}) {
  const [expandedRun, setExpandedRun] = useState<number | null>(null);

  if (runs.length === 0) {
    return (
      <p
        className="mt-2 text-xs"
        style={{ color: "var(--text-subtle)" }}
      >
        尚無執行紀錄
      </p>
    );
  }

  return (
    <div className="mt-3 overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr style={{ borderBottom: "1px solid var(--border)" }}>
            {agentLabel && <th className="pb-2 pr-1 w-6" />}
            {["時間", "結果", "花費", "Tokens", "Commit", "Files", "QA", "Branch"].map(
              (h) => (
                <th
                  key={h}
                  className="pb-2 pr-3 text-left font-mono text-[10px] uppercase"
                  style={{
                    color: "var(--text-subtle)",
                    letterSpacing: "0.08em",
                  }}
                >
                  {h}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody>
          {runs.map((run, i) => (
            <Fragment key={i}>
              <tr
                style={{
                  borderBottom: "1px solid var(--border)",
                  cursor: agentLabel ? "pointer" : "default",
                }}
                onClick={() => {
                  if (!agentLabel) return;
                  setExpandedRun(expandedRun === i ? null : i);
                }}
                onMouseEnter={
                  agentLabel
                    ? (e) =>
                        (e.currentTarget.style.background =
                          "var(--surface-2)")
                    : undefined
                }
                onMouseLeave={
                  agentLabel
                    ? (e) =>
                        (e.currentTarget.style.background = "transparent")
                    : undefined
                }
              >
                {agentLabel && (
                  <td
                    className="py-1.5 pr-1"
                    style={{ color: "var(--text-subtle)" }}
                  >
                    {expandedRun === i ? (
                      <ChevronDown size={14} />
                    ) : (
                      <ChevronRight size={14} />
                    )}
                  </td>
                )}
                <td
                  className="py-1.5 pr-3 whitespace-nowrap font-mono tabular-nums"
                  style={{ color: "var(--text)" }}
                >
                  {run.started_at || "—"}
                </td>
                <td className="py-1.5 pr-3">
                  {run.exit_code === 0 ? (
                    <span style={{ color: "var(--status-ok)" }}>✓</span>
                  ) : (
                    <span
                      className="font-mono"
                      style={{ color: "var(--status-err)" }}
                    >
                      ✗ ({run.exit_code})
                    </span>
                  )}
                </td>
                <td
                  className="py-1.5 pr-3 font-mono tabular-nums"
                  style={{ color: "var(--text)" }}
                >
                  {run.cost_usd != null
                    ? `$${run.cost_usd.toFixed(4)}`
                    : "—"}
                </td>
                <td
                  className="py-1.5 pr-3 font-mono tabular-nums"
                  style={{ color: "var(--text)" }}
                >
                  {run.tokens_used?.toLocaleString() || "—"}
                </td>
                <td
                  className="py-1.5 pr-3 font-mono"
                  style={{ color: "var(--text)" }}
                >
                  {run.commit_sha || "—"}
                </td>
                <td
                  className="py-1.5 pr-3 font-mono tabular-nums"
                  style={{ color: "var(--text)" }}
                >
                  {run.files_changed != null ? run.files_changed : "—"}
                </td>
                <td className="py-1.5 pr-3">
                  {run.qa_passed === 1 ? (
                    <span style={{ color: "var(--status-ok)" }}>✓</span>
                  ) : run.qa_passed === 0 ? (
                    <span style={{ color: "var(--status-err)" }}>✗</span>
                  ) : (
                    <span style={{ color: "var(--text-subtle)" }}>—</span>
                  )}
                </td>
                <td
                  className="py-1.5 font-mono"
                  style={{ color: "var(--text)" }}
                >
                  {run.branch_name || "—"}
                </td>
              </tr>
              {expandedRun === i && agentLabel && run.started_at && (
                <tr>
                  <td
                    colSpan={9}
                    className="px-4"
                    style={{ background: "var(--surface-2)" }}
                  >
                    <RunArtifacts
                      label={agentLabel}
                      startedAt={run.started_at}
                    />
                    <InlineTimeline
                      label={agentLabel}
                      startedAt={run.started_at}
                    />
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
