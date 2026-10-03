"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Source = "claude" | "codex";

interface QuotaReading {
  used_percent: number;
  remaining_percent: number;
  resets_at: number;
  read_at: number;
  reset_since_read: boolean;
}

interface QuotaAccount {
  source: Source;
  account_id: string | null;
  label: string | null;
  plan: string;
  first_seen: number;
  last_seen: number;
  quota: Record<string, QuotaReading>; // key = window length in minutes
}

interface QuotaWindow {
  source: Source;
  account_id: string;
  label: string | null;
  window_min: number;
  resets_at: number;
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
}

interface QuotaData {
  generated_at: number;
  computed_at: number | null;
  error: string | null;
  claude_log_present: boolean;
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
const who = (source: Source, label: string | null, id: string | null) =>
  `${SOURCE_NAME[source]} · ${label ?? (id ? id.slice(0, 8) : "帳號未判讀")}`;

const cell = "px-3 py-2 font-mono tabular-nums";
const head = (text: string, align: "left" | "right" = "left") => (
  <th className={`px-3 py-2 text-${align}`} style={{ fontSize: 11, fontWeight: 500, color: "var(--text-muted)" }}>
    {text}
  </th>
);

// Used up = the quota ran out and has not reset since; the whole reading turns red.
const usedUp = (q?: QuotaReading) => !!q && !q.reset_since_read && q.remaining_percent <= 0;
const ERR = "var(--status-err)";

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

  const weekly = (data?.windows ?? [])
    .filter((w) => String(w.window_min) === WEEK && w.used_to > w.used_from)
    .slice(0, 16);

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

      {data && (
        <div className="overflow-x-auto rounded" style={{ border: "1px solid var(--border)", background: "var(--surface)" }}>
          <table className="w-full" style={{ fontSize: 12 }}>
            <thead style={{ borderBottom: "1px solid var(--border)" }}>
              <tr>
                {head("帳號")}
                {head("方案")}
                {head("首次 / 最後使用")}
                {head("週額度已用", "right")}
                {head("週額度餘量")}
                {head("額度更新（重置）")}
                {head("5 小時餘量", "right")}
                {head("讀數時間")}
              </tr>
            </thead>
            <tbody>
              {data.accounts.map((a) => {
                const w = a.quota[WEEK];
                const h = a.quota[FIVE_HOUR];
                const red = usedUp(w) ? { color: ERR, fontWeight: 600 } : undefined;
                return (
                  <tr key={`${a.source}:${a.account_id}`} style={{ borderTop: "1px solid var(--border)", color: "var(--text)" }}>
                    <td className={cell}>{who(a.source, a.label, a.account_id)}</td>
                    <td className={cell}>{a.plan || "—"}</td>
                    <td className={cell}>{stamp(a.first_seen)} → {stamp(a.last_seen)}</td>
                    <td className={`${cell} text-right`} style={red}>{w ? `${w.used_percent.toFixed(0)}%` : "—"}</td>
                    <td className={cell}>{w ? <RemainingBar q={w} /> : "無讀數"}</td>
                    <td className={cell} style={red}>
                      {w ? stamp(w.resets_at) : "—"}
                      {w?.reset_since_read && <span style={{ color: TEXT_SUBTLE }}>（已重置，待新讀數）</span>}
                    </td>
                    <td className={`${cell} text-right`} style={usedUp(h) ? { color: ERR, fontWeight: 600 } : undefined}>
                      {h ? `${h.remaining_percent.toFixed(0)}%` : "—"}
                    </td>
                    <td className={cell} style={{ color: TEXT_SUBTLE }}>{w ? stamp(w.read_at) : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {weekly.length > 0 && (
        <>
          <h3 className="mt-6 mb-2" style={{ fontSize: 14, fontWeight: 500, color: "var(--text)" }}>
            每週額度 vs token（每個重置週期）
          </h3>
          <div className="overflow-x-auto rounded" style={{ border: "1px solid var(--border)", background: "var(--surface)" }}>
            <table className="w-full" style={{ fontSize: 12 }}>
              <thead style={{ borderBottom: "1px solid var(--border)" }}>
                <tr>
                  {head("帳號")}
                  {head("週期重置")}
                  {head("額度", "right")}
                  {head("總用量", "right")}
                  {head("快取重讀", "right")}
                  {head("輸出", "right")}
                  {head("每 1% 約", "right")}
                  {head("讀數", "right")}
                </tr>
              </thead>
              <tbody>
                {weekly.map((w) => (
                  <tr key={`${w.source}:${w.account_id}:${w.resets_at}`} style={{ borderTop: "1px solid var(--border)", color: "var(--text)" }}>
                    <td className={cell}>{who(w.source, w.label, w.account_id || null)}</td>
                    <td className={cell}>{stamp(w.resets_at)}</td>
                    <td className={`${cell} text-right`}>{w.used_from.toFixed(0)}% → {w.used_to.toFixed(0)}%</td>
                    <td className={`${cell} text-right`}>{millions(w.tokens)}</td>
                    <td className={`${cell} text-right`}>{millions(w.cache_read)}</td>
                    <td className={`${cell} text-right`}>{millions(w.output)}</td>
                    <td className={`${cell} text-right`}>{w.tokens_per_percent ? millions(w.tokens_per_percent) : "—"}</td>
                    <td className={`${cell} text-right`} style={{ color: TEXT_SUBTLE }}>{w.readings}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <p className="mt-2" style={{ fontSize: 11, color: TEXT_SUBTLE, fontFamily: "monospace" }}>
        額度是官方讀數：Codex 取自 rollout 的 rate_limits；Claude 取自 statusLine（token-quota-log），只有裝好之後才有紀錄。
        「每 1% 約」＝該週期第一筆到最後一筆讀數之間，本機記到的總用量 ÷ 額度上升的百分點；同帳號在別台機器或網頁用的部分本機看不到，會讓數字偏低。
        {data && !data.claude_log_present && " 目前還沒有 Claude 額度紀錄：執行 sk deploy 與 sk hooks install 後重開 Claude Code。"}
      </p>
    </section>
  );
}
