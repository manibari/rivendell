"use client";

import { useCallback, useEffect, useState } from "react";
import { KeyRound, RefreshCw, Trash2 } from "lucide-react";

// avatar-gateway 是獨立服務（127.0.0.1:8310），不走 :8000 的 api helpers
const GATEWAY = "http://localhost:8310";

type Persona = {
  slug: string;
  display_name: string;
  gender: string;
  voice: string;
  vrm: string;
};

type PersonaData = { active: string; engine: string; personas: Persona[] };
type HealthData = {
  ok: boolean;
  active: string;
  engine: string;
  engines: Record<string, boolean>;
};
type KeysData = Record<string, { set: boolean; masked: string | null }>;
type HistoryEntry = {
  ts: string;
  persona: string;
  engine: string;
  user: string;
  reply: string;
  dispatch: boolean;
};

const ENGINE_LABEL: Record<string, string> = {
  codex: "Codex（ChatGPT 訂閱額度）",
  claude: "Claude Code（訂閱額度）",
  "openai-api": "OpenAI API（金鑰計費）",
  "anthropic-api": "Anthropic API（金鑰計費）",
};

async function gw<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${GATEWAY}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) throw new Error(`gateway ${res.status}`);
  return res.json();
}

export default function AvatarPage() {
  const [data, setData] = useState<PersonaData | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [keys, setKeys] = useState<KeysData | null>(null);
  const [chosen, setChosen] = useState<string>("");
  const [keyInput, setKeyInput] = useState<Record<string, string>>({});
  const [err, setErr] = useState<string>("");
  const [log, setLog] = useState<HistoryEntry[]>([]);

  const refreshLog = useCallback(async () => {
    try {
      const h = await gw<{ entries: HistoryEntry[] }>("/history?limit=30");
      setLog(h.entries);
    } catch {
      /* gateway down — err banner已處理 */
    }
  }, []);

  useEffect(() => {
    refreshLog();
    const t = setInterval(refreshLog, 10000);
    return () => clearInterval(t);
  }, [refreshLog]);

  const refresh = useCallback(async () => {
    try {
      const [p, h, k] = await Promise.all([
        gw<PersonaData>("/persona"),
        gw<HealthData>("/health"),
        gw<KeysData>("/settings/keys"),
      ]);
      setData(p);
      setHealth(h);
      setKeys(k);
      setChosen((c) => c || p.active);
      setErr("");
    } catch {
      setErr("gateway 未啟動（com.sk.gateway，:8310）");
    }
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem("avatar-persona");
    if (saved) setChosen(saved);
    refresh();
  }, [refresh]);

  const pick = async (slug: string) => {
    setChosen(slug);
    localStorage.setItem("avatar-persona", slug);
    await gw("/persona", { method: "POST", body: JSON.stringify({ active: slug }) });
    refresh();
  };

  const setEngine = async (engine: string) => {
    await gw("/persona", { method: "POST", body: JSON.stringify({ engine }) });
    refresh();
  };

  const saveKeys = async () => {
    await gw("/settings/keys", { method: "POST", body: JSON.stringify(keyInput) });
    setKeyInput({});
    refresh();
  };

  const deleteKey = async (name: string) => {
    await gw(`/settings/keys/${name}`, { method: "DELETE" });
    refresh();
  };

  const persona = data?.personas.find((p) => p.slug === chosen);
  const iframeSrc = persona
    ? `/avatar/widget.html?ollama=${encodeURIComponent(`${GATEWAY}/v1`)}` +
      `&api=${encodeURIComponent(`${GATEWAY}/api/tts`)}` +
      `&llmmodel=${persona.slug}&vrm=${encodeURIComponent(persona.vrm)}` +
      `&voice=${persona.voice}&name=${encodeURIComponent(persona.display_name)}` +
      `&lang=zh-TW&engine=3d&open=true`
    : "";

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 600, marginBottom: 4 }}>助理</h1>
      <p style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 20 }}>
        選一位助理對話。要辦的事她/他只會開提案，確認分級照舊。
      </p>

      {err && (
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--status-err)",
            borderRadius: 8,
            padding: "10px 14px",
            color: "var(--status-err)",
            fontSize: 13,
            marginBottom: 16,
          }}
        >
          {err}
        </div>
      )}

      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        {data?.personas.map((p) => (
          <button
            key={p.slug}
            onClick={() => pick(p.slug)}
            style={{
              flex: 1,
              maxWidth: 260,
              textAlign: "left",
              background: chosen === p.slug ? "var(--accent-bg)" : "var(--surface)",
              border: `1px solid ${chosen === p.slug ? "var(--accent)" : "var(--border-strong)"}`,
              borderRadius: 10,
              padding: "14px 16px",
              cursor: "pointer",
            }}
          >
            <div style={{ fontWeight: 600, fontSize: 15, color: "var(--text)" }}>
              {p.display_name}
              <span style={{ color: "var(--text-subtle)", fontWeight: 400, marginLeft: 8 }}>
                {p.gender === "f" ? "她" : "他"}
              </span>
            </div>
            <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 4 }}>
              {p.slug} · {p.voice.replace("zh-TW-", "").replace("Neural", "")}
            </div>
          </button>
        ))}
      </div>

      {iframeSrc && (
        <iframe
          key={iframeSrc}
          src={iframeSrc}
          allow="microphone; autoplay"
          style={{
            width: "100%",
            height: 560,
            border: "1px solid var(--border)",
            borderRadius: 10,
            background: "var(--surface)",
          }}
          title="assistant avatar"
        />
      )}

      <div
        style={{
          marginTop: 20,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 10,
          padding: "16px 18px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <KeyRound size={15} style={{ color: "var(--accent)" }} />
          <span style={{ fontWeight: 600, fontSize: 14 }}>引擎與 API 金鑰</span>
          <button
            onClick={refresh}
            style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", color: "var(--text-subtle)" }}
            title="重新整理"
          >
            <RefreshCw size={14} />
          </button>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
          <span style={{ fontSize: 13, color: "var(--text-muted)" }}>對話引擎</span>
          <select
            value={data?.engine || "codex"}
            onChange={(e) => setEngine(e.target.value)}
            style={{
              fontSize: 13,
              padding: "4px 8px",
              border: "1px solid var(--border-strong)",
              borderRadius: 6,
              background: "var(--surface)",
              color: "var(--text)",
            }}
          >
            {Object.entries(ENGINE_LABEL).map(([v, label]) => (
              <option key={v} value={v} disabled={health ? !health.engines[v] : false}>
                {label}
                {health && !health.engines[v] ? "（未就緒）" : ""}
              </option>
            ))}
          </select>
          {health && (
            <span style={{ fontSize: 12, color: "var(--text-subtle)" }}>
              codex {health.engines["codex"] ? "已登入" : "未登入"} · claude 可用
            </span>
          )}
        </div>

        {(["OPENAI_API_KEY", "ANTHROPIC_API_KEY"] as const).map((name) => (
          <div key={name} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span style={{ fontSize: 12, fontFamily: "var(--font-geist-mono, monospace)", width: 160, color: "var(--text-muted)" }}>
              {name}
            </span>
            {keys?.[name]?.set ? (
              <>
                <span style={{ fontSize: 12, color: "var(--text)" }}>已設定（{keys[name].masked}）</span>
                <button
                  onClick={() => deleteKey(name)}
                  style={{ background: "none", border: "none", cursor: "pointer", color: "var(--status-err)" }}
                  title="清除"
                >
                  <Trash2 size={13} />
                </button>
              </>
            ) : (
              <input
                type="password"
                placeholder="貼上金鑰後按儲存"
                value={keyInput[name] || ""}
                onChange={(e) => setKeyInput({ ...keyInput, [name]: e.target.value })}
                style={{
                  flex: 1,
                  maxWidth: 380,
                  fontSize: 12,
                  padding: "5px 8px",
                  border: "1px solid var(--border-strong)",
                  borderRadius: 6,
                  background: "var(--surface)",
                  color: "var(--text)",
                }}
              />
            )}
          </div>
        ))}
        {Object.values(keyInput).some(Boolean) && (
          <button
            onClick={saveKeys}
            style={{
              marginTop: 6,
              fontSize: 13,
              padding: "6px 14px",
              background: "var(--accent)",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
            }}
          >
            儲存金鑰
          </button>
        )}
        <p style={{ fontSize: 11, color: "var(--text-subtle)", marginTop: 10 }}>
          金鑰存在本機 ~/.config/rivendell/gateway-keys.env（chmod 600），僅 gateway 讀取，畫面只顯示末四碼。
          設定 OPENAI_API_KEY 後語音自動升級為自然人聲（OpenAI TTS）。
        </p>
      </div>

      <div
        style={{
          marginTop: 20,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 10,
          padding: "16px 18px",
        }}
      >
        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 10 }}>
          今日對話紀錄
          <span style={{ color: "var(--text-subtle)", fontWeight: 400, fontSize: 12, marginLeft: 8 }}>
            data/chat-log/（每 10 秒更新）
          </span>
        </div>
        {log.length === 0 ? (
          <p style={{ fontSize: 13, color: "var(--text-subtle)" }}>今天還沒有對話。</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 360, overflowY: "auto" }}>
            {[...log].reverse().map((e, i) => (
              <div key={i} style={{ fontSize: 13, borderBottom: "1px solid var(--border)", paddingBottom: 8 }}>
                <div style={{ color: "var(--text-subtle)", fontSize: 11, marginBottom: 2 }}>
                  {e.ts} · {e.persona}@{e.engine}
                  {e.dispatch && (
                    <span style={{ color: "var(--accent)", marginLeft: 6 }}>開了提案</span>
                  )}
                </div>
                <div style={{ color: "var(--text-muted)" }}>Peter：{e.user}</div>
                <div style={{ color: "var(--text)" }}>{e.reply}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
