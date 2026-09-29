"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

type Bucket = "minute" | "hour";
type Metric = "output" | "cache";
type Group = "account" | "model";

interface Cell {
  input: number;
  output: number;
  cache_read: number;
  cache_create: number;
  requests: number;
}

interface Part {
  source: "claude" | "codex";
  account: string | null;
  label: string | null;
  model: string;
  tokens: number;
  cache_tokens: number;
}

interface TimelineSeries {
  id: string;
  source: "claude" | "codex";
  account: string | null;
  label: string | null;
  model: string | null;
  totals: Cell;
  tokens_per_minute: number;
  breakdown: Part[];
}

interface TimelineData {
  bucket: Bucket;
  group: Group;
  span: number;
  generated_at: number;
  rate_window_seconds: number;
  account_log_from: number | null;
  series: TimelineSeries[];
  points: { t: number; series: Record<string, Cell> }[];
}

// One color per account or model (2026-09-29, Peter: 不同顏色看是哪一隻帳號). Forest green
// stays first; the rest are muted earth tones — still no blue / purple / pink.
const ACCOUNT_COLORS = ["#2d4a3e", "#b7791f", "#9a4a3a", "#475569", "#6b7a2a", "#8a6d5a"];
// A series keeps the color it first got for as long as the page is open, so a
// new account or model showing up never recolors the ones already on screen.
const assignedColors = new Map<string, string>();
const colorFor = (id: string) => {
  let color = assignedColors.get(id);
  if (!color) {
    const used = new Set(assignedColors.values());
    color = ACCOUNT_COLORS.find((c) => !used.has(c))
      ?? ACCOUNT_COLORS[assignedColors.size % ACCOUNT_COLORS.length];
    assignedColors.set(id, color);
  }
  return color;
};

const BORDER = "#e5e7eb";
const TEXT_SUBTLE = "#9ca3af";
const SURFACE = "#ffffff";

const SPANS: Record<Bucket, { value: number; label: string }[]> = {
  minute: [
    { value: 60, label: "1 小時" },
    { value: 180, label: "3 小時" },
    { value: 360, label: "6 小時" },
  ],
  hour: [
    { value: 24, label: "24 小時" },
    { value: 48, label: "48 小時" },
  ],
};
const POLL_MS: Record<Bucket, number> = { minute: 5000, hour: 30000 };

const SOURCE_NAME = { claude: "Claude Code", codex: "Codex" } as const;

const accountLabel = (p: { source: "claude" | "codex"; account: string | null; label: string | null }) =>
  `${SOURCE_NAME[p.source]} · ${p.label ?? (p.account ? p.account.slice(0, 8) : "帳號未判讀")}`;

const seriesLabel = (s: TimelineSeries) => s.model ?? accountLabel(s);

const partValue = (p: Part, metric: Metric) => (metric === "output" ? p.tokens : p.cache_tokens);

// "claude-opus-5-5 82% · claude-fable-5-1 18%" — what a series is made of.
const breakdownText = (s: TimelineSeries, metric: Metric) => {
  const total = s.breakdown.reduce((sum, p) => sum + partValue(p, metric), 0);
  if (total === 0) return "";
  return s.breakdown
    .filter((p) => partValue(p, metric) > 0)
    .map((p) => `${s.model ? accountLabel(p) : p.model} ${((partValue(p, metric) / total) * 100).toFixed(0)}%`)
    .join(" · ");
};

const cellValue = (c: Cell | undefined, metric: Metric) =>
  !c ? 0 : metric === "output" ? c.input + c.output : c.cache_read + c.cache_create;

const compact = (v: number) =>
  v >= 1e9 ? `${(v / 1e9).toFixed(1)}B`
    : v >= 1e6 ? `${(v / 1e6).toFixed(1)}M`
      : v >= 1e3 ? `${(v / 1e3).toFixed(0)}K`
        : `${v}`;

const pad = (n: number) => String(n).padStart(2, "0");
const clock = (t: number) => {
  const d = new Date(t * 1000);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
};
const dayClock = (t: number) => {
  const d = new Date(t * 1000);
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${clock(t)}`;
};

const toggleStyle = (active: boolean): React.CSSProperties => ({
  padding: "3px 10px",
  fontSize: 12,
  fontFamily: "var(--font-mono)",
  borderRadius: "var(--radius-sm)",
  border: `1px solid ${active ? "var(--accent)" : "var(--border)"}`,
  background: active ? "var(--accent)" : "var(--surface)",
  color: active ? "#ffffff" : "var(--text-muted)",
});

export default function LiveUsage() {
  const [bucket, setBucket] = useState<Bucket>("minute");
  const [span, setSpan] = useState(60);
  const [metric, setMetric] = useState<Metric>("output");
  const [group, setGroup] = useState<Group>("account");
  const [paused, setPaused] = useState(false);
  const [data, setData] = useState<TimelineData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = () => {
      if (document.hidden) return;
      apiFetch<TimelineData>(`/api/tokens/timeline?bucket=${bucket}&span=${span}&group=${group}`)
        .then((d) => {
          if (!alive) return;
          setData(d);
          setErr(null);
        })
        .catch((e) => alive && setErr(e.message));
    };
    load();
    if (paused) return () => { alive = false; };
    const timer = setInterval(load, POLL_MS[bucket]);
    document.addEventListener("visibilitychange", load);
    return () => {
      alive = false;
      clearInterval(timer);
      document.removeEventListener("visibilitychange", load);
    };
  }, [bucket, span, group, paused]);

  const colors = useMemo(() => {
    const ids = (data?.series ?? []).map((s) => s.id).sort();
    return Object.fromEntries(ids.map((id) => [id, colorFor(id)]));
  }, [data]);

  const rows = useMemo(
    () =>
      (data?.points ?? []).map((p) => {
        const row: Record<string, number> = { t: p.t };
        for (const s of data?.series ?? []) row[s.id] = cellValue(p.series[s.id], metric);
        return row;
      }),
    [data, metric],
  );

  const stale = data && (data.bucket !== bucket || data.group !== group);

  return (
    <section className="mt-8">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h2 style={{ fontSize: 18, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.01em" }}>
          即時用量
        </h2>
        <span style={{ fontSize: 11, color: TEXT_SUBTLE, fontFamily: "var(--font-mono)" }}>
          {paused ? "已暫停" : `每 ${POLL_MS[bucket] / 1000} 秒更新`}
          {data && ` · ${clock(data.generated_at)}:${pad(new Date(data.generated_at * 1000).getSeconds())}`}
        </span>
        <span className="ml-auto flex flex-wrap items-center gap-1">
          <button style={toggleStyle(group === "account")} onClick={() => setGroup("account")}>
            依帳號
          </button>
          <button style={toggleStyle(group === "model")} onClick={() => setGroup("model")}>
            依模型
          </button>
          <span style={{ width: 8 }} />
          {(["minute", "hour"] as Bucket[]).map((b) => (
            <button
              key={b}
              style={toggleStyle(bucket === b)}
              onClick={() => {
                setBucket(b);
                setSpan(SPANS[b][0].value);
              }}
            >
              {b === "minute" ? "每分鐘" : "每小時"}
            </button>
          ))}
          <span style={{ width: 8 }} />
          {SPANS[bucket].map((s) => (
            <button key={s.value} style={toggleStyle(span === s.value)} onClick={() => setSpan(s.value)}>
              {s.label}
            </button>
          ))}
          <span style={{ width: 8 }} />
          <button style={toggleStyle(metric === "output")} onClick={() => setMetric("output")}>
            產出 (in+out)
          </button>
          <button style={toggleStyle(metric === "cache")} onClick={() => setMetric("cache")}>
            Context 重讀
          </button>
          <span style={{ width: 8 }} />
          <button style={toggleStyle(false)} onClick={() => setPaused((p) => !p)}>
            {paused ? "繼續" : "暫停"}
          </button>
        </span>
      </div>

      {err && <p style={{ fontSize: 12, color: "var(--status-err)" }}>讀不到即時用量：{err}</p>}

      {data && data.series.length > 0 && (
        <div className="mb-2 flex flex-col gap-y-1" style={{ fontSize: 12, fontFamily: "var(--font-mono)" }}>
          {data.series.map((s) => (
            <span key={s.id} style={{ color: "var(--text)" }}>
              <span
                style={{
                  display: "inline-block", width: 10, height: 10, marginRight: 6,
                  background: colors[s.id], borderRadius: 2,
                }}
              />
              {seriesLabel(s)}
              <span style={{ color: "var(--text-muted)" }}>
                {" "}· 目前 {s.tokens_per_minute.toLocaleString()} tokens/分
                · 區間 {cellValue(s.totals, metric).toLocaleString()} · {s.totals.requests.toLocaleString()} 次請求
              </span>
              <span style={{ color: TEXT_SUBTLE }}>
                {breakdownText(s, metric) && `　${s.model ? "帳號" : "模型"}：${breakdownText(s, metric)}`}
              </span>
            </span>
          ))}
        </div>
      )}

      <div
        className="h-64 w-full"
        style={{
          border: "1px solid var(--border)", borderRadius: "var(--radius-md)",
          background: "var(--surface)", opacity: stale ? 0.5 : 1,
        }}
      >
        {data && data.series.length === 0 ? (
          <p className="p-4" style={{ fontSize: 12, color: "var(--text-muted)" }}>
            這段時間內沒有用量紀錄。
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={256}>
            <BarChart data={rows} margin={{ top: 16, right: 16, bottom: 8, left: 0 }} barCategoryGap={1}>
              <CartesianGrid stroke={BORDER} strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="t"
                tick={{ fontSize: 10, fill: TEXT_SUBTLE, fontFamily: "monospace" }}
                tickFormatter={clock}
                minTickGap={40}
                stroke={BORDER}
              />
              <YAxis
                tick={{ fontSize: 10, fill: TEXT_SUBTLE, fontFamily: "monospace" }}
                tickFormatter={compact}
                stroke={BORDER}
                width={48}
              />
              <Tooltip
                contentStyle={{
                  background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 4,
                  fontFamily: "var(--font-mono)", fontSize: 12,
                }}
                labelFormatter={(t) => dayClock(Number(t))}
                formatter={(value) => Number(value).toLocaleString()}
                cursor={{ fill: "var(--surface-2)" }}
              />
              <Legend wrapperStyle={{ fontSize: 11, fontFamily: "monospace" }} />
              {(data?.series ?? []).map((s) => (
                <Bar
                  key={s.id}
                  dataKey={s.id}
                  stackId="account"
                  fill={colors[s.id]}
                  name={seriesLabel(s)}
                  isAnimationActive={false}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      <p className="mt-2" style={{ fontSize: 11, color: TEXT_SUBTLE, fontFamily: "monospace" }}>
        「目前」＝最近 {(data?.rate_window_seconds ?? 300) / 60} 分鐘的平均。Claude Code 的用量紀錄沒有帳號欄位，帳號是照「當時登入的是誰」對回去的；
        {data?.account_log_from
          ? `登入紀錄從 ${dayClock(data.account_log_from)} 開始，更早的用量標「帳號未判讀」。`
          : "這段時間沒有登入紀錄，Claude Code 用量標「帳號未判讀」。"}
        Codex 帳號取自每個 session 自己的紀錄。
      </p>
    </section>
  );
}
