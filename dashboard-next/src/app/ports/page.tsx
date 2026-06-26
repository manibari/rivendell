"use client";

import React, { useEffect, useMemo, useState } from "react";
import { apiFetch, type PortInfo, type PortsData } from "@/lib/api";
import { AlertTriangle, Eye, EyeOff, ExternalLink, Folder, MinusCircle, RefreshCw } from "lucide-react";
import StatusDot from "@/components/StatusDot";

const TABS = ["全部", "前端", "後端", "資料庫"] as const;
type Tab = (typeof TABS)[number];

// ── Sub-components ────────────────────────────────────────────────────────────

function TypeChip({ type }: { type: PortInfo["type"] }) {
  // All types use the same neutral chip — DESIGN.md says no extra brand colors.
  // The "type" label is the differentiator, not the color.
  return (
    <span
      className="text-[10px] font-mono"
      style={{
        background: "var(--surface-2)",
        color: "var(--text)",
        border: "1px solid var(--border)",
        padding: "2px 6px",
        borderRadius: "var(--radius-sm)",
      }}
    >
      {type}
    </span>
  );
}

function PortStatusBadge({ status }: { status: PortInfo["status"] }) {
  const dot: "ok" | "warn" | "err" | "idle" =
    status === "live"
      ? "ok"
      : status === "drift"
        ? "err"
        : status === "wild"
          ? "warn"
          : status === "stopped"
            ? "idle"
            : "warn";
  const label =
    status === "drift"
      ? "declared-only"
      : status === "wild"
        ? "wild"
        : status;
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-mono"
      style={{
        borderRadius: 99,
        background: "var(--surface-2)",
      }}
    >
      <StatusDot status={dot} />
      {label}
    </span>
  );
}

function PortRow({ port }: { port: PortInfo }) {
  const clickable = port.web && port.status !== "unknown";
  const listenerTitle = port.listener?.pid
    ? `${port.listener.command || "listener"} pid ${port.listener.pid}`
    : undefined;

  return (
    <tr
      className={clickable ? "cursor-pointer transition-colors" : undefined}
      onClick={
        clickable
          ? () => window.open(`http://localhost:${port.port}`, "_blank")
          : undefined
      }
      onMouseEnter={
        clickable
          ? (e) => (e.currentTarget.style.background = "var(--surface-2)")
          : undefined
      }
      onMouseLeave={
        clickable
          ? (e) => (e.currentTarget.style.background = "transparent")
          : undefined
      }
    >
      <td
        className="px-4 py-3 font-mono text-sm tabular-nums"
        style={{ color: "var(--text)", fontWeight: 500 }}
      >
        {port.port}
      </td>
      <td className="px-4 py-3 text-sm" style={{ color: "var(--text)" }}>
        {port.service}
      </td>
      <td
        className="px-4 py-3 font-mono text-xs"
        style={{ color: "var(--text-muted)" }}
      >
        {port.container}
      </td>
      <td className="px-4 py-3">
        <TypeChip type={port.type} />
      </td>
      <td className="px-4 py-3">
        <PortStatusBadge status={port.status} />
      </td>
      <td className="px-4 py-2" title={listenerTitle}>
        {port.web ? (
          <a
            href={`http://localhost:${port.port}`}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            title={`開啟 localhost:${port.port}`}
            className="flex items-center justify-center w-7 h-7 rounded-md transition-colors"
            style={{ color: "var(--text-muted)" }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "var(--text)";
              e.currentTarget.style.background = "var(--surface-2)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "var(--text-muted)";
              e.currentTarget.style.background = "transparent";
            }}
          >
            <ExternalLink size={14} />
          </a>
        ) : (
          <span
            className="flex items-center justify-center w-7 h-7"
            style={{ color: "var(--text-subtle)" }}
            title="非 HTTP 服務"
          >
            <MinusCircle size={14} />
          </span>
        )}
      </td>
    </tr>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function PortsPage() {
  const [data, setData] = useState<PortsData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("全部");
  // Default view = current deployment (live ports only). The toggle reveals the
  // "related deployments" — ports declared in compose but not currently running
  // (drift), plus undeclared local listeners (wild).
  const [showRelated, setShowRelated] = useState(false);

  // Inline fetch so we don't trigger the react-hooks/set-state-in-effect lint
  // (calling a wrapper that also setStates from inside useEffect was the prior
  // pattern; this version keeps load() for the explicit Refresh button only).
  useEffect(() => {
    apiFetch<PortsData>("/api/ports")
      .then((d) => {
        setData(d);
        setErr(null);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : String(e)));
  }, []);

  const load = (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true);
    apiFetch<PortsData>("/api/ports")
      .then((d) => {
        setData(d);
        setErr(null);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : String(e)))
      .finally(() => setRefreshing(false));
  };

  const filtered = useMemo(() => {
    if (!data) return [];
    return activeTab === "全部"
      ? data.ports
      : data.ports.filter((p) => p.category === activeTab);
  }, [data, activeTab]);

  const grouped = useMemo(() => {
    const map = new Map<string, PortInfo[]>();
    for (const p of filtered) {
      if (!map.has(p.project)) map.set(p.project, []);
      map.get(p.project)!.push(p);
    }
    return Array.from(map.entries());
  }, [filtered]);

  const liveCount = filtered.filter((p) => p.status === "live").length;
  const driftCount = filtered.filter((p) => p.status === "drift").length;
  const wildCount = filtered.filter((p) => p.status === "wild").length;
  const relatedCount = filtered.filter((p) => p.status !== "live").length;

  // Current deployment (live) shown by default; related (non-live) ports render
  // below them within each group only when the toggle is on. Groups with nothing
  // visible are dropped so the table doesn't show empty project headers.
  const visibleGrouped = useMemo(() => {
    return grouped
      .map(([project, ports]) => {
        const live = ports.filter((p) => p.status === "live");
        const related = ports.filter((p) => p.status !== "live");
        const visible = showRelated ? [...live, ...related] : live;
        return [project, visible, related.length] as const;
      })
      .filter(([, visible]) => visible.length > 0);
  }, [grouped, showRelated]);

  if (err && !data) {
    return (
      <div
        className="px-4 py-3 text-sm"
        style={{
          background: "var(--surface-2)",
          color: "var(--status-err)",
          border: "1px solid var(--status-err)",
          borderRadius: "var(--radius-md)",
        }}
      >
        無法載入 Port 資料 — {err}
      </div>
    );
  }

  if (!data)
    return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;

  return (
    <div>
      <div className="flex items-start justify-between mb-5">
        <div>
          <h1
            className="tracking-tight"
            style={{
              fontSize: 28,
              fontWeight: 500,
              color: "var(--text)",
              letterSpacing: "-0.02em",
            }}
          >
            部署管理
          </h1>
          <p
            className="mt-1 text-sm"
            style={{ color: "var(--text-muted)" }}
          >
            當前實際部署的服務 · 切換「相關部署」可顯示已宣告但未啟動的 port
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div
            className="flex items-center gap-3 text-xs font-mono tabular-nums"
            style={{ color: "var(--text-muted)" }}
          >
            <StatusDot status="ok" label={`${liveCount} live`} />
            <StatusDot status="err" label={`${driftCount} drift`} />
            <StatusDot status="warn" label={`${wildCount} wild`} />
          </div>
          <button
            onClick={() => setShowRelated((v) => !v)}
            title={
              showRelated
                ? "隱藏相關部署（已宣告但未啟動 / 未宣告的本機 listener）"
                : "顯示相關部署（已宣告但未啟動 / 未宣告的本機 listener）"
            }
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium transition-colors"
            style={{
              background: showRelated ? "var(--accent-bg)" : "var(--surface)",
              border: `1px solid ${showRelated ? "var(--accent)" : "var(--border-strong)"}`,
              borderRadius: "var(--radius-sm)",
              color: showRelated ? "var(--accent)" : "var(--text-muted)",
            }}
          >
            {showRelated ? <Eye size={14} /> : <EyeOff size={14} />}
            相關部署
            <span
              className="font-mono text-[10px] tabular-nums px-1.5 py-0.5"
              style={{
                borderRadius: 99,
                background: showRelated ? "var(--surface)" : "var(--surface-2)",
                color: showRelated ? "var(--accent)" : "var(--text-muted)",
              }}
            >
              {relatedCount}
            </span>
          </button>
          <button
            onClick={() => load(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-50"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border-strong)",
              borderRadius: "var(--radius-sm)",
              color: "var(--text)",
            }}
          >
            <RefreshCw
              size={14}
              className={refreshing ? "animate-spin" : ""}
            />
            Refresh
          </button>
        </div>
      </div>

      {/* Tab bar */}
      <div
        className="flex gap-1 mb-4"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        {TABS.map((tab) => {
          const count =
            tab === "全部"
              ? data.ports.length
              : data.ports.filter((p) => p.category === tab).length;
          const isActive = activeTab === tab;
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className="px-3 py-2 text-sm font-medium transition-colors"
              style={{
                borderBottom: `2px solid ${
                  isActive ? "var(--accent)" : "transparent"
                }`,
                marginBottom: -1,
                color: isActive ? "var(--text)" : "var(--text-muted)",
              }}
            >
              {tab}
              <span
                className="ml-1.5 px-1.5 py-0.5 text-[10px] font-mono tabular-nums"
                style={{
                  borderRadius: 99,
                  background: isActive
                    ? "var(--accent-bg)"
                    : "var(--surface-2)",
                  color: isActive ? "var(--accent)" : "var(--text-muted)",
                }}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Table */}
      <div
        className="overflow-hidden"
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-md)",
        }}
      >
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border)" }}>
              {["Port", "服務", "Container", "類型", "狀態"].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left font-mono text-[10px] uppercase"
                  style={{
                    color: "var(--text-subtle)",
                    letterSpacing: "0.08em",
                  }}
                >
                  {h}
                </th>
              ))}
              <th className="px-4 py-3 w-10" />
            </tr>
          </thead>
          <tbody>
            {visibleGrouped.map(([project, ports, relatedLen], gi) => {
              const folder = ports.find((p) => p.folder)?.folder ?? null;
              const stale = folder?.includes("/Documents/Projects/") ?? false;
              const health = data.health?.[project] ?? null;
              return (
              <React.Fragment key={`group-${project}-${gi}`}>
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-2"
                    style={{
                      background: "var(--surface-2)",
                      borderTop:
                        gi > 0 ? "1px solid var(--border)" : "none",
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <Folder
                        size={14}
                        style={{ color: "var(--text-muted)" }}
                      />
                      <span
                        className="text-xs"
                        style={{ color: "var(--text)", fontWeight: 500 }}
                      >
                        {project}
                      </span>
                      <span
                        className="text-[10px] font-mono tabular-nums"
                        style={{ color: "var(--text-subtle)" }}
                      >
                        {ports.length} port{ports.length > 1 ? "s" : ""}
                      </span>
                      {folder && (
                        <span
                          className="text-[10px] font-mono"
                          style={{ color: "var(--text-subtle)" }}
                          title={folder}
                        >
                          · {folder.split("/").pop()}
                        </span>
                      )}
                      {stale && (
                        <span
                          className="inline-flex items-center gap-1 text-[10px] font-mono"
                          style={{ color: "var(--status-err)" }}
                          title={`容器跑在舊 iCloud 路徑（${folder}）— 應改用 ~/code 重建`}
                        >
                          <AlertTriangle size={11} />
                          iCloud 路徑
                        </span>
                      )}
                      {!showRelated && relatedLen > 0 && (
                        <span
                          className="text-[10px] font-mono tabular-nums"
                          style={{ color: "var(--text-subtle)" }}
                          title="此專案另有相關部署（未啟動），開啟上方「相關部署」可見"
                        >
                          +{relatedLen} 相關
                        </span>
                      )}
                      {health && (
                        <span
                          className="inline-flex items-center text-[10px] font-mono"
                          title={`部署健康：${health.detail}${health.url ? ` (${health.url})` : ""}`}
                        >
                          <StatusDot
                            status={
                              health.status === "ok"
                                ? "ok"
                                : health.status === "down"
                                  ? "err"
                                  : "idle"
                            }
                            label={
                              health.status === "ok"
                                ? "healthy"
                                : health.status === "down"
                                  ? "unhealthy"
                                  : "health 未知"
                            }
                          />
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
                {ports.map((port) => (
                  <PortRow
                    key={`${port.project}-${port.service}-${port.port}`}
                    port={port}
                  />
                ))}
              </React.Fragment>
              );
            })}
            {visibleGrouped.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-8 text-center text-sm"
                  style={{ color: "var(--text-muted)" }}
                >
                  無符合條件的 port
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p
        className="mt-3 text-xs"
        style={{ color: "var(--text-subtle)" }}
      >
        資料源：
        <code
          className="font-mono"
          style={{ color: "var(--text-muted)" }}
        >
          docker-compose.yml
        </code>{" "}
        · 狀態：compose 宣告與本機 TCP listener 比對
      </p>
    </div>
  );
}
