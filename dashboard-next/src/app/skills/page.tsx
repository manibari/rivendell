"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiFetch, type SkillInfo, type SkillUsage } from "@/lib/api";
import MetricsRow from "@/components/MetricsRow";
import {
  Treemap,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
} from "recharts";

// DESIGN.md says: differentiate by label, not color. Categories all get the
// same neutral chip; treemap uses sequential green shades for visual
// distinction without a rainbow palette.
const SEQ_GREENS = [
  "#2d4a3e",
  "#3e5c4f",
  "#4f6f5f",
  "#5b7a6a",
  "#7a9489",
  "#a3bbb1",
  "#c8d4d0",
  "#dfe7e3",
];

const ACCENT = "#2d4a3e";
const ACCENT_SOFT = "#5b7a6a";
const SURFACE = "#ffffff";
const SURFACE_2 = "#f3f4f6";
const BORDER = "#e5e7eb";
const TEXT_SUBTLE = "#9ca3af";

// Lifecycle: 3 monochrome shades — manual=accent, hook=accent-soft, agent=status-warn
const LIFECYCLE_COLORS: Record<string, string> = {
  manual: ACCENT,
  hook: ACCENT_SOFT,
  agent: "#b8772f", // sepia accent for the third tier
  unknown: TEXT_SUBTLE,
};

function LifecycleBadge({ lifecycle }: { lifecycle: string }) {
  const color = LIFECYCLE_COLORS[lifecycle] || LIFECYCLE_COLORS.unknown;
  return (
    <span
      className="inline-block px-2 py-0.5 text-xs font-medium font-mono"
      style={{
        borderRadius: 99,
        background: SURFACE_2,
        color,
        border: `1px solid ${color}`,
        fontSize: 10,
      }}
    >
      {lifecycle}
    </span>
  );
}

// Treemap custom content — recolored
function TreemapContent(props: {
  x: number;
  y: number;
  width: number;
  height: number;
  name: string;
  color: string;
}) {
  const { x, y, width, height, name, color } = props;
  if (width < 40 || height < 20) return null;
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        rx={4}
        fill={color}
        stroke={SURFACE}
        strokeWidth={2}
        style={{ opacity: 0.95 }}
      />
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

const tooltipStyle: React.CSSProperties = {
  background: SURFACE,
  border: `1px solid ${BORDER}`,
  borderRadius: 4,
  fontFamily: "monospace",
  fontSize: 12,
};

export default function SkillsPage() {
  const [skills, setSkills] = useState<SkillInfo[] | null>(null);
  const [usage, setUsage] = useState<SkillUsage>({});
  const [err, setErr] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("");

  useEffect(() => {
    apiFetch<SkillInfo[]>("/api/skills")
      .then(setSkills)
      .catch((e) => setErr(e.message));
    apiFetch<SkillUsage>("/api/skills/usage")
      .then(setUsage)
      .catch(() => {});
  }, []);

  const categories = useMemo(() => {
    if (!skills) return [];
    const cats = new Set(skills.map((s) => s.category).filter(Boolean));
    return Array.from(cats).sort();
  }, [skills]);

  const filtered = useMemo(() => {
    if (!skills) return [];
    return skills.filter((s) => {
      if (filterCategory && s.category !== filterCategory) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          s.name.toLowerCase().includes(q) ||
          s.summary.toLowerCase().includes(q) ||
          s.category.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [skills, search, filterCategory]);

  const grouped = useMemo(() => {
    const map = new Map<string, SkillInfo[]>();
    for (const s of filtered) {
      const cat = s.category || "未分類";
      if (!map.has(cat)) map.set(cat, []);
      map.get(cat)!.push(s);
    }
    return Array.from(map.entries()).sort(([a], [b]) => {
      if (a === "未分類") return 1;
      if (b === "未分類") return -1;
      return a.localeCompare(b);
    });
  }, [filtered]);

  const treemapData = useMemo(() => {
    if (!skills) return [];
    const counts = new Map<string, number>();
    for (const s of skills) {
      const cat = s.category || "未分類";
      counts.set(cat, (counts.get(cat) || 0) + 1);
    }
    return Array.from(counts.entries())
      .map(([name, size], i) => ({
        name: `${name} (${size})`,
        size,
        color: SEQ_GREENS[i % SEQ_GREENS.length],
      }))
      .sort((a, b) => b.size - a.size);
  }, [skills]);

  const lifecycleData = useMemo(() => {
    if (!skills) return [];
    const counts = new Map<string, number>();
    for (const s of skills) {
      const lc = s.lifecycle || "unknown";
      counts.set(lc, (counts.get(lc) || 0) + 1);
    }
    return Array.from(counts.entries()).map(([name, value]) => ({
      name,
      value,
    }));
  }, [skills]);

  const topSkills = useMemo(() => {
    return Object.entries(usage)
      .map(([name, days]) => ({
        name,
        count: days.reduce((s, d) => s + d.count, 0),
      }))
      .filter((s) => s.count > 0)
      .sort((a, b) => b.count - a.count)
      .slice(0, 12);
  }, [usage]);

  const metrics = useMemo(() => {
    if (!skills) return null;
    const invocableCount = skills.filter((s) => s.invocable).length;
    const avgLines = Math.round(
      skills.reduce((sum, s) => sum + s.line_count, 0) / skills.length
    );
    return {
      total: skills.length,
      categories:
        categories.length + (skills.some((s) => !s.category) ? 1 : 0),
      invocableRate: `${Math.round(
        (invocableCount / skills.length) * 100
      )}%`,
      avgLines,
    };
  }, [skills, categories]);

  if (err)
    return <p style={{ color: "var(--status-err)" }}>Error: {err}</p>;
  if (!skills || !metrics)
    return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;

  const sectionH2: React.CSSProperties = {
    fontSize: 18,
    fontWeight: 500,
    color: "var(--text)",
    letterSpacing: "-0.01em",
  };

  const cardStyle: React.CSSProperties = {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius-md)",
  };

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
        Skill 總覽
      </h1>

      <MetricsRow
        metrics={[
          { label: "總數", value: metrics.total },
          { label: "分類", value: metrics.categories },
          { label: "可呼叫", value: metrics.invocableRate },
          { label: "平均行數", value: metrics.avgLines },
        ]}
      />

      {/* Charts row */}
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="p-4" style={cardStyle}>
          <h2 className="mb-3 text-sm" style={{ color: "var(--text)", fontWeight: 500 }}>
            Category Map
          </h2>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height={224}>
              <Treemap
                data={treemapData}
                dataKey="size"
                aspectRatio={4 / 3}
                content={
                  <TreemapContent
                    x={0}
                    y={0}
                    width={0}
                    height={0}
                    name=""
                    color=""
                  />
                }
              />
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-4" style={cardStyle}>
          <h2 className="mb-3 text-sm" style={{ color: "var(--text)", fontWeight: 500 }}>
            Lifecycle 分佈
          </h2>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height={224}>
              <PieChart>
                <Pie
                  data={lifecycleData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius="45%"
                  outerRadius="75%"
                  paddingAngle={3}
                  label={({
                    name,
                    value,
                  }: {
                    name?: string;
                    value?: number;
                  }) => `${name ?? ""} (${value ?? 0})`}
                >
                  {lifecycleData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={LIFECYCLE_COLORS[entry.name] || TEXT_SUBTLE}
                    />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Top skills usage chart */}
      {topSkills.length > 0 && (
        <div className="mt-4 p-4" style={cardStyle}>
          <h2 className="mb-3 text-sm" style={{ color: "var(--text)", fontWeight: 500 }}>
            最常使用（累計呼叫次數）
          </h2>
          <div style={{ height: topSkills.length * 28 + 16 }}>
            <ResponsiveContainer
              width="100%"
              height={topSkills.length * 28 + 16}
            >
              <BarChart
                data={topSkills}
                layout="vertical"
                margin={{ top: 0, right: 48, left: 0, bottom: 0 }}
              >
                <XAxis
                  type="number"
                  tick={{ fontSize: 10, fill: TEXT_SUBTLE, fontFamily: "monospace" }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={160}
                  tick={{ fontSize: 11, fill: "var(--text-muted)", fontFamily: "monospace" }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(v) => [v, "呼叫次數"]}
                  cursor={{ fill: SURFACE_2 }}
                />
                <Bar
                  dataKey="count"
                  fill={ACCENT}
                  radius={[0, 3, 3, 0]}
                  label={{
                    position: "right",
                    fontSize: 10,
                    fill: TEXT_SUBTLE,
                    fontFamily: "monospace",
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p
            className="mt-3 text-xs leading-relaxed"
            style={{ color: "var(--text-muted)" }}
          >
            此計數系統性低估真實使用量。只計入兩種訊號：(1) Claude 透過{" "}
            <code
              className="font-mono"
              style={{ color: "var(--text)" }}
            >
              Read
            </code>{" "}
            工具讀 SKILL.md，(2) 使用者透過{" "}
            <code
              className="font-mono"
              style={{ color: "var(--text)" }}
            >
              Skill
            </code>{" "}
            工具呼叫。最常見的 description-match auto-trigger 與 Hook
            觸發路徑都不留 tool call 紀錄，因此完全看不見。實際使用量通常是這裡顯示的 3-5 倍。
          </p>
        </div>
      )}

      {/* Search + filter */}
      <div className="mt-6 flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="搜尋 skill..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-1.5 text-sm"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-sm)",
            color: "var(--text)",
            fontFamily: "var(--font-mono)",
          }}
        />
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="px-3 py-1.5 text-sm"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-sm)",
            color: "var(--text)",
            fontFamily: "var(--font-mono)",
          }}
        >
          <option value="">全部分類</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Grouped skill cards */}
      <div className="mt-6 space-y-6">
        {grouped.map(([category, catSkills]) => (
          <section key={category}>
            <h2
              className="mb-3 flex items-center gap-2"
              style={sectionH2}
            >
              {category}
              <span
                className="font-mono tabular-nums"
                style={{ color: "var(--text-muted)", fontSize: 13, fontWeight: 400 }}
              >
                ({catSkills.length})
              </span>
            </h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {catSkills.map((skill) => {
                const skillUsage = usage[skill.name] ?? [];
                const uses30 = skillUsage.reduce(
                  (s, d) => s + d.count,
                  0
                );
                return (
                  <Link
                    key={skill.name}
                    href={`/skills/${encodeURIComponent(skill.name)}`}
                    className="transition-shadow"
                    style={{
                      background: "var(--surface)",
                      border: "1px solid var(--border)",
                      borderLeft: "3px solid var(--accent-soft)",
                      borderRadius: "var(--radius-md)",
                      display: "block",
                    }}
                  >
                    <div className="p-4">
                      <div className="flex items-start justify-between gap-2">
                        <h3
                          className="text-sm"
                          style={{
                            color: "var(--text)",
                            fontWeight: 500,
                            fontFamily: "var(--font-mono)",
                          }}
                        >
                          {skill.name}
                        </h3>
                        <LifecycleBadge lifecycle={skill.lifecycle} />
                      </div>
                      {skill.summary && (
                        <p
                          className="mt-2 text-xs leading-relaxed"
                          style={{ color: "var(--text-muted)" }}
                        >
                          {skill.summary}
                        </p>
                      )}
                      <div
                        className="mt-3 flex items-center gap-3 text-xs font-mono tabular-nums"
                        style={{ color: "var(--text-subtle)" }}
                      >
                        <span>{skill.line_count} lines</span>
                        {uses30 > 0 && (
                          <span style={{ color: "var(--accent)" }}>
                            {uses30}× / 30d
                          </span>
                        )}
                        {skill.invocable && (
                          <span
                            className="px-1.5 py-0.5"
                            style={{
                              background: "var(--accent-bg)",
                              color: "var(--accent)",
                              borderRadius: 2,
                            }}
                          >
                            invocable
                          </span>
                        )}
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
