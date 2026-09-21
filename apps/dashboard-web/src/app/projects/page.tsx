"use client";

import { useEffect, useState } from "react";
import {
  apiFetch,
  apiPost,
  apiPut,
  apiDelete,
  type ProjectsData,
  type ProjectInfo,
  type MissionBrief,
} from "@/lib/api";
import MetricsRow from "@/components/MetricsRow";
import {
  Pencil,
  Trash2,
  Plus,
  X,
  FolderOpen,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Target,
  Ban,
  Bot,
} from "lucide-react";
import Link from "next/link";

// ── Reusable styles ──────────────────────────────────────────────────

const cardStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
};

const inputStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-sm)",
  color: "var(--text)",
};

const accentBtn: React.CSSProperties = {
  background: "var(--accent)",
  color: "var(--surface)",
  borderRadius: "var(--radius-sm)",
};

const ghostBtn: React.CSSProperties = {
  background: "transparent",
  border: "1px solid var(--border-strong)",
  color: "var(--text)",
  borderRadius: "var(--radius-sm)",
};

const dangerBtn: React.CSSProperties = {
  background: "var(--status-err)",
  color: "var(--surface)",
  borderRadius: "var(--radius-sm)",
};

const subtleLabel: React.CSSProperties = {
  fontSize: 11,
  color: "var(--text-muted)",
  fontFamily: "var(--font-mono)",
};

// ── Git Status Badge ──────────────────────────────────────────────────

function GitBadge({ git }: { git: ProjectInfo["git"] }) {
  if (!git) return null;
  if (git.error === "no-repo" || git.error === "no-git") {
    return (
      <div
        className="mt-3 px-3 py-2 text-xs"
        style={{
          background: "var(--surface-2)",
          color: "var(--text-subtle)",
          borderRadius: "var(--radius-sm)",
        }}
      >
        {git.error === "no-repo" ? "repo 路徑不存在" : "非 git repo"}
      </div>
    );
  }
  if (!git.is_git) return null;

  const syncColor =
    git.behind > 0
      ? "var(--status-err)"
      : git.ahead > 0
        ? "var(--status-warn)"
        : "var(--status-ok)";

  const syncLabel =
    git.behind > 0
      ? `↓${git.behind} behind`
      : git.ahead > 0
        ? `↑${git.ahead} unpushed`
        : "synced";

  return (
    <div
      className="mt-3 px-3 py-2 text-xs"
      style={{
        background: "var(--surface-2)",
        borderRadius: "var(--radius-sm)",
      }}
    >
      <div className="flex items-center justify-between">
        <span
          className="font-mono"
          style={{ color: "var(--text-muted)" }}
        >
          {git.branch}
        </span>
        <span
          className="font-mono font-medium tabular-nums"
          style={{ color: syncColor }}
        >
          {syncLabel}
        </span>
      </div>
      {git.last_commit_msg && (
        <p
          className="mt-1 truncate"
          style={{ color: "var(--text-muted)" }}
        >
          {git.last_commit_ago} — {git.last_commit_msg}
        </p>
      )}
      {git.recent_files.length > 0 && (
        <p
          className="mt-0.5 truncate font-mono"
          style={{ color: "var(--text-subtle)" }}
        >
          {git.recent_files.slice(0, 3).join(", ")}
        </p>
      )}
    </div>
  );
}

// ── Mission ──────────────────────────────────────────────────────────

const EMPTY_MISSION: MissionBrief = {
  goal: "",
  commercial_value: "",
  potential_clients: [],
  expected_revenue: "",
  blockers: [],
  next_steps: [],
  resources_needed: "",
  situation_analysis: "",
  deadline: "",
};

function hasMission(m: MissionBrief): boolean {
  return !!(
    m.goal ||
    m.commercial_value ||
    m.situation_analysis ||
    m.expected_revenue ||
    m.potential_clients.length ||
    m.blockers.length ||
    m.next_steps.length
  );
}

function MissionCard({ mission }: { mission: MissionBrief }) {
  const [open, setOpen] = useState(true);
  if (!hasMission(mission)) return null;

  return (
    <div
      className="mt-3 text-xs"
      style={{
        background: "var(--accent-bg)",
        border: "1px solid var(--accent-soft)",
        borderRadius: "var(--radius-sm)",
      }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-3 py-2 font-medium"
        style={{ color: "var(--accent)" }}
      >
        <span className="inline-flex items-center gap-1.5">
          <Target size={12} /> 使命
        </span>
        {open ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
      </button>
      {open && (
        <div
          className="space-y-1 px-3 pb-2"
          style={{ color: "var(--text)" }}
        >
          {mission.goal && (
            <p>
              <span style={{ color: "var(--text-subtle)" }}>目標：</span>
              {mission.goal}
            </p>
          )}
          {mission.deadline && (
            <p>
              <span style={{ color: "var(--text-subtle)" }}>期限：</span>
              {mission.deadline}
            </p>
          )}
          {mission.expected_revenue && (
            <p>
              <span style={{ color: "var(--text-subtle)" }}>預期收益：</span>
              {mission.expected_revenue}
            </p>
          )}
          {mission.potential_clients.length > 0 && (
            <p>
              <span style={{ color: "var(--text-subtle)" }}>潛在客戶：</span>
              {mission.potential_clients.join("、")}
            </p>
          )}
          {mission.situation_analysis && (
            <p>
              <span style={{ color: "var(--text-subtle)" }}>局勢：</span>
              {mission.situation_analysis}
            </p>
          )}
          {mission.commercial_value && (
            <p>
              <span style={{ color: "var(--text-subtle)" }}>商業價值：</span>
              {mission.commercial_value}
            </p>
          )}
          {mission.blockers.length > 0 && (
            <p>
              <span style={{ color: "var(--text-subtle)" }}>阻礙：</span>
              {mission.blockers.map((b, i) => (
                <span
                  key={i}
                  className="mr-1.5 inline-flex items-center gap-1"
                  style={{ color: "var(--status-err)" }}
                >
                  <Ban size={10} /> {b}
                </span>
              ))}
            </p>
          )}
          {mission.next_steps.length > 0 && (
            <p>
              <span style={{ color: "var(--text-subtle)" }}>下一步：</span>
              {mission.next_steps.slice(0, 3).map((s, i) => (
                <span key={i} className="mr-2">
                  {i + 1}. {s}
                </span>
              ))}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function MissionEditForm({
  mission,
  onChange,
}: {
  mission: MissionBrief;
  onChange: (m: MissionBrief) => void;
}) {
  const field = (
    key: keyof MissionBrief,
    label: string,
    placeholder = ""
  ) => (
    <label className="block">
      <span style={subtleLabel}>{label}</span>
      <input
        value={mission[key] as string}
        onChange={(e) => onChange({ ...mission, [key]: e.target.value })}
        placeholder={placeholder}
        className="mt-0.5 w-full px-2 py-1 text-xs"
        style={inputStyle}
      />
    </label>
  );

  const listField = (
    key: "potential_clients" | "blockers" | "next_steps",
    label: string,
    placeholder = ""
  ) => (
    <label className="block">
      <span style={subtleLabel}>{label}（逗號分隔）</span>
      <input
        value={(mission[key] as string[]).join(", ")}
        onChange={(e) =>
          onChange({
            ...mission,
            [key]: e.target.value
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean),
          })
        }
        placeholder={placeholder}
        className="mt-0.5 w-full px-2 py-1 text-xs"
        style={inputStyle}
      />
    </label>
  );

  return (
    <div
      className="mt-3 space-y-2 p-3"
      style={{
        background: "var(--accent-bg)",
        border: "1px solid var(--accent-soft)",
        borderRadius: "var(--radius-sm)",
      }}
    >
      <p
        className="text-xs font-medium inline-flex items-center gap-1.5"
        style={{ color: "var(--accent)" }}
      >
        <Target size={12} /> 使命
      </p>
      {field("goal", "目標（一句話）", "S35 完成，可上線 SMB 客戶")}
      {field("deadline", "期限", "S35 結束前")}
      {field("expected_revenue", "預期收益", "NT$50k/月")}
      {listField("potential_clients", "潛在客戶", "東聯化學, 台塑石化")}
      {field("situation_analysis", "當前局勢", "HubSpot 貴且難用")}
      {field("commercial_value", "商業價值", "B2B SaaS, 每客戶年約")}
      {listField("blockers", "阻礙", "Auth 系統未動工")}
      {listField("next_steps", "下一步", "接洽公安協會, 開發 MVP")}
      {field("resources_needed", "所需資源", "前端工程師 × 1")}
    </div>
  );
}

// ── Project Card ──────────────────────────────────────────────────────

function ProjectCard({
  project,
  onRefresh,
}: {
  project: ProjectInfo;
  onRefresh: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [desc, setDesc] = useState(project.description);
  const [agentsStr, setAgentsStr] = useState(project.agents.join(", "));
  const [mission, setMission] = useState<MissionBrief>(
    project.mission ?? EMPTY_MISSION
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setBusy(true);
    setError(null);
    try {
      await apiPut(`/api/projects/${encodeURIComponent(project.name)}`, {
        description: desc,
        agents: agentsStr
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        mission,
      });
      setEditing(false);
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`確定刪除專案「${project.name}」？（不會影響 plist 檔案）`))
      return;
    setBusy(true);
    try {
      await apiDelete(`/api/projects/${encodeURIComponent(project.name)}`);
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="p-5" style={cardStyle}>
      <div className="flex items-start justify-between gap-3">
        <Link
          href={`/projects/${encodeURIComponent(project.name)}`}
          className="flex items-center gap-2 transition-colors"
          style={{ color: "var(--text)" }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.color = "var(--accent)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.color = "var(--text)")
          }
        >
          <FolderOpen
            size={18}
            style={{ color: "var(--text-muted)" }}
          />
          <h3
            className="text-base"
            style={{ fontWeight: 500, fontFamily: "var(--font-mono)" }}
          >
            {project.name}
          </h3>
          <ChevronRight
            size={16}
            style={{ color: "var(--text-subtle)" }}
          />
        </Link>
        <span
          className="inline-flex items-center px-2 py-0.5 text-xs font-mono tabular-nums"
          style={{
            borderRadius: 99,
            background:
              project.agent_count_loaded > 0
                ? "var(--accent-bg)"
                : "var(--surface-2)",
            color:
              project.agent_count_loaded > 0
                ? "var(--accent)"
                : "var(--text-muted)",
          }}
        >
          {project.agent_count_loaded}/{project.agents.length} running
        </span>
      </div>

      <p
        className="mt-1 font-mono text-xs"
        style={{ color: "var(--text-subtle)" }}
      >
        {project.repo}
      </p>

      {editing ? (
        <div className="mt-3 space-y-2">
          <input
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            placeholder="描述"
            className="w-full px-3 py-1.5 text-sm"
            style={inputStyle}
          />
          <input
            value={agentsStr}
            onChange={(e) => setAgentsStr(e.target.value)}
            placeholder="Agents（逗號分隔）"
            className="w-full px-3 py-1.5 text-sm font-mono"
            style={inputStyle}
          />
          <MissionEditForm mission={mission} onChange={setMission} />
          <div className="flex gap-2 pt-1">
            <button
              disabled={busy}
              onClick={handleSave}
              className="px-3 py-1.5 text-xs font-medium disabled:opacity-50"
              style={accentBtn}
            >
              儲存
            </button>
            <button
              onClick={() => setEditing(false)}
              className="px-3 py-1.5 text-xs font-medium"
              style={ghostBtn}
            >
              取消
            </button>
          </div>
        </div>
      ) : (
        <>
          <p
            className="mt-2 text-sm"
            style={{ color: "var(--text-muted)" }}
          >
            {project.description || "（無描述）"}
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            {project.agents.map((name) => (
              <span
                key={name}
                className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-mono"
                style={{
                  borderRadius: 99,
                  background: "var(--surface-2)",
                  color: "var(--text)",
                  border: "1px solid var(--border)",
                }}
              >
                <Bot size={11} />
                {name}
              </span>
            ))}
            {project.agents.length === 0 && (
              <span
                className="text-xs"
                style={{ color: "var(--text-subtle)" }}
              >
                尚無 agent
              </span>
            )}
          </div>

          <MissionCard mission={project.mission ?? EMPTY_MISSION} />
          <GitBadge git={project.git} />

          <div className="mt-4 flex gap-2">
            <button
              onClick={() => {
                setEditing(true);
                setMission(project.mission ?? EMPTY_MISSION);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium"
              style={ghostBtn}
            >
              <Pencil size={14} /> 編輯
            </button>
            <button
              disabled={busy}
              onClick={handleDelete}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium disabled:opacity-50"
              style={dangerBtn}
            >
              <Trash2 size={14} /> 刪除
            </button>
          </div>
        </>
      )}

      {error && (
        <p
          className="mt-2 text-xs"
          style={{ color: "var(--status-err)" }}
        >
          {error}
        </p>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────

export default function ProjectsPage() {
  const [data, setData] = useState<ProjectsData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [newName, setNewName] = useState("");
  const [newRepo, setNewRepo] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newAgents, setNewAgents] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    apiFetch<ProjectsData>("/api/projects")
      .then(setData)
      .catch((e) => setErr(e.message));
  }, []);

  function reload() {
    apiFetch<ProjectsData>("/api/projects")
      .then(setData)
      .catch((e) => setErr(e.message));
  }

  async function handleCreate() {
    if (!newName.trim()) return;
    setCreating(true);
    setErr(null);
    try {
      await apiPost("/api/projects", {
        name: newName.trim(),
        repo: newRepo.trim(),
        description: newDesc.trim(),
        agents: newAgents
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      });
      setNewName("");
      setNewRepo("");
      setNewDesc("");
      setNewAgents("");
      setShowForm(false);
      reload();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  }

  if (err && !data)
    return <p style={{ color: "var(--status-err)" }}>Error: {err}</p>;
  if (!data)
    return <p style={{ color: "var(--text-muted)" }}>載入中...</p>;

  const { projects } = data;
  const totalAgents = projects.reduce((s, p) => s + p.agents.length, 0);
  const totalCost = projects.reduce((s, p) => s + p.total_cost_usd, 0);

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
        專案管理
      </h1>

      <MetricsRow
        metrics={[
          { label: "總專案", value: projects.length },
          { label: "總 Agent", value: totalAgents },
          { label: "總花費", value: `$${totalCost.toFixed(2)}` },
        ]}
      />

      <div className="mt-6 flex justify-end">
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium"
          style={accentBtn}
        >
          {showForm ? <X size={16} /> : <Plus size={16} />}
          {showForm ? "取消" : "新增專案"}
        </button>
      </div>

      {showForm && (
        <div
          className="mt-4 p-5"
          style={{
            background: "var(--accent-bg)",
            border: "1px solid var(--accent-soft)",
            borderRadius: "var(--radius-md)",
          }}
        >
          <h2
            className="mb-4 text-sm"
            style={{ color: "var(--text)", fontWeight: 500 }}
          >
            新增專案
          </h2>
          <div className="space-y-3">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="block">
                <span style={subtleLabel}>專案名稱</span>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="my-project"
                  className="mt-1 w-full px-3 py-2 text-sm"
                  style={inputStyle}
                />
              </label>
              <label className="block">
                <span style={subtleLabel}>Repo 路徑</span>
                <input
                  value={newRepo}
                  onChange={(e) => setNewRepo(e.target.value)}
                  placeholder="/Users/…/Projects/my-project"
                  className="mt-1 w-full px-3 py-2 text-sm font-mono"
                  style={inputStyle}
                />
              </label>
            </div>
            <label className="block">
              <span style={subtleLabel}>描述</span>
              <input
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Project description…"
                className="mt-1 w-full px-3 py-2 text-sm"
                style={inputStyle}
              />
            </label>
            <label className="block">
              <span style={subtleLabel}>Agent（逗號分隔）</span>
              <input
                value={newAgents}
                onChange={(e) => setNewAgents(e.target.value)}
                placeholder="maintainer, tester"
                className="mt-1 w-full px-3 py-2 text-sm font-mono"
                style={inputStyle}
              />
            </label>
            <button
              disabled={creating || !newName.trim()}
              onClick={handleCreate}
              className="px-4 py-2 text-sm font-medium disabled:opacity-50"
              style={accentBtn}
            >
              建立
            </button>
          </div>
          {err && (
            <p
              className="mt-2 text-xs"
              style={{ color: "var(--status-err)" }}
            >
              {err}
            </p>
          )}
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {projects.map((p) => (
          <ProjectCard key={p.name} project={p} onRefresh={reload} />
        ))}
        {projects.length === 0 && (
          <p
            className="text-sm"
            style={{ color: "var(--text-muted)" }}
          >
            尚無專案。點擊「新增專案」或編輯{" "}
            <code
              className="px-1 text-xs font-mono"
              style={{
                background: "var(--surface-2)",
                color: "var(--text)",
                borderRadius: 2,
              }}
            >
              ~/.claude/projects.json
            </code>
          </p>
        )}
      </div>
    </div>
  );
}
