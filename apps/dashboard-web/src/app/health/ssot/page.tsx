"use client";

import { useEffect, useState } from "react";
import { apiFetch, type HealthData, type SsotDriftInfo } from "@/lib/api";
import StatusDot from "@/components/StatusDot";

function DriftList({
  title,
  hint,
  pairs,
}: {
  title: string;
  hint: string;
  pairs: { project: string; agent: string }[];
}) {
  return (
    <section className="mt-6">
      <h2
        className="mb-1"
        style={{ fontSize: 18, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.01em" }}
      >
        {title}
        <span className="ml-2 font-mono text-sm" style={{ color: "var(--text-subtle)" }}>
          {pairs.length}
        </span>
      </h2>
      <p className="mb-3 text-sm" style={{ color: "var(--text-muted)" }}>
        {hint}
      </p>
      {pairs.length === 0 ? (
        <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
          無
        </p>
      ) : (
        <div
          className="overflow-hidden"
          style={{ border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}
        >
          {pairs.map((p, i) => (
            <div
              key={`${p.project}/${p.agent}`}
              className="flex items-center gap-3 px-4 py-2 font-mono text-sm"
              style={{
                background: "var(--surface)",
                borderTop: i === 0 ? "none" : "1px solid var(--border)",
              }}
            >
              <span style={{ color: "var(--text-subtle)" }}>{p.project}</span>
              <span style={{ color: "var(--text-subtle)" }}>/</span>
              <span style={{ color: "var(--text)" }}>{p.agent}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default function SsotDriftPage() {
  const [ssot, setSsot] = useState<SsotDriftInfo | null>(null);
  const [checkedAt, setCheckedAt] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<HealthData>("/api/health")
      .then((d) => {
        setSsot(d.ssot_drift);
        setCheckedAt(d.checked_at);
      })
      .catch((e) => setErr(e.message));
  }, []);

  const drift = ssot ? ssot.total_drift : null;
  const dot = drift === null ? "idle" : drift < 0 ? "err" : drift === 0 ? "ok" : "warn";
  const label = drift === null ? "—" : drift < 0 ? "檢查失敗" : drift === 0 ? "一致" : `${drift} 筆漂移`;

  return (
    <div>
      <div className="mb-2 flex items-center gap-3">
        <h1
          className="tracking-tight"
          style={{ fontSize: 28, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.02em" }}
        >
          SSOT 漂移
        </h1>
        {ssot && <StatusDot status={dot} label={label} />}
      </div>

      <p className="mb-5 max-w-3xl text-sm" style={{ color: "var(--text-muted)", lineHeight: 1.55 }}>
        比對 <code className="font-mono">agents/agents.conf</code>（agent 身分 SSOT）與{" "}
        <code className="font-mono">~/.claude/projects.json</code>（專案 metadata SSOT）。兩邊應描述同一組
        agent；不一致即為漂移。由 <code className="font-mono">bin/sk check ssot</code> 偵測，每日 03:00 cron 複查。
      </p>

      {err && <p style={{ color: "var(--status-err)" }}>Error: {err}</p>}
      {!err && !ssot && <p style={{ color: "var(--text-muted)" }}>載入中...</p>}

      {ssot && ssot.error && (
        <p style={{ color: "var(--status-err)" }}>檢查失敗：{ssot.error}</p>
      )}

      {ssot && drift === 0 && (
        <div
          className="p-6"
          style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}
        >
          <p style={{ color: "var(--status-ok)" }}>✓ 無漂移，兩個 SSOT 一致。</p>
        </div>
      )}

      {ssot && drift !== null && drift > 0 && (
        <>
          <DriftList
            title="agents.conf 有，projects.json 缺"
            hint="agent 已定義並排程，但 projects.json 沒有對應 metadata。多為系統 agent（doctor/janitor…）刻意不列，或新 agent 尚未補登。"
            pairs={ssot.agents_conf_only}
          />
          <DriftList
            title="projects.json 宣稱，agents.conf 沒有"
            hint="專案 metadata 引用了一個 agents.conf 未定義的 agent。常見成因：兩邊 project key 命名不一致（如 sales vs sales-assistant），或 agent 已移除但 metadata 未清。"
            pairs={ssot.projects_json_only}
          />

          <section className="mt-8">
            <h2
              className="mb-2"
              style={{ fontSize: 18, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.01em" }}
            >
              如何修復
            </h2>
            <ul className="max-w-3xl list-disc space-y-1 pl-5 text-sm" style={{ color: "var(--text-muted)", lineHeight: 1.55 }}>
              <li>
                <b>project key 不一致</b>：統一命名 —— 將 <code className="font-mono">agents.conf</code> 的 key
                或 <code className="font-mono">projects.json</code> 的 key 改成一致（如 sales → sales-assistant）。
              </li>
              <li>
                <b>系統 agent 未列入 projects.json</b>：若是 doctor/janitor 這類內部 agent，可在{" "}
                <code className="font-mono">projects.json</code> 的 rivendell <code className="font-mono">agents</code>{" "}
                陣列補上，或接受其為已知差異。
              </li>
              <li>
                <b>agent 已移除</b>：從 <code className="font-mono">projects.json</code> 刪掉該 agent 引用。
              </li>
            </ul>
          </section>
        </>
      )}

      {checkedAt && (
        <p className="mt-8 font-mono text-[11px]" style={{ color: "var(--text-subtle)" }}>
          檢查時間：{new Date(checkedAt).toLocaleString("zh-TW")}
        </p>
      )}
    </div>
  );
}
