"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiFetch, type SkillInfo, type SkillUsage } from "@/lib/api";
import MetricsRow from "@/components/MetricsRow";
import {
  Treemap,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
} from "recharts";

// The page answers one question: what is the skill architecture right now?
// Two views of the same 124 rivendell skills — the loop × PDCA grid (the
// taxonomy of record, same source as the README table) and the folder map
// (where the files live). gstack / builtin / external are filterable but
// off by default so they stop drowning the picture.

const LOOP_ORDER = ["sales", "gov", "invest", "hr", "knowledge", "platform", "dev", "shared"];
const PDCA_ORDER = ["plan", "do", "check", "act"] as const;

const LOOP_LABELS: Record<string, string> = {
  sales: "業務開發",
  gov: "政府案件",
  invest: "投資研究",
  hr: "人資",
  knowledge: "內容消化",
  platform: "平台自我改善",
  dev: "產品開發",
  shared: "跨循環共用",
};

const FOLDER_LABELS: Record<string, string> = {
  platform: "平台自我改善",
  agents: "自動化 Agent",
  planning: "需求與規劃",
  workflow: "工作流程與 Session",
  qa: "QA 與驗收",
  quality: "程式品質",
  git: "Git / GitHub",
  frontend: "前端",
  backend: "後端服務",
  sales: "業務開發",
  gov: "政府案件",
  invest: "投資研究",
  hr: "人資",
  knowledge: "內容消化",
  docs: "文件與簡報",
};

const SOURCE_LABELS: Record<string, string> = {
  rivendell: "rivendell",
  gstack: "gstack",
  external: "其他",
  builtin: "內建",
};

// DESIGN.md: differentiate by label, not color; sequential greens only.
const SEQ_GREENS = ["#2d4a3e", "#3e5c4f", "#4f6f5f", "#5b7a6a", "#7a9489", "#a3bbb1", "#c8d4d0", "#dfe7e3"];
const ACCENT = "#2d4a3e";
const ACCENT_SOFT = "#5b7a6a";
const SURFACE = "#ffffff";
const SURFACE_2 = "#f3f4f6";
const BORDER = "#e5e7eb";
const TEXT_SUBTLE = "#9ca3af";

const LIFECYCLE_COLORS: Record<string, string> = {
  manual: ACCENT,
  hook: ACCENT_SOFT,
  agent: "#b8772f",
  unknown: TEXT_SUBTLE,
};

const cardStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
};

const tooltipStyle: React.CSSProperties = {
  background: SURFACE,
  border: `1px solid ${BORDER}`,
  borderRadius: 4,
  fontFamily: "monospace",
  fontSize: 12,
};

function Tag({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "accent" }) {
  return (
    <span
      className="inline-block px-1.5 py-0.5 font-mono"
      style={{
        fontSize: 10,
        lineHeight: "14px",
        borderRadius: 2,
        background: tone === "accent" ? "var(--accent-bg)" : SURFACE_2,
        color: tone === "accent" ? "var(--accent)" : "var(--text-muted)",
      }}
    >
      {children}
    </span>
  );
}

function LifecycleBadge({ lifecycle }: { lifecycle: string }) {
  const color = LIFECYCLE_COLORS[lifecycle] || LIFECYCLE_COLORS.unknown;
  return (
    <span
      className="inline-block px-2 py-0.5 text-xs font-medium font-mono"
      style={{ borderRadius: 99, background: SURFACE_2, color, border: `1px solid ${color}`, fontSize: 10 }}
    >
      {lifecycle}
    </span>
  );
}

function SkillLink({ name }: { name: string }) {
  return (
    <Link
      href={`/skills/${encodeURIComponent(name)}`}
      className="inline-block font-mono transition-colors"
      style={{
        fontSize: 11,
        lineHeight: "16px",
        padding: "1px 6px",
        borderRadius: 3,
        border: "1px solid var(--border)",
        background: "var(--surface)",
        color: "var(--text)",
        whiteSpace: "nowrap",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--accent-soft)")}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
    >
      {name}
    </Link>
  );
}

function TreemapContent(props: { x: number; y: number; width: number; height: number; name: string; color: string }) {
  const { x, y, width, height, name, color } = props;
  if (width < 40 || height < 20) return null;
  return (
    <g>
      <rect x={x} y={y} width={width} height={height} rx={4} fill={color} stroke={SURFACE} strokeWidth={2} style={{ opacity: 0.95 }} />
      {width > 60 && height > 30 && (
        <text
          x={x + width / 2}
          y={y + height / 2}
          textAnchor="middle"
          dominantBaseline="central"
          fill={SURFACE}
          fontSize={Math.min(12, width / 6)}
          fontWeight={500}
          fontFamily="monospace"
        >
          {name}
        </text>
      )}
    </g>
  );
}

const selectStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-sm)",
  color: "var(--text)",
  fontFamily: "var(--font-mono)",
};

export default function SkillsPage() {
  const [skills, setSkills] = useState<SkillInfo[] | null>(null);
  const [usage, setUsage] = useState<SkillUsage>({});
  const [err, setErr] = useState<string | null>(null);
  const [source, setSource] = useState<string>("rivendell");
  const [search, setSearch] = useState("");
  const [filterFolder, setFilterFolder] = useState("");
  const [filterLoop, setFilterLoop] = useState("");

  useEffect(() => {
    apiFetch<SkillInfo[]>("/api/skills").then(setSkills).catch((e) => setErr(e.message));
    apiFetch<SkillUsage>("/api/skills/usage").then(setUsage).catch(() => {});
  }, []);

  const sourceCounts = useMemo(() => {
    const m = new Map<string, number>();
    for (const s of skills ?? []) m.set(s.source, (m.get(s.source) || 0) + 1);
    return m;
  }, [skills]);

  // Everything below the source toggle works on this subset.
  const scoped = useMemo(() => {
    if (!skills) return [];
    return source === "all" ? skills : skills.filter((s) => s.source === source);
  }, [skills, source]);

  const rivendell = useMemo(() => (skills ?? []).filter((s) => s.source === "rivendell"), [skills]);

  // Loop × PDCA grid is always over rivendell: only our skills carry the tags.
  const grid = useMemo(() => {
    const cells = new Map<string, SkillInfo[]>();
    const loopCount = new Map<string, number>();
    for (const s of rivendell) {
      if (!s.loop) continue;
      loopCount.set(s.loop, (loopCount.get(s.loop) || 0) + 1);
      if (!s.pdca) continue;
      const k = `${s.loop}/${s.pdca}`;
      if (!cells.has(k)) cells.set(k, []);
      cells.get(k)!.push(s);
    }
    const loops = LOOP_ORDER.filter((l) => loopCount.has(l));
    let gaps = 0;
    for (const l of loops) for (const p of PDCA_ORDER) if (!cells.has(`${l}/${p}`)) gaps++;
    return { cells, loops, loopCount, gaps, untagged: rivendell.filter((s) => !s.loop || !s.pdca).length };
  }, [rivendell]);

  const folders = useMemo(() => {
    const set = new Set(scoped.map((s) => s.folder || s.category).filter(Boolean));
    return Array.from(set).sort();
  }, [scoped]);

  const filtered = useMemo(() => {
    return scoped.filter((s) => {
      const f = s.folder || s.category;
      if (filterFolder && f !== filterFolder) return false;
      if (filterLoop && s.loop !== filterLoop) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          s.name.toLowerCase().includes(q) ||
          s.summary.toLowerCase().includes(q) ||
          f.toLowerCase().includes(q) ||
          s.loop.includes(q)
        );
      }
      return true;
    });
  }, [scoped, search, filterFolder, filterLoop]);

  const grouped = useMemo(() => {
    const map = new Map<string, SkillInfo[]>();
    for (const s of filtered) {
      const f = s.folder || s.category || "未分類";
      if (!map.has(f)) map.set(f, []);
      map.get(f)!.push(s);
    }
    return Array.from(map.entries()).sort(([a], [b]) => {
      if (a === "未分類") return 1;
      if (b === "未分類") return -1;
      return a.localeCompare(b);
    });
  }, [filtered]);

  const treemapData = useMemo(() => {
    const counts = new Map<string, number>();
    for (const s of rivendell) counts.set(s.folder || "未分類", (counts.get(s.folder || "未分類") || 0) + 1);
    return Array.from(counts.entries())
      .map(([name, size], i) => ({ name: `${name} (${size})`, size, color: SEQ_GREENS[i % SEQ_GREENS.length] }))
      .sort((a, b) => b.size - a.size);
  }, [rivendell]);

  const topSkills = useMemo(() => {
    const names = new Set(scoped.map((s) => s.name));
    return Object.entries(usage)
      .filter(([name]) => names.has(name))
      .map(([name, days]) => ({ name, count: days.reduce((s, d) => s + d.count, 0) }))
      .filter((s) => s.count > 0)
      .sort((a, b) => b.count - a.count)
      .slice(0, 12);
  }, [usage, scoped]);

  const metrics = useMemo(() => {
    if (!skills) return null;
    const invocable = scoped.filter((s) => s.invocable).length;
    return {
      total: scoped.length,
      folders: folders.length,
      loops: grid.loops.length,
      gaps: grid.gaps,
      invocableRate: scoped.length ? `${Math.round((invocable / scoped.length) * 100)}%` : "—",
    };
  }, [skills, scoped, folders, grid]);

  if (err) return <p style={{ color: "var(--status-err)" }}>Error: {err}</p>;
  if (!skills || !metrics) return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;

  const h2: React.CSSProperties = { fontSize: 14, fontWeight: 500, color: "var(--text)" };

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="tracking-tight" style={{ fontSize: 28, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.02em" }}>
            Skill 總覽
          </h1>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            循環 × PDCA 是分類的依據（與 README 覆蓋表同源）；資料夾是檔案所在。
            <Link href="/skills/roles" className="ml-2" style={{ color: "var(--accent)" }}>
              依角色看 →
            </Link>
          </p>
        </div>
        {/* Source toggle */}
        <div className="flex gap-1 p-0.5" style={{ background: SURFACE_2, borderRadius: "var(--radius-sm)" }}>
          {["rivendell", "gstack", "external", "builtin", "all"].map((k) => {
            const n = k === "all" ? skills.length : sourceCounts.get(k) || 0;
            if (k !== "all" && n === 0) return null;
            const on = source === k;
            return (
              <button
                key={k}
                type="button"
                onClick={() => {
                  setSource(k);
                  setFilterFolder("");
                  setFilterLoop("");
                }}
                className="px-2.5 py-1 text-xs font-mono transition-colors"
                style={{
                  borderRadius: 3,
                  background: on ? "var(--surface)" : "transparent",
                  color: on ? "var(--text)" : "var(--text-muted)",
                  boxShadow: on ? "0 0 0 1px var(--border)" : "none",
                }}
              >
                {k === "all" ? "全部" : SOURCE_LABELS[k]} {n}
              </button>
            );
          })}
        </div>
      </div>

      <MetricsRow
        metrics={[
          { label: "總數", value: metrics.total },
          { label: "資料夾", value: metrics.folders },
          { label: "循環", value: metrics.loops },
          { label: "缺環（格）", value: metrics.gaps },
          { label: "可呼叫", value: metrics.invocableRate },
        ]}
      />

      {/* Loop × PDCA grid — the architecture view */}
      <div className="mt-6 p-4" style={cardStyle}>
        <div className="mb-3 flex items-baseline justify-between gap-3">
          <h2 style={h2}>循環 × PDCA</h2>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            每格列出該循環在該階段的 skill；「—」代表缺環。
            {grid.untagged > 0 && ` 未標籤 ${grid.untagged} 支。`}
          </span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table className="w-full" style={{ borderCollapse: "separate", borderSpacing: 0, minWidth: 880 }}>
            <thead>
              <tr>
                <th className="text-left px-2 py-1.5 text-[11px] font-medium uppercase tracking-wider" style={{ color: "var(--text-subtle)", width: 150 }}>
                  loop
                </th>
                {PDCA_ORDER.map((p) => (
                  <th key={p} className="text-left px-2 py-1.5 text-[11px] font-medium uppercase tracking-wider" style={{ color: "var(--text-subtle)" }}>
                    {p}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {grid.loops.map((loop) => (
                <tr key={loop} style={{ borderTop: `1px solid ${BORDER}` }}>
                  <td className="px-2 py-2 align-top" style={{ borderTop: `1px solid ${BORDER}` }}>
                    <button
                      type="button"
                      onClick={() => setFilterLoop(filterLoop === loop ? "" : loop)}
                      className="text-left"
                      title="點一下只看這個循環"
                    >
                      <div className="font-mono text-sm" style={{ color: filterLoop === loop ? "var(--accent)" : "var(--text)", fontWeight: 500 }}>
                        {loop}
                      </div>
                      <div className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                        {LOOP_LABELS[loop] ?? ""} · {grid.loopCount.get(loop)}
                      </div>
                    </button>
                  </td>
                  {PDCA_ORDER.map((p) => {
                    const list = grid.cells.get(`${loop}/${p}`) ?? [];
                    return (
                      <td key={p} className="px-2 py-2 align-top" style={{ borderTop: `1px solid ${BORDER}`, borderLeft: `1px solid ${BORDER}` }}>
                        {list.length === 0 ? (
                          <span className="font-mono text-xs" title="缺環" style={{ color: "var(--text-subtle)" }}>
                            —
                          </span>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {list.map((s) => (
                              <SkillLink key={s.name} name={s.name} />
                            ))}
                          </div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Folder map + usage */}
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="p-4" style={cardStyle}>
          <h2 className="mb-3" style={h2}>
            資料夾（skills/&lt;folder&gt;/）
          </h2>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height={224}>
              <Treemap
                data={treemapData}
                dataKey="size"
                aspectRatio={4 / 3}
                content={<TreemapContent x={0} y={0} width={0} height={0} name="" color="" />}
              />
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-4" style={cardStyle}>
          <h2 className="mb-3" style={h2}>
            最常使用（累計呼叫次數）
          </h2>
          {topSkills.length === 0 ? (
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              這個來源沒有呼叫紀錄。
            </p>
          ) : (
            <div style={{ height: 224 }}>
              <ResponsiveContainer width="100%" height={224}>
                <BarChart data={topSkills.slice(0, 8)} layout="vertical" margin={{ top: 0, right: 40, left: 0, bottom: 0 }}>
                  <XAxis type="number" tick={{ fontSize: 10, fill: TEXT_SUBTLE, fontFamily: "monospace" }} tickLine={false} axisLine={false} />
                  <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 11, fill: "var(--text-muted)", fontFamily: "monospace" }} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v) => [v, "呼叫次數"]} cursor={{ fill: SURFACE_2 }} />
                  <Bar dataKey="count" fill={ACCENT} radius={[0, 3, 3, 0]} label={{ position: "right", fontSize: 10, fill: TEXT_SUBTLE, fontFamily: "monospace" }} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          <p className="mt-2 text-[11px] leading-relaxed" style={{ color: "var(--text-subtle)" }}>
            只計 Read SKILL.md 與 Skill 工具呼叫；description 自動觸發與 hook 不留紀錄，實際用量約為顯示的 3–5 倍。
          </p>
        </div>
      </div>

      {/* Search + filters */}
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <input
          type="text"
          placeholder="搜尋 skill..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-1.5 text-sm"
          style={selectStyle}
        />
        <select value={filterFolder} onChange={(e) => setFilterFolder(e.target.value)} className="px-3 py-1.5 text-sm" style={selectStyle}>
          <option value="">全部資料夾</option>
          {folders.map((f) => (
            <option key={f} value={f}>
              {f}
              {FOLDER_LABELS[f] ? ` — ${FOLDER_LABELS[f]}` : ""}
            </option>
          ))}
        </select>
        {source === "rivendell" && (
          <select value={filterLoop} onChange={(e) => setFilterLoop(e.target.value)} className="px-3 py-1.5 text-sm" style={selectStyle}>
            <option value="">全部循環</option>
            {grid.loops.map((l) => (
              <option key={l} value={l}>
                {l} — {LOOP_LABELS[l]}
              </option>
            ))}
          </select>
        )}
        <span className="text-xs font-mono" style={{ color: "var(--text-subtle)" }}>
          {filtered.length} / {scoped.length}
        </span>
      </div>

      {/* Grouped skill cards, by folder */}
      <div className="mt-6 space-y-6">
        {grouped.map(([folder, list]) => (
          <section key={folder}>
            <h2 className="mb-3 flex items-baseline gap-2" style={{ fontSize: 18, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.01em" }}>
              <span className="font-mono">{folder}</span>
              {FOLDER_LABELS[folder] && (
                <span className="text-sm" style={{ color: "var(--text-muted)", fontWeight: 400 }}>
                  {FOLDER_LABELS[folder]}
                </span>
              )}
              <span className="font-mono tabular-nums" style={{ color: "var(--text-muted)", fontSize: 13, fontWeight: 400 }}>
                ({list.length})
              </span>
            </h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {list.map((skill) => {
                const uses = (usage[skill.name] ?? []).reduce((s, d) => s + d.count, 0);
                return (
                  <Link
                    key={skill.name}
                    href={`/skills/${encodeURIComponent(skill.name)}`}
                    className="transition-shadow"
                    style={{ ...cardStyle, borderLeft: "3px solid var(--accent-soft)", display: "block" }}
                  >
                    <div className="p-4">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="text-sm" style={{ color: "var(--text)", fontWeight: 500, fontFamily: "var(--font-mono)" }}>
                          {skill.name}
                        </h3>
                        <LifecycleBadge lifecycle={skill.lifecycle} />
                      </div>
                      {skill.summary && (
                        <p className="mt-2 text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                          {skill.summary}
                        </p>
                      )}
                      <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs font-mono tabular-nums" style={{ color: "var(--text-subtle)" }}>
                        {skill.loop && <Tag tone="accent">{skill.loop}</Tag>}
                        {skill.pdca && <Tag>{skill.pdca}</Tag>}
                        {skill.source !== "rivendell" && <Tag>{SOURCE_LABELS[skill.source] ?? skill.source}</Tag>}
                        <span className="ml-auto">{skill.line_count} lines</span>
                        {uses > 0 && <span style={{ color: "var(--accent)" }}>{uses}×</span>}
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </section>
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="mt-4 text-sm" style={{ color: "var(--text-muted)" }}>
          沒有符合條件的 skill
        </p>
      )}
    </div>
  );
}
