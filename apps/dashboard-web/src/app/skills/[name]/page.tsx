"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch, type SkillDetail, type SkillUsage } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { ChevronLeft, Zap } from "lucide-react";

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

function LifecycleBadge({ lifecycle }: { lifecycle: string }) {
  const color = LIFECYCLE_COLORS[lifecycle] ?? LIFECYCLE_COLORS.unknown;
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

export default function SkillDetailPage() {
  const params = useParams();
  const name = decodeURIComponent(params.name as string);

  const [detail, setDetail] = useState<SkillDetail | null>(null);
  const [usageDays, setUsageDays] = useState<
    { date: string; count: number }[]
  >([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiFetch<SkillDetail>(`/api/skills/${encodeURIComponent(name)}`),
      apiFetch<SkillUsage>("/api/skills/usage"),
    ])
      .then(([d, usage]) => {
        setDetail(d);
        setUsageDays(usage[name] ?? []);
      })
      .catch((e: Error) => setErr(e.message));
  }, [name]);

  const chartData = useMemo(() => {
    const today = new Date();
    const map: Record<string, number> = {};
    for (const u of usageDays) map[u.date] = u.count;
    return Array.from({ length: 30 }, (_, i) => {
      const d = new Date(today);
      d.setDate(d.getDate() - (29 - i));
      const iso = d.toISOString().slice(0, 10);
      return { date: iso.slice(5), count: map[iso] ?? 0 };
    });
  }, [usageDays]);

  const total7 = useMemo(
    () => chartData.slice(-7).reduce((s, d) => s + d.count, 0),
    [chartData]
  );
  const total30 = useMemo(
    () => chartData.reduce((s, d) => s + d.count, 0),
    [chartData]
  );
  const totalAll = useMemo(
    () => usageDays.reduce((s, d) => s + d.count, 0),
    [usageDays]
  );

  if (err)
    return <p style={{ color: "var(--status-err)" }}>Error: {err}</p>;
  if (!detail)
    return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;

  const body = detail.content
    .replace(/^---\s*\n[\s\S]*?\n---\s*\n?/, "")
    .trim();

  return (
    <div className="max-w-3xl">
      <Link
        href="/skills"
        className="mb-4 inline-flex items-center gap-1 text-sm transition-colors"
        style={{ color: "var(--text-muted)" }}
        onMouseEnter={(e) =>
          (e.currentTarget.style.color = "var(--text)")
        }
        onMouseLeave={(e) =>
          (e.currentTarget.style.color = "var(--text-muted)")
        }
      >
        <ChevronLeft size={16} />
        Skills
      </Link>

      <div className="mt-2 flex flex-wrap items-center gap-2">
        <h1
          className="tracking-tight"
          style={{
            fontSize: 28,
            fontWeight: 500,
            color: "var(--text)",
            letterSpacing: "-0.02em",
            fontFamily: "var(--font-mono)",
          }}
        >
          {name}
        </h1>
        {detail.lifecycle && (
          <LifecycleBadge lifecycle={detail.lifecycle} />
        )}
        {detail.category && (
          <span
            className="px-2 py-0.5 text-xs font-mono"
            style={{
              borderRadius: 99,
              background: "var(--surface-2)",
              color: "var(--text-muted)",
            }}
          >
            {detail.category}
          </span>
        )}
        {detail.invocable && (
          <span
            className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono"
            style={{
              borderRadius: 99,
              background: "var(--accent-bg)",
              color: "var(--accent)",
            }}
          >
            <Zap size={10} />
            invocable
          </span>
        )}
      </div>
      {detail.summary && (
        <p
          className="mt-2 text-sm"
          style={{ color: "var(--text-muted)" }}
        >
          {detail.summary}
        </p>
      )}

      {/* Usage metrics */}
      <div className="mt-6 grid grid-cols-3 gap-3">
        {[
          { label: "最近 7 天", value: total7 },
          { label: "最近 30 天", value: total30 },
          { label: "累計全部", value: totalAll },
        ].map(({ label, value }) => (
          <div key={label} className="p-4" style={cardStyle}>
            <p
              className="font-mono text-[10px] uppercase"
              style={{
                color: "var(--text-subtle)",
                letterSpacing: "0.1em",
              }}
            >
              {label}
            </p>
            <p
              className="mt-1 tabular-nums"
              style={{
                color: "var(--text)",
                fontSize: 24,
                fontWeight: 500,
                fontFamily: "var(--font-mono)",
              }}
            >
              {value}
            </p>
          </div>
        ))}
      </div>

      {/* Time series chart */}
      <div className="mt-4 p-4" style={cardStyle}>
        <h2
          className="mb-3 text-sm"
          style={{ color: "var(--text)", fontWeight: 500 }}
        >
          呼叫次數（近 30 天）
        </h2>
        <div className="h-36 w-full">
          <ResponsiveContainer width="100%" height={144}>
            <BarChart
              data={chartData}
              margin={{ top: 2, right: 4, left: -24, bottom: 0 }}
            >
              <XAxis
                dataKey="date"
                tick={{ fontSize: 9, fill: TEXT_SUBTLE, fontFamily: "monospace" }}
                interval={4}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 9, fill: TEXT_SUBTLE, fontFamily: "monospace" }}
                allowDecimals={false}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(v) => [v, "呼叫次數"]}
                labelFormatter={(l) => `日期：${l}`}
                cursor={{ fill: SURFACE_2 }}
              />
              <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                {chartData.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={entry.count > 0 ? ACCENT : BORDER}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* SKILL.md content */}
      <div className="mt-6 p-6" style={cardStyle}>
        <p
          className="mb-4 font-mono text-[10px] uppercase"
          style={{
            color: "var(--text-subtle)",
            letterSpacing: "0.12em",
          }}
        >
          SKILL.md
        </p>
        <div
          className="prose prose-sm max-w-none"
          style={{ color: "var(--text)" }}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{body}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
