"use client";

import { useState, useEffect, useRef } from "react";
import type { AgentInfo, AgentRun } from "@/lib/api";
import { apiFetch, apiPost } from "@/lib/api";
import RunHistory from "./RunHistory";
import StatusDot from "./StatusDot";
import Link from "next/link";
import {
  ChevronDown,
  ChevronRight,
  Play,
  Square,
  Download,
  RefreshCw,
  Shield,
  ExternalLink,
  Loader2,
} from "lucide-react";

function StatusBadge({ agent }: { agent: AgentInfo }) {
  if (!agent.installed) {
    return <StatusDot status="idle" label="未安裝" />;
  }
  if (agent.pid !== null) {
    return (
      <span
        className="inline-flex items-center gap-1.5 font-mono text-xs"
        style={{ color: "var(--status-ok)" }}
      >
        <span className="relative flex h-2 w-2">
          <span
            className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-60"
            style={{ background: "var(--status-ok)" }}
          />
          <span
            className="relative inline-flex h-2 w-2 rounded-full"
            style={{ background: "var(--status-ok)" }}
          />
        </span>
        執行中
      </span>
    );
  }
  if (agent.exit_code !== null && agent.exit_code !== 0) {
    return <StatusDot status="err" label={`Exit ${agent.exit_code}`} />;
  }
  if (agent.loaded) {
    return <StatusDot status="ok" label="已載入" />;
  }
  return <StatusDot status="err" label="未載入" />;
}

function ActivityIndicator({
  activity,
}: {
  activity: AgentInfo["current_activity"];
}) {
  if (!activity) return null;
  return (
    <div
      className="mt-2 flex items-center gap-2 px-3 py-2 text-xs"
      style={{
        background: "var(--accent-bg)",
        border: "1px solid var(--accent-soft)",
        borderRadius: "var(--radius-sm)",
      }}
    >
      <Loader2
        size={14}
        className="animate-spin"
        style={{ color: "var(--accent)" }}
      />
      <span style={{ color: "var(--accent)", fontWeight: 500 }}>
        {activity.label}
      </span>
      {activity.detail && (
        <span
          className="min-w-0 truncate font-mono"
          style={{ color: "var(--accent-soft)" }}
        >
          {activity.detail}
        </span>
      )}
    </div>
  );
}

export default function AgentCard({
  agent,
  onRefresh,
}: {
  agent: AgentInfo;
  onRefresh: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [showSafety, setShowSafety] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [runs, setRuns] = useState<AgentRun[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [justStarted, setJustStarted] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (justStarted) {
      pollRef.current = setInterval(() => {
        onRefresh();
      }, 2000);
      const timeout = setTimeout(() => {
        setJustStarted(false);
      }, 60000);
      return () => {
        if (pollRef.current) clearInterval(pollRef.current);
        clearTimeout(timeout);
      };
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [justStarted, onRefresh]);

  useEffect(() => {
    if (justStarted && agent.pid !== null) {
      setJustStarted(false);
      setToast(null);
    }
  }, [justStarted, agent.pid]);

  async function action(
    path: string,
    body: Record<string, unknown>,
    successMsg?: string
  ) {
    setBusy(true);
    setError(null);
    setToast(null);
    try {
      await apiPost(path, body);
      if (successMsg) {
        setToast(successMsg);
        setTimeout(() => setToast(null), 5000);
      }
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleStart() {
    setBusy(true);
    setError(null);
    setToast(null);
    try {
      await apiPost("/api/agents/start", { label: agent.label });
      setToast("已觸發，等待啟動中...");
      setJustStarted(true);
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function loadRuns() {
    if (runs !== null) {
      setShowHistory(!showHistory);
      return;
    }
    try {
      const data = await apiFetch<AgentRun[]>(
        `/api/agents/${encodeURIComponent(agent.label)}/runs`
      );
      setRuns(data);
      setShowHistory(true);
    } catch {
      setRuns([]);
      setShowHistory(true);
    }
  }

  const isRunning = agent.pid !== null;

  // Action button styles
  const primaryBtn: React.CSSProperties = {
    background: "var(--accent)",
    color: "var(--surface)",
    borderRadius: "var(--radius-sm)",
  };
  const ghostBtn: React.CSSProperties = {
    background: "transparent",
    border: "1px solid var(--border-strong)",
    color: "var(--text)",
    borderRadius: "var(--radius-sm)",
  };
  const dangerBtn: React.CSSProperties = {
    background: "var(--status-err)",
    color: "var(--surface)",
    borderRadius: "var(--radius-sm)",
  };
  const successBtn: React.CSSProperties = {
    background: "var(--status-ok)",
    color: "var(--surface)",
    borderRadius: "var(--radius-sm)",
  };

  return (
    <div
      className="p-5"
      style={{
        background: isRunning ? "var(--accent-bg)" : "var(--surface)",
        border: `1px solid ${
          isRunning ? "var(--accent-soft)" : "var(--border)"
        }`,
        borderRadius: "var(--radius-md)",
      }}
    >
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            href={`/agents/${encodeURIComponent(agent.label)}`}
            className="text-base inline-flex items-center transition-colors"
            style={{
              color: "var(--text)",
              fontWeight: 500,
              fontFamily: "var(--font-mono)",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.color = "var(--accent)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.color = "var(--text)")
            }
          >
            {agent.project}/{agent.name}
            <ExternalLink size={14} className="ml-1.5" />
          </Link>
          <p
            className="text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            {agent.role_badge}
          </p>
          {agent.description && (
            <p
              className="mt-1 text-sm"
              style={{ color: "var(--text-muted)" }}
            >
              {agent.description}
            </p>
          )}
        </div>
        <div className="flex items-center gap-4 text-sm">
          <StatusBadge agent={agent} />
          <span
            className="font-mono text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            排程：{agent.schedule_display}
          </span>
        </div>
      </div>

      {isRunning && (
        <ActivityIndicator activity={agent.current_activity} />
      )}

      {justStarted && !isRunning && (
        <div
          className="mt-2 flex items-center gap-2 px-3 py-2 text-xs"
          style={{
            background: "var(--surface-2)",
            border: "1px solid var(--status-warn)",
            borderRadius: "var(--radius-sm)",
          }}
        >
          <Loader2
            size={14}
            className="animate-spin"
            style={{ color: "var(--status-warn)" }}
          />
          <span style={{ color: "var(--status-warn)" }}>
            已觸發，等待啟動中...
          </span>
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-4 text-sm">
        {agent.merge_strategy_display !== "—" && (
          <span style={{ color: "var(--text)" }}>
            Merge:{" "}
            <code
              className="px-1.5 py-0.5 text-xs font-mono"
              style={{
                background: "var(--surface-2)",
                color: "var(--text)",
                borderRadius: 2,
              }}
            >
              {agent.merge_strategy_display}
            </code>
          </span>
        )}
        <span style={{ color: "var(--text)" }}>
          QA:{" "}
          <code
            className="px-1.5 py-0.5 text-xs font-mono"
            style={{
              background: "var(--surface-2)",
              color: "var(--text)",
              borderRadius: 2,
            }}
          >
            {agent.qa_display}
          </code>
        </span>
        {agent.recent_commit && (
          <span style={{ color: "var(--text-muted)" }}>
            最近 commit:{" "}
            <code
              className="text-xs font-mono"
              style={{ color: "var(--text)" }}
            >
              {agent.recent_commit.sha}
            </code>{" "}
            {agent.recent_commit.message}
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="mt-4 flex flex-wrap gap-2">
        {!agent.installed && (
          <button
            disabled={busy}
            onClick={() =>
              action("/api/agents/install", {
                plist_path: agent.plist_path,
              })
            }
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium disabled:opacity-50"
            style={primaryBtn}
          >
            <Download size={14} /> 安裝
          </button>
        )}
        {agent.installed && !agent.loaded && (
          <button
            disabled={busy}
            onClick={() =>
              action("/api/agents/load", { label: agent.label })
            }
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium disabled:opacity-50"
            style={successBtn}
          >
            <Play size={14} /> 啟動
          </button>
        )}
        {agent.installed && agent.loaded && (
          <button
            disabled={busy}
            onClick={() =>
              action("/api/agents/unload", { label: agent.label })
            }
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium disabled:opacity-50"
            style={dangerBtn}
          >
            <Square size={14} /> 停止
          </button>
        )}
        {agent.installed && (
          <button
            disabled={busy || isRunning}
            onClick={handleStart}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium disabled:opacity-50"
            style={ghostBtn}
          >
            {isRunning ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <RefreshCw size={14} />
            )}
            {isRunning ? "執行中..." : "立即執行"}
          </button>
        )}
      </div>

      {error && (
        <p
          className="mt-2 text-xs"
          style={{ color: "var(--status-err)" }}
        >
          {error}
        </p>
      )}
      {toast && !justStarted && (
        <p
          className="mt-2 text-xs"
          style={{ color: "var(--status-ok)" }}
        >
          {toast}
        </p>
      )}

      {/* Collapsible sections */}
      <div className="mt-4 flex gap-3 text-xs">
        {agent.git_safety && (
          <button
            onClick={() => setShowSafety(!showSafety)}
            className="inline-flex items-center gap-1 transition-colors"
            style={{ color: "var(--text-muted)" }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.color = "var(--text)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.color = "var(--text-muted)")
            }
          >
            <Shield size={14} />
            {showSafety ? (
              <ChevronDown size={14} />
            ) : (
              <ChevronRight size={14} />
            )}
            Git 安全設定
          </button>
        )}
        <button
          onClick={loadRuns}
          className="inline-flex items-center gap-1 transition-colors"
          style={{ color: "var(--text-muted)" }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.color = "var(--text)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.color = "var(--text-muted)")
          }
        >
          {showHistory ? (
            <ChevronDown size={14} />
          ) : (
            <ChevronRight size={14} />
          )}
          執行歷史
        </button>
      </div>

      {showSafety && agent.git_safety && (
        <div
          className="mt-2 p-3 text-xs"
          style={{
            background: "var(--surface-2)",
            borderRadius: "var(--radius-sm)",
          }}
        >
          {agent.git_safety.allowed_paths.length > 0 && (
            <p>
              <strong style={{ color: "var(--text)" }}>Allowed paths:</strong>{" "}
              {agent.git_safety.allowed_paths.map((p) => (
                <code
                  key={p}
                  className="mr-1 px-1 font-mono"
                  style={{
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    borderRadius: 2,
                    color: "var(--text)",
                  }}
                >
                  {p}
                </code>
              ))}
            </p>
          )}
          {agent.git_safety.forbidden_paths.length > 0 && (
            <p className="mt-1">
              <strong style={{ color: "var(--text)" }}>Forbidden paths:</strong>{" "}
              {agent.git_safety.forbidden_paths.map((p) => (
                <code
                  key={p}
                  className="mr-1 px-1 font-mono"
                  style={{
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    borderRadius: 2,
                    color: "var(--text)",
                  }}
                >
                  {p}
                </code>
              ))}
            </p>
          )}
          {agent.git_safety.max_files_changed > 0 && (
            <p
              className="mt-1"
              style={{ color: "var(--text)" }}
            >
              <strong>Max files:</strong> {agent.git_safety.max_files_changed}
            </p>
          )}
        </div>
      )}

      {showHistory && <RunHistory runs={runs || []} />}
    </div>
  );
}
