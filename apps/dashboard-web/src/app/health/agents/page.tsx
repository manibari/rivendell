"use client";

import { useEffect, useState } from "react";
import { apiFetch, type HealthData, type AgentDriftInfo, type AgentDriftPair } from "@/lib/api";
import StatusDot from "@/components/StatusDot";

function PairList({
  title,
  hint,
  pairs,
}: {
  title: string;
  hint: string;
  pairs: AgentDriftPair[];
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
      <p className="mb-3 max-w-3xl text-sm" style={{ color: "var(--text-muted)", lineHeight: 1.55 }}>
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
              key={p.label}
              className="flex items-center gap-3 px-4 py-2 font-mono text-sm"
              style={{
                background: "var(--surface)",
                borderTop: i === 0 ? "none" : "1px solid var(--border)",
              }}
            >
              <span style={{ color: "var(--text-subtle)" }}>{p.project}</span>
              <span style={{ color: "var(--text-subtle)" }}>/</span>
              <span style={{ color: "var(--text)" }}>{p.agent}</span>
              <span className="ml-auto text-[11px]" style={{ color: "var(--text-subtle)" }}>
                {p.label}
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default function ScheduleHealthPage() {
  const [info, setInfo] = useState<AgentDriftInfo | null>(null);
  const [checkedAt, setCheckedAt] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<HealthData>("/api/health")
      .then((d) => {
        setInfo(d.agent_drift);
        setCheckedAt(d.checked_at);
      })
      .catch((e) => setErr(e.message));
  }, []);

  const drift = info ? info.total_drift : null;
  const dot = drift === null ? "idle" : drift < 0 ? "err" : drift === 0 ? "ok" : "warn";
  const label =
    drift === null ? "—" : drift < 0 ? "檢查失敗" : drift === 0 ? "全部載入" : `${drift} 項未對齊`;

  return (
    <div>
      <div className="mb-2 flex items-center gap-3">
        <h1
          className="tracking-tight"
          style={{ fontSize: 28, fontWeight: 500, color: "var(--text)", letterSpacing: "-0.02em" }}
        >
          排程健康
        </h1>
        {info && <StatusDot status={dot} label={label} />}
      </div>

      <p className="mb-5 max-w-3xl text-sm" style={{ color: "var(--text-muted)", lineHeight: 1.55 }}>
        比對 <code className="font-mono">agents/agents.conf</code>（agent 身分 SSOT）與目前{" "}
        <code className="font-mono">launchctl</code> 已載入的服務。每個已定義的 agent 都應實際載入到 launchd 才會按排程執行。
        <b>注意</b>：總覽的 Agent 表與 Pending Issues 只列舉<u>已安裝 plist</u> 的 agent —— 在 agents.conf
        有定義但從未安裝 plist 的 agent 會在那些畫面<u>完全隱形</u>，只有這裡抓得到。
        由 <code className="font-mono">bin/sk check agents</code> 偵測。
      </p>

      {err && <p style={{ color: "var(--status-err)" }}>Error: {err}</p>}
      {!err && !info && <p style={{ color: "var(--text-muted)" }}>載入中...</p>}

      {info && info.error && <p style={{ color: "var(--status-err)" }}>檢查失敗：{info.error}</p>}

      {info && drift !== null && drift >= 0 && (
        <>
          <div
            className="flex gap-6 p-4 font-mono text-sm"
            style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}
          >
            <span>
              <span style={{ color: "var(--text-subtle)" }}>已定義 </span>
              <span style={{ color: "var(--text)" }}>{info.defined}</span>
            </span>
            <span>
              <span style={{ color: "var(--text-subtle)" }}>已載入 </span>
              <span style={{ color: drift === 0 ? "var(--status-ok)" : "var(--text)" }}>{info.loaded}</span>
            </span>
          </div>

          {drift === 0 ? (
            <p className="mt-4" style={{ color: "var(--status-ok)" }}>
              ✓ 所有 agents.conf 定義的 agent 都已載入 launchd。
            </p>
          ) : (
            <>
              <PairList
                title="已定義但未載入"
                hint="這些 agent 在 agents.conf 有定義，但 launchd 沒載入 → 排程不會執行。多因新增 agent 後沒（或不能）重跑 sk-setup-agents（其 PROJECTS_DIR 仍寫死舊路徑，重跑會倒回全部 plist）。修法：手動建 plist + launchctl bootstrap，或修好 sk-setup-agents 後重跑。"
                pairs={info.not_loaded}
              />
              <PairList
                title="launchd 有但 agents.conf 沒有"
                hint="launchd 載入了一個 agents.conf 未定義的服務（孤兒 plist）。多為改名 / 移除 agent 後 plist 沒清。修法：launchctl bootout 後刪除該 plist，或補回 agents.conf。"
                pairs={info.loaded_not_in_conf}
              />
            </>
          )}
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
