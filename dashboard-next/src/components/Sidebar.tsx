"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState, useCallback } from "react";
import {
  LayoutDashboard,
  FolderOpen,
  Bot,
  Coins,
  Sparkles,
  Wheat,
  Network,
  Workflow,
  Library,
  Activity,
  HardDrive,
  GitCompare,
  CalendarClock,
  FileWarning,
  GitBranch,
  ChevronRight,
  ChevronDown,
  UserRound,
} from "lucide-react";
import { apiFetch, type ProjectsData, type AgentsData } from "@/lib/api";
import Logo from "./Logo";

type NavNode =
  | {
      // A caption that groups the rows below it; not a route, never expands.
      kind: "section";
      label: string;
    }
  | {
      kind: "link";
      href: string;
      label: string;
      icon?: typeof LayoutDashboard;
      children?: NavNode[];
    }
  | {
      kind: "header";
      label: string;
      icon?: typeof LayoutDashboard;
      children: NavNode[];
    };

const NAV: NavNode[] = [
  // ── 看狀況 ────────────────────────────────────────────────────────────
  { kind: "section", label: "看狀況" },
  { kind: "link", href: "/", label: "總覽", icon: LayoutDashboard },
  {
    kind: "header",
    label: "系統健康",
    icon: Activity,
    children: [
      { kind: "link", href: "/health/disk", label: "磁碟容量", icon: HardDrive },
      { kind: "link", href: "/health/ssot", label: "SSOT 漂移", icon: GitCompare },
      { kind: "link", href: "/health/agents", label: "排程健康", icon: CalendarClock },
      { kind: "link", href: "/health/errors", label: "最近錯誤", icon: FileWarning },
      { kind: "link", href: "/health/git", label: "Git 衛生", icon: GitBranch },
    ],
  },
  // ── 做事 ──────────────────────────────────────────────────────────────
  { kind: "section", label: "做事" },
  { kind: "link", href: "/avatar", label: "助理", icon: UserRound },
  {
    kind: "link",
    href: "/projects/rivendell/workflow",
    label: "工作流程",
    icon: Workflow,
    children: [
      { kind: "link", href: "/projects/rivendell/workflow/ui", label: "UI Feature" },
      { kind: "link", href: "/projects/rivendell/workflow/backend", label: "Backend" },
      {
        kind: "link",
        href: "/projects/rivendell/workflow/slide",
        label: "Slide",
        children: [
          { kind: "link", href: "/projects/rivendell/workflow/slide?branch=branch-a", label: "A. 投資人 BP" },
          { kind: "link", href: "/projects/rivendell/workflow/slide?branch=branch-b", label: "B. 客戶客製提案" },
          { kind: "link", href: "/projects/rivendell/workflow/slide?branch=branch-c", label: "C. IoT / 廠務報告" },
          { kind: "link", href: "/projects/rivendell/workflow/slide?branch=branch-d", label: "D. B2B 首拜 / 通用" },
        ],
      },
      { kind: "link", href: "/projects/rivendell/workflow/maintenance", label: "Maintenance" },
    ],
  },
  // ── 管資產 ────────────────────────────────────────────────────────────
  { kind: "section", label: "管資產" },
  {
    kind: "header",
    label: "技能庫",
    icon: Library,
    children: [
      { kind: "link", href: "/skills", label: "Skill 總覽", icon: Sparkles },
      { kind: "link", href: "/skills/roles", label: "依角色看", icon: UserRound },
      { kind: "link", href: "/harvest", label: "Skill Harvest", icon: Wheat },
    ],
  },
  { kind: "link", href: "/projects", label: "專案", icon: FolderOpen },
  { kind: "link", href: "/agents", label: "Agent", icon: Bot },
  { kind: "link", href: "/tokens", label: "Token 用量", icon: Coins },
  { kind: "link", href: "/ports", label: "部署", icon: Network },
];

function nodeId(node: NavNode): string {
  if (node.kind === "link") return node.href;
  return `${node.kind}:${node.label}`;
}

/** Splits a node's href into pathname + query-param entries for matching.
 *  Query-aware nodes (Slide branches with ?branch=...) need to match both
 *  the pathname AND every query param they declare. */
function parseHref(href: string): {
  pathname: string;
  params: [string, string][];
} {
  const qIdx = href.indexOf("?");
  if (qIdx < 0) return { pathname: href, params: [] };
  const path = href.slice(0, qIdx);
  const params = new URLSearchParams(href.slice(qIdx + 1));
  return { pathname: path, params: Array.from(params.entries()) };
}

/** Does a node's href match the current URL (pathname + search params)? */
function nodeMatches(
  href: string,
  currentPath: string,
  currentParams: URLSearchParams,
): boolean {
  const { pathname, params } = parseHref(href);
  const pathMatch =
    pathname === "/" ? currentPath === "/" : currentPath.startsWith(pathname);
  if (!pathMatch) return false;
  for (const [k, v] of params) {
    if (currentParams.get(k) !== v) return false;
  }
  return true;
}

/** Returns the set of node ids whose subtree contains the active route. */
function ancestorsOfPath(
  nodes: NavNode[],
  pathname: string,
  searchParams: URLSearchParams,
): Set<string> {
  const out = new Set<string>();
  function visit(node: NavNode, ancestors: string[]): boolean {
    if (node.kind === "section") return false;
    const id = nodeId(node);
    const selfMatches =
      node.kind === "link" && nodeMatches(node.href, pathname, searchParams);
    let descendantMatches = false;
    if (node.kind !== "link" || node.children) {
      const children =
        node.kind === "header" ? node.children : node.children ?? [];
      for (const c of children) {
        if (visit(c, [...ancestors, id])) descendantMatches = true;
      }
    }
    if (descendantMatches) out.add(id);
    return selfMatches || descendantMatches;
  }
  for (const n of nodes) visit(n, []);
  return out;
}

interface RunningAgent {
  label: string;
  name: string;
  project: string;
  pid: number | null;
  activity: { tool: string; label: string; detail: string } | null;
}

function RunningAgentsPanel() {
  const [agents, setAgents] = useState<RunningAgent[]>([]);

  const poll = useCallback(() => {
    apiFetch<AgentsData>("/api/agents")
      .then((data) => {
        const running = data.agents
          .filter((a) => a.pid !== null)
          .map((a) => ({
            label: a.label,
            name: a.name,
            project: a.project,
            pid: a.pid,
            activity: a.current_activity ?? null,
          }));
        setAgents(running);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    poll();
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, [poll]);

  if (agents.length === 0) return null;

  return (
    <div
      className="px-3 py-3"
      style={{ borderTop: "1px solid var(--border)" }}
    >
      <p
        className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider"
        style={{ color: "var(--text-subtle)" }}
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
        執行中 ({agents.length})
      </p>
      <div className="space-y-1.5">
        {agents.map((a) => (
          <Link
            key={a.label}
            href={`/agents/${encodeURIComponent(a.label)}`}
            className="block rounded-md px-2 py-1.5 transition-colors"
            style={{ color: "var(--text)" }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = "var(--surface-2)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "transparent")
            }
          >
            <div className="flex items-center gap-2 text-xs">
              <span
                className="h-1.5 w-1.5 shrink-0 rounded-full"
                style={{ background: "var(--status-ok)" }}
              />
              <span className="min-w-0 truncate font-medium">{a.name}</span>
              <span
                className="ml-auto shrink-0 font-mono text-[10px]"
                style={{ color: "var(--text-subtle)" }}
              >
                {a.project}
              </span>
            </div>
            {a.activity && (
              <div
                className="mt-0.5 ml-3.5 flex items-center gap-1.5 text-[10px]"
                style={{ color: "var(--text-subtle)" }}
              >
                <span style={{ color: "var(--text-muted)", fontWeight: 500 }}>
                  {a.activity.label}
                </span>
                {a.activity.detail && (
                  <span className="min-w-0 truncate font-mono">
                    {a.activity.detail}
                  </span>
                )}
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}

// useSearchParams forces a CSR bailout, so this part must live inside a
// <Suspense> boundary. Extracted into its own component for that reason.
function SidebarNav() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [manualExpanded, setManualExpanded] = useState<Set<string>>(
    () => new Set(),
  );
  const routeAncestors = useMemo(
    () => ancestorsOfPath(NAV, pathname, searchParams),
    [pathname, searchParams],
  );
  const expanded = useMemo(
    () => new Set([...manualExpanded, ...routeAncestors]),
    [manualExpanded, routeAncestors],
  );

  function toggle(id: string) {
    setManualExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const leafHref = (() => {
    let leaf: string | null = null;
    let bestScore = -1;
    function visit(node: NavNode) {
      if (node.kind === "section") return;
      if (node.kind === "link" && nodeMatches(node.href, pathname, searchParams)) {
        const { pathname: hPath, params } = parseHref(node.href);
        const score = hPath.length + params.length * 100;
        if (score > bestScore) {
          leaf = node.href;
          bestScore = score;
        }
      }
      const children =
        node.kind === "header"
          ? node.children
          : node.kind === "link" && node.children
            ? node.children
            : [];
      for (const c of children) visit(c);
    }
    for (const n of NAV) visit(n);
    return leaf;
  })();

  function renderNode(node: NavNode, depth: number, key: string): React.ReactElement {
    if (node.kind === "section") {
      return (
        <p
          key={key}
          className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider"
          style={{ color: "var(--text-subtle)", paddingTop: key === "n-0" ? 0 : 14 }}
        >
          {node.label}
        </p>
      );
    }
    const id = nodeId(node);
    const children =
      node.kind === "header"
        ? node.children
        : node.kind === "link" && node.children
          ? node.children
          : [];
    const hasChildren = children.length > 0;
    const isExpanded = expanded.has(id);
    const padLeft =
      depth === 0 ? 12 : depth === 1 ? 32 : 48;
    const chevSize = 12;

    const Chevron = hasChildren ? (
      <button
        type="button"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          toggle(id);
        }}
        aria-label={isExpanded ? "collapse" : "expand"}
        className="flex items-center justify-center shrink-0 rounded p-0.5 transition-colors"
        style={{
          color: "var(--text-subtle)",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text)")}
        onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-subtle)")}
      >
        {isExpanded ? (
          <ChevronDown size={chevSize} />
        ) : (
          <ChevronRight size={chevSize} />
        )}
      </button>
    ) : null;

    let rowEl: React.ReactElement;
    if (node.kind === "header") {
      // Header rows are toggle-only but styled like a top-level link so
      // 總覽 / 專案管理 / Skills all read at the same visual weight.
      const Icon = node.icon;
      const fontSize = depth === 0 ? 14 : depth === 1 ? 13 : 12;
      rowEl = (
        <div
          role="button"
          tabIndex={0}
          onClick={() => toggle(id)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              toggle(id);
            }
          }}
          className="flex items-center gap-3 w-full text-left rounded-md py-2 font-medium transition-colors"
          style={{
            paddingLeft: padLeft,
            paddingRight: hasChildren ? 4 : 12,
            fontSize,
            background: "transparent",
            color: "var(--text-muted)",
            border: "none",
            cursor: "pointer",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "var(--surface)";
            e.currentTarget.style.color = "var(--text)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.color = "var(--text-muted)";
          }}
        >
          {Icon ? <Icon size={depth === 0 ? 18 : 16} /> : null}
          <span>{node.label}</span>
          <span className="ml-auto">{Chevron}</span>
        </div>
      );
    } else {
      const { href, label, icon: Icon } = node;
      const active = href === leafHref;
      const fontSize = depth === 0 ? 14 : depth === 1 ? 13 : 12;
      rowEl = (
        <div className="flex items-stretch">
          <Link
            href={href}
            className={`flex items-center gap-3 rounded-md py-2 font-medium flex-1 transition-colors`}
            style={{
              paddingLeft: padLeft,
              paddingRight: hasChildren ? 4 : 12,
              fontSize,
              background: active ? "var(--surface)" : "transparent",
              color: active ? "var(--text)" : "var(--text-muted)",
              boxShadow: active ? "0 0 0 1px var(--border)" : "none",
            }}
            onMouseEnter={(e) => {
              if (!active) {
                e.currentTarget.style.background = "var(--surface)";
                e.currentTarget.style.color = "var(--text)";
              }
            }}
            onMouseLeave={(e) => {
              if (!active) {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.color = "var(--text-muted)";
              }
            }}
          >
            {Icon ? <Icon size={depth === 0 ? 18 : 16} /> : null}
            <span>{label}</span>
          </Link>
          {hasChildren && (
            <div className="flex items-center pr-2">{Chevron}</div>
          )}
        </div>
      );
    }

    return (
      <div key={key}>
        {rowEl}
        {hasChildren && isExpanded && (
          <div>
            {children.map((c, i) => renderNode(c, depth + 1, `${key}-${i}`))}
          </div>
        )}
      </div>
    );
  }

  return (
    <nav className="flex flex-col gap-0.5 px-2">
      {NAV.map((n, i) => renderNode(n, 0, `n-${i}`))}
    </nav>
  );
}

export default function Sidebar() {
  const [projects, setProjects] = useState<string[]>([]);

  useEffect(() => {
    apiFetch<ProjectsData>("/api/projects")
      .then((d) => setProjects(d.projects.map((p) => p.name)))
      .catch(() => {});
  }, []);

  return (
    <aside
      className="flex w-56 shrink-0 flex-col min-h-screen"
      style={{
        background: "var(--surface-2)",
        borderRight: "1px solid var(--border)",
      }}
    >
      <div className="px-4 pt-6 pb-1">
        <Logo size={28} />
      </div>
      <p
        className="px-4 pb-5 font-mono text-[11px]"
        style={{ color: "var(--text-muted)", letterSpacing: "0.02em" }}
      >
        council of skills · refuge of work
      </p>

      {/* Project switcher */}
      <div className="px-3 pb-4">
        <select
          className="w-full rounded-md px-2.5 py-1.5 text-xs font-mono"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            color: "var(--text)",
          }}
        >
          <option value="">all projects</option>
          {projects.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>

      <Suspense fallback={null}>
        <SidebarNav />
      </Suspense>

      <div className="mt-auto">
        <RunningAgentsPanel />
      </div>
    </aside>
  );
}
