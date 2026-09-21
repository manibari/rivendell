"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import {
  apiFetch,
  apiPost,
  type AgentInfo,
  type AgentsData,
  type AgentRun,
  type AgentFile,
  type AgentFileContent,
} from "@/lib/api";
import RunHistory from "@/components/RunHistory";
import {
  ArrowLeft,
  Play,
  Square,
  RefreshCw,
  FileText,
  Clock,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";

function StatusBadge({ agent }: { agent: AgentInfo }) {
  if (!agent.installed)
    return <span className="text-zinc-400">⚪ 未安裝</span>;
  if (agent.exit_code !== null && agent.exit_code !== 0)
    return <span className="text-red-500">🔴 Exit {agent.exit_code}</span>;
  if (agent.loaded)
    return <span className="text-green-600">🟢 已載入</span>;
  return <span className="text-red-500">🔴 未載入</span>;
}

function FileViewer({ label }: { label: string }) {
  const [files, setFiles] = useState<AgentFile[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState<AgentFileContent | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiFetch<AgentFile[]>(
      `/api/agents/${encodeURIComponent(label)}/files`
    ).then(setFiles).catch(() => setFiles([]));
  }, [label]);

  async function openFile(path: string) {
    if (selected === path) {
      setSelected(null);
      setContent(null);
      return;
    }
    setLoading(true);
    setSelected(path);
    try {
      const data = await apiFetch<AgentFileContent>(
        `/api/agents/${encodeURIComponent(label)}/file?path=${encodeURIComponent(path)}`
      );
      setContent(data);
    } catch {
      setContent({ name: "error", content: "Failed to load file", size: 0 });
    } finally {
      setLoading(false);
    }
  }

  if (files.length === 0) {
    return <p className="text-sm text-zinc-500">尚無檔案</p>;
  }

  // Group files by type
  const logs = files.filter((f) => f.type === "log");
  const reports = files.filter((f) => f.type === "md" || f.type === "html");
  const data = files.filter(
    (f) => f.type !== "log" && f.type !== "md" && f.type !== "html"
  );

  const groups = [
    { title: "Reports", icon: "📄", items: reports },
    { title: "Logs", icon: "📋", items: logs },
    { title: "Data", icon: "📊", items: data },
  ].filter((g) => g.items.length > 0);

  return (
    <div className="space-y-4">
      {groups.map((group) => (
        <div key={group.title}>
          <h4 className="mb-2 text-xs font-semibold uppercase text-zinc-500">
            {group.icon} {group.title} ({group.items.length})
          </h4>
          <div className="space-y-1">
            {group.items.map((f) => (
              <div key={f.path}>
                <button
                  onClick={() => openFile(f.path)}
                  className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm transition-colors ${
                    selected === f.path
                      ? "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300"
                      : "hover:bg-zinc-100 dark:hover:bg-zinc-800"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {selected === f.path ? (
                      <ChevronDown size={14} />
                    ) : (
                      <ChevronRight size={14} />
                    )}
                    <FileText size={14} />
                    <span className="font-mono">{f.name}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-zinc-400">
                    <span>
                      {f.size > 1024
                        ? `${(f.size / 1024).toFixed(1)} KB`
                        : `${f.size} B`}
                    </span>
                    <span>
                      {new Date(f.modified * 1000).toLocaleString("zh-TW", {
                        month: "2-digit",
                        day: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </button>
                {selected === f.path && (
                  <div className="mt-1 rounded-md border border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900">
                    {loading ? (
                      <p className="p-4 text-sm text-zinc-400">載入中...</p>
                    ) : content ? (
                      <pre className="max-h-96 overflow-auto p-4 text-xs leading-relaxed whitespace-pre-wrap">
                        {content.content}
                      </pre>
                    ) : null}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AgentDetailPage() {
  const params = useParams();
  const label = decodeURIComponent(params.label as string);

  const [agent, setAgent] = useState<AgentInfo | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [liveMode, setLiveMode] = useState(false);
  const [liveLines, setLiveLines] = useState<string[]>([]);
  const [liveRunning, setLiveRunning] = useState(false);
  const liveOffset = useRef(0);
  const liveRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(() => {
    apiFetch<AgentsData>("/api/agents").then((data) => {
      const found = data.agents.find((a) => a.label === label);
      setAgent(found || null);
    });
    apiFetch<AgentRun[]>(
      `/api/agents/${encodeURIComponent(label)}/runs?limit=20`
    )
      .then(setRuns)
      .catch(() => setRuns([]));
  }, [label]);

  useEffect(load, [load]);

  async function action(path: string, body: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      await apiPost(path, body);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  function startLiveMode() {
    setLiveMode(true);
    setLiveLines([]);
    setLiveRunning(true);

    // Snapshot current log size BEFORE triggering, so we only show new output
    apiFetch<{
      running: boolean;
      log_size: number;
      log_lines: string[];
    }>(`/api/agents/${encodeURIComponent(label)}/live?offset=999999`)
      .then((snap) => {
        // Start from end of existing log (skip old output)
        liveOffset.current = snap.log_size;
      })
      .catch(() => {
        liveOffset.current = 0;
      })
      .finally(() => {
        // Trigger the agent, then start polling immediately
        apiPost("/api/agents/start", { label })
          .then(() => pollLive())
          .catch((e) => setError(e instanceof Error ? e.message : String(e)));
      });
  }

  function pollLive() {
    if (liveRef.current) clearInterval(liveRef.current);
    let idleTicks = 0; // count polls with no new output after process ends

    liveRef.current = setInterval(async () => {
      try {
        const data = await apiFetch<{
          running: boolean;
          pid: number | null;
          log_lines: string[];
          log_size: number;
        }>(`/api/agents/${encodeURIComponent(label)}/live?offset=${liveOffset.current}`);

        setLiveRunning(data.running);
        if (data.log_lines.length > 0) {
          setLiveLines((prev) => [...prev, ...data.log_lines]);
          liveOffset.current = data.log_size;
          idleTicks = 0;
        }

        // Stop when: not running + got some output + no new lines for 2 ticks
        // This handles fast processes that finish before first poll
        if (!data.running) {
          idleTicks++;
          if (idleTicks >= 2) {
            if (liveRef.current) clearInterval(liveRef.current);
            liveRef.current = null;

            // If we never got new output (fast process finished before first poll),
            // fetch the last 30 lines so the user sees something
            setLiveLines((prev) => {
              if (prev.length === 0 && data.log_size > 0) {
                const tailOffset = Math.max(0, data.log_size - 30);
                apiFetch<{ log_lines: string[] }>(
                  `/api/agents/${encodeURIComponent(label)}/live?offset=${tailOffset}`
                ).then((tail) => {
                  if (tail.log_lines.length > 0) {
                    setLiveLines(tail.log_lines);
                  }
                }).catch(() => {});
              }
              return prev;
            });

            load(); // Refresh run history
          }
        }
      } catch {
        // ignore polling errors
      }
    }, 1000); // poll every 1s (was 2s) for faster feedback
  }

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (liveRef.current) clearInterval(liveRef.current);
    };
  }, [liveRef]);

  if (!agent) return <p className="text-zinc-400">載入中...</p>;

  return (
    <div className="mx-auto max-w-4xl">
      {/* Back link — go to project page if agent has a project */}
      <Link
        href={agent.project ? `/projects/${encodeURIComponent(agent.project)}` : "/agents"}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
      >
        <ArrowLeft size={16} /> {agent.project ? `返回 ${agent.project}` : "返回 Agent 列表"}
      </Link>

      {/* Header */}
      <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold">
              {agent.project}/{agent.name}
            </h1>
            <p className="mt-1 text-sm text-zinc-500">{agent.role_badge}</p>
            <p className="mt-1 font-mono text-xs text-zinc-400">
              {agent.label}
            </p>
          </div>
          <StatusBadge agent={agent} />
        </div>

        {/* Info grid */}
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <div>
            <span className="text-xs text-zinc-500">排程</span>
            <p className="font-medium">
              <Clock size={14} className="mr-1 inline" />
              {agent.schedule_display}
            </p>
          </div>
          <div>
            <span className="text-xs text-zinc-500">QA</span>
            <p className="font-medium">{agent.qa_display}</p>
          </div>
          <div>
            <span className="text-xs text-zinc-500">Merge</span>
            <p className="font-medium">{agent.merge_strategy_display}</p>
          </div>
          {agent.recent_commit && (
            <div>
              <span className="text-xs text-zinc-500">最近 Commit</span>
              <p className="font-mono text-xs">
                {agent.recent_commit.sha}{" "}
                <span className="text-zinc-500">
                  {agent.recent_commit.message}
                </span>
              </p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="mt-4 flex flex-wrap gap-2">
          {agent.installed && !agent.loaded && (
            <button
              disabled={busy}
              onClick={() =>
                action("/api/agents/load", { label: agent.label })
              }
              className="inline-flex items-center gap-1.5 rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
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
              className="inline-flex items-center gap-1.5 rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              <Square size={14} /> 停止
            </button>
          )}
          {agent.installed && (
            <button
              disabled={busy || liveRunning}
              onClick={startLiveMode}
              className="inline-flex items-center gap-1.5 rounded-md border border-zinc-300 px-3 py-1.5 text-xs font-medium hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
            >
              <RefreshCw size={14} className={liveRunning ? "animate-spin" : ""} />
              {liveRunning ? "執行中..." : "立即執行"}
            </button>
          )}
        </div>

        {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
      </div>

      {/* Live Execution Panel */}
      {liveMode && (
        <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50/30 dark:border-blue-900 dark:bg-blue-950/20">
          <div className="flex items-center justify-between border-b border-blue-200 px-4 py-2 dark:border-blue-900">
            <div className="flex items-center gap-2 text-sm font-medium">
              {liveRunning ? (
                <>
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-green-500" />
                  </span>
                  執行中 (PID polling...)
                </>
              ) : liveLines.length > 0 ? (
                <>
                  <span className="h-2.5 w-2.5 rounded-full bg-zinc-400" />
                  執行完成
                </>
              ) : (
                <>
                  <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-yellow-400" />
                  啟動中...
                </>
              )}
            </div>
            <button
              onClick={() => {
                setLiveMode(false);
                setLiveLines([]);
                if (liveRef.current) clearInterval(liveRef.current);
              }}
              className="text-xs text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
            >
              關閉
            </button>
          </div>
          <pre className="max-h-96 overflow-auto p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap">
            {liveLines.length > 0
              ? liveLines.join("\n")
              : liveRunning
                ? "等待輸出..."
                : "執行完成（無新輸出）"}
          </pre>
        </div>
      )}

      {/* Run History — click a row to expand its timeline */}
      <div className="mt-6 rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="mb-1 text-lg font-semibold">執行歷史</h2>
        <p className="mb-3 text-xs text-zinc-500">點擊任一筆展開時間線</p>
        {runs.length > 0 ? (
          <RunHistory runs={runs} agentLabel={label} />
        ) : (
          <p className="text-sm text-zinc-500">尚無執行紀錄</p>
        )}
      </div>

      {/* Files */}
      <div className="mt-6 rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="mb-4 text-lg font-semibold">Logs & 成果</h2>
        <FileViewer label={label} />
      </div>
    </div>
  );
}
