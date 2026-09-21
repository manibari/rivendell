"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, apiPost, type DiskTreeData, type DiskTreeNode } from "@/lib/api";
import { squarify, humanKB, tileColors } from "@/lib/treemap";

const VIEW_W = 1000;
const VIEW_H = 560;
const STALE_HOURS = 25;

function relativeTime(iso?: string): { text: string; stale: boolean } {
  if (!iso) return { text: "—", stale: true };
  const then = new Date(iso).getTime();
  const mins = Math.round((Date.now() - then) / 60000);
  const stale = mins > STALE_HOURS * 60;
  if (mins < 1) return { text: "剛剛", stale };
  if (mins < 60) return { text: `${mins} 分鐘前`, stale };
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return { text: `${hrs} 小時前`, stale };
  return { text: `${Math.round(hrs / 24)} 天前`, stale };
}

export default function DiskTreePage() {
  const [data, setData] = useState<DiskTreeData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [stack, setStack] = useState<DiskTreeNode[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(() => {
    apiFetch<DiskTreeData>("/api/health/disk-tree")
      .then((d) => {
        setData(d);
        setStack((prev) => (prev.length === 0 && d.tree ? [d.tree] : prev));
      })
      .catch((e) => setErr(e.message));
  }, []);

  useEffect(() => {
    load();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [load]);

  const refresh = useCallback(async () => {
    if (refreshing) return;
    const before = data?.generated_at;
    setRefreshing(true);
    try {
      await apiPost("/api/health/disk-tree/refresh", {});
    } catch {
      /* fall through to polling — cron/manual run may still land */
    }
    pollRef.current = setInterval(async () => {
      try {
        const d = await apiFetch<DiskTreeData>("/api/health/disk-tree");
        if (d.available && d.generated_at && d.generated_at !== before) {
          setData(d);
          setStack(d.tree ? [d.tree] : []);
          setRefreshing(false);
          if (pollRef.current) clearInterval(pollRef.current);
        }
      } catch {
        /* keep polling */
      }
    }, 4000);
  }, [data?.generated_at, refreshing]);

  const current = stack[stack.length - 1] ?? null;
  const tiles =
    current && current.children.length > 0
      ? squarify(current.children, { x: 0, y: 0, w: VIEW_W, h: VIEW_H })
      : [];
  const maxChild =
    current && current.children.length > 0
      ? Math.max(...current.children.map((c) => c.size_kb))
      : 0;

  const gen = relativeTime(data?.generated_at);

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <h1
          className="tracking-tight"
          style={{ fontSize: 28, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.02em" }}
        >
          磁碟容量
        </h1>
        <button
          type="button"
          onClick={refresh}
          disabled={refreshing}
          className="rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
          style={{
            background: refreshing ? "var(--surface-2)" : "var(--accent)",
            color: refreshing ? "var(--text-muted)" : "var(--surface)",
            border: "1px solid var(--border-strong)",
            cursor: refreshing ? "default" : "pointer",
          }}
        >
          {refreshing ? "掃描中…" : "重新整理"}
        </button>
      </div>

      {/* Context line: volume usage + snapshot freshness */}
      <div
        className="mb-5 flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[11px]"
        style={{ color: "var(--text-muted)" }}
      >
        {data?.df && (
          <span>
            {data.df.mount} · 已用 {humanKB(data.df.used_kb)} / {humanKB(data.df.size_kb)} ({data.df.percent}%)
          </span>
        )}
        <span style={{ color: gen.stale ? "var(--status-warn)" : "var(--text-subtle)" }}>
          快照：{gen.text}
          {gen.stale && " · 可能過時"}
          {data?.duration_sec != null && ` · 掃描 ${data.duration_sec}s`}
        </span>
      </div>

      {err && <p style={{ color: "var(--status-err)" }}>Error: {err}</p>}

      {!err && !data && <p style={{ color: "var(--text-muted)" }}>載入中...</p>}

      {data && !data.available && (
        <div
          className="p-6"
          style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}
        >
          <p style={{ color: "var(--text-muted)" }}>{data.hint || data.error || "尚無快照資料"}</p>
        </div>
      )}

      {/* Breadcrumb */}
      {current && stack.length > 0 && (
        <div className="mb-3 flex flex-wrap items-center gap-1 text-sm">
          {stack.map((n, idx) => {
            const last = idx === stack.length - 1;
            return (
              <span key={n.path} className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => setStack(stack.slice(0, idx + 1))}
                  className="rounded px-1.5 py-0.5 font-mono transition-colors"
                  style={{
                    color: last ? "var(--text)" : "var(--accent)",
                    fontWeight: last ? 500 : 400,
                    cursor: last ? "default" : "pointer",
                  }}
                >
                  {idx === 0 ? "~" : n.name}
                </button>
                {!last && <span style={{ color: "var(--text-subtle)" }}>/</span>}
              </span>
            );
          })}
          <span className="ml-2 font-mono text-xs" style={{ color: "var(--text-subtle)" }}>
            {current && humanKB(current.size_kb)}
          </span>
        </div>
      )}

      {/* Treemap */}
      {current && tiles.length > 0 && (
        <div
          style={{
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
            overflow: "hidden",
            background: "var(--surface)",
          }}
        >
          <svg
            viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
            width="100%"
            style={{ display: "block" }}
            role="img"
            aria-label="磁碟使用量 treemap"
          >
            {tiles.map((t) => {
              const [fill, textColor] = tileColors(t.node.size_kb, maxChild);
              const drillable = t.node.children.length > 0;
              const showLabel = t.w > 46 && t.h > 20;
              const showSize = t.w > 60 && t.h > 36;
              const maxChars = Math.max(0, Math.floor(t.w / 7) - 1);
              const name =
                t.node.name.length > maxChars ? t.node.name.slice(0, maxChars) + "…" : t.node.name;
              return (
                <g
                  key={t.node.path}
                  onClick={() => drillable && setStack([...stack, t.node])}
                  style={{ cursor: drillable ? "pointer" : "default" }}
                >
                  <title>
                    {t.node.path} — {humanKB(t.node.size_kb)}
                    {drillable ? " (點擊下鑽)" : ""}
                  </title>
                  <rect
                    x={t.x + 1}
                    y={t.y + 1}
                    width={Math.max(0, t.w - 2)}
                    height={Math.max(0, t.h - 2)}
                    fill={fill}
                    rx={2}
                  />
                  {showLabel && (
                    <text
                      x={t.x + 7}
                      y={t.y + 16}
                      fontSize={11}
                      fontFamily="var(--font-mono)"
                      fill={textColor}
                      style={{ pointerEvents: "none" }}
                    >
                      {name}
                    </text>
                  )}
                  {showSize && (
                    <text
                      x={t.x + 7}
                      y={t.y + 30}
                      fontSize={10}
                      fontFamily="var(--font-mono)"
                      fill={textColor}
                      opacity={0.8}
                      style={{ pointerEvents: "none" }}
                    >
                      {humanKB(t.node.size_kb)}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      )}

      {/* 明細 list — the treemap can't label small tiles (names truncate, tiny
          squares go blank), so every child gets a readable row here (QA
          2026-07-05, Peter: 「磁碟容量下面要有 list 說明」). Row click drills
          the same as clicking the tile. */}
      {current && current.children.length > 0 && (
        <div
          className="mt-4 overflow-hidden"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
          }}
        >
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {["#", "目錄", "大小", "佔比", ""].map((h, i) => (
                  <th
                    key={i}
                    className="px-4 py-2.5 text-left font-mono text-[10px] uppercase"
                    style={{ color: "var(--text-subtle)", letterSpacing: "0.08em" }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...current.children]
                .sort((a, b) => b.size_kb - a.size_kb)
                .map((c, i) => {
                  const share = current.size_kb > 0 ? (c.size_kb / current.size_kb) * 100 : 0;
                  const drillable = c.children.length > 0;
                  return (
                    <tr
                      key={c.path}
                      onClick={() => drillable && setStack([...stack, c])}
                      className={drillable ? "cursor-pointer transition-colors" : undefined}
                      style={{ borderBottom: "1px solid var(--border)" }}
                      onMouseEnter={(e) => {
                        if (drillable) e.currentTarget.style.background = "var(--surface-2)";
                      }}
                      onMouseLeave={(e) => {
                        if (drillable) e.currentTarget.style.background = "transparent";
                      }}
                    >
                      <td
                        className="px-4 py-2 font-mono text-xs tabular-nums"
                        style={{ color: "var(--text-subtle)" }}
                      >
                        {i + 1}
                      </td>
                      <td
                        className="px-4 py-2 font-mono text-xs"
                        style={{ color: "var(--text)" }}
                        title={c.path}
                      >
                        {c.name}
                      </td>
                      <td
                        className="px-4 py-2 font-mono text-xs tabular-nums"
                        style={{ color: "var(--text)" }}
                      >
                        {humanKB(c.size_kb)}
                      </td>
                      <td className="px-4 py-2" style={{ minWidth: 140 }}>
                        <div className="flex items-center gap-2">
                          <div
                            className="h-1.5 flex-1"
                            style={{
                              background: "var(--surface-2)",
                              borderRadius: 99,
                              overflow: "hidden",
                              maxWidth: 90,
                            }}
                          >
                            <div
                              className="h-full"
                              style={{
                                width: `${Math.min(100, share)}%`,
                                background: "var(--accent-soft)",
                                borderRadius: 99,
                              }}
                            />
                          </div>
                          <span
                            className="font-mono text-[11px] tabular-nums"
                            style={{ color: "var(--text-muted)" }}
                          >
                            {share.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      <td
                        className="px-4 py-2 text-right font-mono text-[11px]"
                        style={{ color: "var(--text-subtle)" }}
                      >
                        {drillable ? "下鑽 ›" : ""}
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      )}

      {current && current.children.length === 0 && data?.available && (
        <p className="mt-4 text-sm" style={{ color: "var(--text-muted)" }}>
          此目錄無更深的快照資料（快照深度 {data.depth}）。返回上層或重新整理以更深掃描。
        </p>
      )}
    </div>
  );
}
