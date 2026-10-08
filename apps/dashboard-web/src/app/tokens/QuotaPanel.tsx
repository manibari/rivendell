"use client";

import { Fragment, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Source = "claude" | "codex";

interface QuotaReading {
  used_percent: number;
  remaining_percent: number;
  resets_at: number;
  read_at: number;
  reset_since_read: boolean;
}

interface Advice {
  status: "usable" | "blocked" | "unknown";
  rank: number | null;
  blocked_by?: "week" | "session" | null;
  blocked_until?: number | null;
  rate_per_hour?: number | null;
  exhaust_at?: number | null;
  pace_per_day?: number | null;
}

interface QuotaAccount {
  source: Source;
  account_id: string | null;
  label: string | null;
  plan: string;
  first_seen: number;
  last_seen: number;
  quota: Record<string, QuotaReading>; // key = window length in minutes
  advice: Advice;
  week_estimate: WeekEstimate | null;
}

interface ModelEstimate {
  model: string;
  per_percent: number;
  week_tokens: number;
  steps: number;
  weeks: number;
  rough: boolean;
}

interface WeekEstimate {
  per_percent: number;
  week_tokens: number;
  basis: "steps" | "average" | "model";
  weeks: number;
  rough: boolean;
  model: string | null;
  by_model: ModelEstimate[];
}

interface QuotaWindow {
  source: Source;
  account_id: string;
  label: string | null;
  window_min: number;
  resets_at: number;
  reset_exact: number | null;
  plan: string;
  first_at: number;
  last_at: number;
  used_from: number;
  used_to: number;
  readings: number;
  input: number;
  output: number;
  cache_read: number;
  cache_create: number;
  tokens: number;
  tokens_per_percent: number | null;
  step_tokens_per_percent: number | null;
  clean_steps: number;
  local_percent: number | null;
  other_percent: number | null;
  main_model: string | null;
}

interface QuotaData {
  generated_at: number;
  computed_at: number | null;
  error: string | null;
  claude_log_present: boolean;
  hidden_idle_accounts: number;
  accounts: QuotaAccount[];
  windows: QuotaWindow[];
}

const WEEK = "10080";
const FIVE_HOUR = "300";
const SOURCE_NAME = { claude: "Claude Code", codex: "Codex" } as const;
const TEXT_SUBTLE = "#9ca3af";
const POLL_MS = 60000;

const pad = (n: number) => String(n).padStart(2, "0");
const stamp = (epoch: number) => {
  const d = new Date(epoch * 1000);
  return `${pad(d.getMonth() + 1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};
const millions = (v: number) => `${(v / 1e6).toFixed(1)}M`;
// Model display name: drop the claude- prefix; no model read as unknown.
const modelName = (model: string | null) => {
  const m = model ?? "";
  if (!m) return "未知";
  return m.startsWith("claude-") ? m.slice("claude-".length) : m;
};
// One line under the weekly figure: the model the number is for, or a note
// when it mixes models.
const estModelLine = (est: WeekEstimate) => {
  if (est.basis === "model") return modelName(est.model);
  if (est.model) return "混用估算";
  return "";
};
const who = (source: Source, label: string | null, id: string | null) =>
  `${SOURCE_NAME[source]} · ${label ?? (id ? id.slice(0, 8) : "帳號未判讀")}`;

const cell = "px-3 py-2 font-mono tabular-nums";

// Display order only: per source, ranked first, then blocked (soonest free), then unknown.
const STATUS_ORDER = { usable: 0, blocked: 1, unknown: 2 } as const;
const byAdvice = (x: QuotaAccount, y: QuotaAccount) =>
  x.source.localeCompare(y.source)
  || STATUS_ORDER[x.advice.status] - STATUS_ORDER[y.advice.status]
  || (x.advice.rank ?? 0) - (y.advice.rank ?? 0)
  || (x.advice.blocked_until ?? 0) - (y.advice.blocked_until ?? 0);
const head = (text: string, align: "left" | "right" = "left") => (
  <th className={`px-3 py-2 text-${align}`} style={{ fontSize: 11, fontWeight: 500, color: "var(--text-muted)" }}>
    {text}
  </th>
);

// Used up = the quota ran out and has not reset since; the whole reading turns red.
const usedUp = (q?: QuotaReading) => !!q && !q.reset_since_read && q.remaining_percent <= 0;
const ERR = "var(--status-err)";

const BLOCKED_BY = { week: "週額度用完", session: "session 用完" } as const;

// The backend ranks; this only words it. Rank 1 per source is the one to use now.
function AdviceBadge({ a }: { a: QuotaAccount }) {
  const adv = a.advice;
  if (adv.status === "usable" && adv.rank === 1) {
    return <span style={{ color: "var(--accent)", fontWeight: 600, whiteSpace: "nowrap" }}>優先用</span>;
  }
  if (adv.status === "usable") {
    return <span style={{ color: "var(--text-muted)", whiteSpace: "nowrap" }}>第 {adv.rank} 順位</span>;
  }
  if (adv.status === "blocked" && adv.blocked_until) {
    return (
      <span style={{ color: "var(--status-warn)", whiteSpace: "nowrap" }}>
        等到 {stamp(adv.blocked_until)}
        <br />
        <span style={{ fontSize: 11 }}>{BLOCKED_BY[adv.blocked_by ?? "week"]}</span>
      </span>
    );
  }
  return <span style={{ color: TEXT_SUBTLE }}>—</span>;
}

function Outlook({ adv }: { adv: Advice }) {
  if (adv.status === "unknown") return null;
  if (adv.exhaust_at) {
    return (
      <div style={{ fontSize: 11, color: "var(--status-warn)", whiteSpace: "nowrap" }}>
        照目前速度 {stamp(adv.exhaust_at)} 用完
        {adv.pace_per_day ? `；撐到重置每天 ${adv.pace_per_day}%` : ""}
      </div>
    );
  }
  if (adv.pace_per_day && adv.status === "usable") {
    return <div style={{ fontSize: 11, color: TEXT_SUBTLE, whiteSpace: "nowrap" }}>撐到重置每天可用 {adv.pace_per_day}%</div>;
  }
  return null;
}

function Summary({ accounts }: { accounts: QuotaAccount[] }) {
  const lines = (["claude", "codex"] as Source[]).map((source) => {
    const mine = accounts.filter((a) => a.source === source && a.advice.status !== "unknown");
    if (mine.length === 0) return null;
    const first = mine.find((a) => a.advice.rank === 1);
    if (first) {
      return `${SOURCE_NAME[source]}：用 ${first.label ?? first.account_id?.slice(0, 8)}`;
    }
    const next = mine
      .filter((a) => a.advice.blocked_until)
      .sort((x, y) => (x.advice.blocked_until ?? 0) - (y.advice.blocked_until ?? 0))[0];
    return next
      ? `${SOURCE_NAME[source]}：全部被擋住，最早 ${stamp(next.advice.blocked_until!)} ${next.label ?? ""} 可用`
      : null;
  }).filter(Boolean);
  if (lines.length === 0) return null;
  return (
    <p className="mb-2" style={{ fontSize: 13, color: "var(--text)" }}>
      <span style={{ fontWeight: 600 }}>建議：</span>{lines.join("　·　")}
    </p>
  );
}

function RemainingBar({ q }: { q: QuotaReading }) {
  const color = q.remaining_percent <= 10 ? "var(--status-err)"
    : q.remaining_percent <= 30 ? "var(--status-warn)" : "var(--accent)";
  return (
    <span className="inline-flex items-center gap-2"
      style={{ whiteSpace: "nowrap", ...(usedUp(q) ? { color: ERR, fontWeight: 600 } : {}) }}>
      <span style={{ display: "inline-block", width: 80, height: 6, background: "var(--border)", borderRadius: 3 }}>
        <span style={{
          display: "block", width: `${Math.min(100, q.remaining_percent)}%`, height: 6,
          background: color, borderRadius: 3,
        }} />
      </span>
      {q.remaining_percent.toFixed(0)}%{usedUp(q) && " 已用完"}
    </span>
  );
}

export default function QuotaPanel() {
  const [data, setData] = useState<QuotaData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    let alive = true;
    const load = () => {
      if (document.hidden) return;
      apiFetch<QuotaData>("/api/tokens/quota")
        .then((d) => { if (alive) { setData(d); setErr(null); } })
        .catch((e) => alive && setErr(e.message));
    };
    load();
    const timer = setInterval(load, POLL_MS);
    document.addEventListener("visibilitychange", load);
    return () => {
      alive = false;
      clearInterval(timer);
      document.removeEventListener("visibilitychange", load);
    };
  }, []);

  const weeklyFor = (a: QuotaAccount) =>
    (data?.windows ?? []).filter((w) => w.source === a.source
      && (w.account_id || null) === (a.account_id || null)
      && String(w.window_min) === WEEK && w.used_to > w.used_from);

  const toggleWeek = (key: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });

  return (
    <section className="mt-8">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h2 style={{ fontSize: 18, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.01em" }}>
          帳號與額度
        </h2>
        <span style={{ fontSize: 11, color: TEXT_SUBTLE, fontFamily: "var(--font-mono)" }}>
          每分鐘重算
          {data?.computed_at ? ` · 上次 ${stamp(data.computed_at)}` : " · 計算中"}
        </span>
      </div>

      {err && <p style={{ fontSize: 12, color: "var(--status-err)" }}>讀不到額度：{err}</p>}
      {data?.error && <p style={{ fontSize: 12, color: "var(--status-err)" }}>重算失敗：{data.error}</p>}

      {data && <Summary accounts={data.accounts} />}

      {data && (
        <div className="overflow-x-auto rounded" style={{ border: "1px solid var(--border)", background: "var(--surface)" }}>
          <table className="w-full" style={{ fontSize: 12 }}>
            <thead style={{ borderBottom: "1px solid var(--border)" }}>
              <tr>
                {head("建議")}
                {head("帳號")}
                {head("方案")}
                {head("首次 / 最後使用")}
                {head("週額度已用", "right")}
                {head("週額度餘量")}
                {head("用滿一週約", "right")}
                {head("額度更新（重置）")}
                {head("目前 session（5 小時）", "right")}
                {head("session 重置")}
                {head("讀數時間")}
              </tr>
            </thead>
            <tbody>
              {[...data.accounts].sort(byAdvice).map((a) => {
                const w = a.quota[WEEK];
                const h = a.quota[FIVE_HOUR];
                const red = usedUp(w) ? { color: ERR, fontWeight: 600 } : undefined;
                const weeks = weeklyFor(a);
                const key = `${a.source}:${a.account_id}`;
                const open = expanded.has(key);
                const est = a.week_estimate;
                const estLine = est ? estModelLine(est) : "";
                return (
                  <Fragment key={key}>
                  <tr style={{ borderTop: "1px solid var(--border)", color: "var(--text)" }}>
                    <td className={cell}><AdviceBadge a={a} /></td>
                    <td className={cell}>
                      {who(a.source, a.label, a.account_id)}
                      {weeks.length > 0 && (
                        <button
                          type="button"
                          onClick={() => toggleWeek(key)}
                          style={{ marginLeft: 8, fontSize: 11, color: "var(--text-muted)", background: "none", border: "1px solid var(--border)", borderRadius: 4, padding: "1px 6px", cursor: "pointer" }}>
                          {open ? "▾ 收起" : "▸ 細節"}
                        </button>
                      )}
                    </td>
                    <td className={cell}>{a.plan || "—"}</td>
                    <td className={cell} style={{ whiteSpace: "nowrap" }}>
                      {stamp(a.first_seen)}
                      <br />→ {stamp(a.last_seen)}
                    </td>
                    <td className={`${cell} text-right`} style={red}>{w ? `${w.used_percent.toFixed(0)}%` : "—"}</td>
                    <td className={cell}>
                      {w ? <RemainingBar q={w} /> : "無讀數"}
                      <Outlook adv={a.advice} />
                    </td>
                    <td className={`${cell} text-right`} style={{ whiteSpace: "nowrap" }}>
                      {est
                        ? <>{millions(est.week_tokens)}
                            <br />
                            <span style={{ fontSize: 11, color: TEXT_SUBTLE }}>
                              每 1% 約 {(est.per_percent / 1e6).toFixed(1)}M{est.rough && "（粗估）"}
                              {estLine && <><br />{estLine}</>}
                            </span></>
                        : "—"}
                    </td>
                    <td className={cell} style={red}>
                      {w
                        ? w.reset_since_read
                          ? <>已重置<br /><span style={{ color: TEXT_SUBTLE }}>（原 {stamp(w.resets_at)}）</span></>
                          : stamp(w.resets_at)
                        : "—"}
                    </td>
                    <td className={`${cell} text-right`} style={{ whiteSpace: "nowrap", ...(usedUp(h) ? { color: ERR, fontWeight: 600 } : {}) }}>
                      {h ? `已用 ${h.used_percent.toFixed(0)}% · 剩 ${h.remaining_percent.toFixed(0)}%` : "—"}
                    </td>
                    <td className={cell} style={usedUp(h) ? { color: ERR, fontWeight: 600 } : undefined}>
                      {h
                        ? h.reset_since_read
                          ? <><span style={{ whiteSpace: "nowrap" }}>已重置 · 下次使用起算 5 小時</span><br /><span style={{ color: TEXT_SUBTLE }}>（原 {stamp(h.resets_at)}）</span></>
                          : stamp(h.resets_at)
                        : "—"}
                    </td>
                    <td className={cell} style={{ color: TEXT_SUBTLE }}>{w ? stamp(w.read_at) : "—"}</td>
                  </tr>
                  {open && (
                    <tr style={{ color: "var(--text)" }}>
                      <td colSpan={11} style={{ padding: "0 12px 12px", background: "var(--row-hover, rgba(125,125,125,0.06))" }}>
                        {est && est.by_model.length >= 2 && (
                          <div style={{ fontSize: 11, color: TEXT_SUBTLE, marginBottom: 6, fontFamily: "monospace" }}>
                            各模型：{est.by_model.map((e) =>
                              `${modelName(e.model)} 每 1% 約 ${millions(e.per_percent)}（用滿約 ${millions(e.week_tokens)}，${e.steps} 段）${e.rough ? "粗估" : ""}`
                            ).join(" · ")}
                          </div>
                        )}
                        <table className="w-full" style={{ fontSize: 11 }}>
                          <thead style={{ borderBottom: "1px solid var(--border)" }}>
                            <tr>
                              {head("週期重置")}
                              {head("額度", "right")}
                              {head("本機用量", "right")}
                              {head("每 1% 約", "right")}
                              {head("其他電腦約", "right")}
                              {head("主要模型")}
                            </tr>
                          </thead>
                          <tbody>
                            {weeks.map((dw) => (
                              <tr key={`${dw.source}:${dw.account_id}:${dw.resets_at}`}>
                                <td className={cell}>{stamp(dw.reset_exact ?? dw.resets_at)}</td>
                                <td className={`${cell} text-right`}>{dw.used_from.toFixed(0)}% → {dw.used_to.toFixed(0)}%</td>
                                <td className={`${cell} text-right`}>{millions(dw.tokens)}</td>
                                <td className={`${cell} text-right`}>
                                  {dw.step_tokens_per_percent != null
                                    ? millions(dw.step_tokens_per_percent)
                                    : dw.tokens_per_percent != null
                                      ? <span style={{ color: TEXT_SUBTLE }}>{millions(dw.tokens_per_percent)} 樣本少</span>
                                      : "—"}
                                </td>
                                <td className={`${cell} text-right`}>{dw.other_percent != null ? `${dw.other_percent.toFixed(0)}%` : "—"}</td>
                                <td className={cell}>{dw.main_model ? modelName(dw.main_model) : "—"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </td>
                    </tr>
                  )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="mt-2" style={{ fontSize: 11, color: TEXT_SUBTLE, fontFamily: "monospace" }}>
        額度是官方讀數：Codex 取自 rollout 的 rate_limits；Claude 取自 statusLine（token-quota-log），只有裝好之後才有紀錄。
        「用滿一週約」＝每 1% 額度本機約用多少 token × 100，取各週中位數；資料不到 2 週、額度動不到 20%，或只能用整週平均算的，標「粗估」。點「細節」看每週數字。
        換模型會改變每 1% 的 token 數（Opus 比 Sonnet 少很多），所以只用同一個模型為主的 1% 段來估；混用的段不算進各模型。
        「建議」：同一個來源裡，先用週額度最快重置、還有剩的帳號（重置後沒用完的就作廢）；被週額度或 5 小時 session 擋住的排後面。
        超過 30 天沒用的帳號不列出{data?.hidden_idle_accounts ? `（目前隱藏 ${data.hidden_idle_accounts} 個）` : ""}，資料保留，再用到會自動出現。
        {data && !data.claude_log_present && " 目前還沒有 Claude 額度紀錄：執行 sk deploy 與 sk hooks install 後重開 Claude Code。"}
      </p>
    </section>
  );
}
