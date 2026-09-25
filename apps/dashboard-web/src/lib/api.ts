// Default to SAME-ORIGIN relative URLs: apiFetch("/api/x") → this origin → the
// next.config.ts rewrite proxies /api/* to the backend server-side. Never bake a
// host into the client bundle (NEXT_PUBLIC_API_URL=localhost would break tunnel /
// cross-machine access). Set NEXT_PUBLIC_API_URL only for a deliberate direct API.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return apiFetch(path, { method: "POST", body: JSON.stringify(body) });
}

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return apiFetch(path, { method: "PUT", body: JSON.stringify(body) });
}

export function apiDelete<T>(path: string): Promise<T> {
  return apiFetch(path, { method: "DELETE" });
}

// ── Types ────────────────────────────────────────────────────────────

export interface OverviewData {
  metrics: {
    total_skills: number;
    running_agents: number;
    enabled_hooks: number;
    total_cost_usd: number;
    total_projects: number;
  };
  agents: AgentInfo[];
  hooks: HookInfo[];
  projects_summary: {
    name: string;
    description: string;
    agent_count: number;
    agent_count_loaded: number;
  }[];
}

export interface HookInfo {
  event: string;
  matcher: string;
  command: string;
}

export interface AgentInfo {
  label: string;
  name: string;
  description: string;
  project: string;
  plist_path: string;
  working_directory: string;
  schedule: Record<string, unknown>;
  schedule_display: string;
  schedule_list: Record<string, number>[];
  loaded: boolean;
  installed: boolean;
  pid: number | null;
  exit_code: number | null;
  role_badge: string;
  merge_strategy_display: string;
  qa_display: string;
  recent_commit: { sha: string; message: string } | null;
  git_safety: {
    allowed_paths: string[];
    forbidden_paths: string[];
    max_files_changed: number;
  } | null;
  current_activity: {
    tool: string;
    label: string;
    detail: string;
  } | null;
}

export interface AgentsData {
  metrics: {
    total: number;
    running: number;
    last_success: string | null;
    today_cost: number;
  };
  agents: AgentInfo[];
  by_project: Record<string, string[]>;
}

export interface AgentRun {
  started_at: string | null;
  finished_at: string | null;
  exit_code: number | null;
  tokens_used: number | null;
  cost_usd: number | null;
  commit_sha: string | null;
  files_changed: number | null;
  qa_passed: number | null;
  branch_name: string | null;
  pr_url: string | null;
}

export interface TokensData {
  totals: {
    total_sessions: number;
    total_messages: number;
    total_cost_usd: number;
    total_input: number;
    total_output: number;
    total_cache_read: number;
    first_session: string;
    last_computed: string;
  };
  daily: {
    date: string;
    sessions: number;
    messages: number;
    tool_calls: number;
    tokens_total: number;
    cost_usd: number;
    models: Record<string, number>;
  }[];
  models: {
    model: string;
    input_tokens: number;
    output_tokens: number;
    cache_read_tokens: number;
    cache_create_tokens: number;
    cost_usd: number;
  }[];
}

export interface FilteredTokensData {
  total_sessions: number;
  total_messages: number;
  total_cost_usd: number;
  total_tokens: number;
  total_cache_tokens: number;
  daily: {
    date: string;
    sessions: number;
    messages: number;
    tokens_total: number;
    cache_tokens: number;
    cost_usd: number;
  }[];
  models: {
    model: string;
    source: "claude" | "codex";
    billing: "api" | "subscription";
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
  }[];
  sources?: Record<
    "claude" | "codex",
    { sessions: number; messages: number; tokens: number; cache_tokens: number; cost_usd: number }
  >;
  projects: {
    project: string;
    sessions: number;
    messages: number;
    tokens_total: number;
    cost_usd: number;
  }[];
}

export interface CollaborationData {
  found: boolean;
  pending: number;
  resolved: number;
  resolution_rate: number;
}

export interface IssueItem {
  source: "agent" | "learnings" | "skill" | "env";
  severity: "error" | "warning" | "info";
  title: string;
  detail: string;
  label: string;
}

export interface IssuesData {
  total: number;
  errors: number;
  warnings: number;
  issues: IssueItem[];
}

// ── Health ───────────────────────────────────────────────────────────

export interface DiskInfo {
  volume: string;
  mount: string;
  size_gb: number;
  used_gb: number;
  avail_gb: number;
  percent: number;
  status: "ok" | "warn" | "crit" | "error";
  warn_threshold: number;
  crit_threshold: number;
  error?: string;
}

export interface SsotDriftInfo {
  total_drift: number;
  agents_conf_only: { project: string; agent: string }[];
  projects_json_only: { project: string; agent: string }[];
  error?: string;
}

export interface AgentDriftPair {
  label: string;
  project: string;
  agent: string;
}

export interface AgentDriftInfo {
  total_drift: number;
  defined: number;
  loaded: number;
  not_loaded: AgentDriftPair[];
  loaded_not_in_conf: AgentDriftPair[];
  error?: string;
}

export interface HealthData {
  ssot_drift: SsotDriftInfo;
  disk: DiskInfo;
  agent_drift: AgentDriftInfo;
  checked_at: string;
}

export interface GitRepoStatus {
  name: string;
  branch: string;
  dirty: number;
  ahead: number;
  behind: number;
  has_upstream: boolean;
}

export interface GitHealthData {
  root: string;
  total: number;
  dirty: number;
  unpushed: number;
  repos: GitRepoStatus[];
}

export interface RecentErrorItem {
  name: string;
  size: number;
  mtime: string;
  tail: string;
}

export interface RecentErrorsData {
  recent_days: number;
  total: number;
  errors: RecentErrorItem[];
}

export interface DiskTreeNode {
  name: string;
  path: string;
  size_kb: number;
  children: DiskTreeNode[];
}

export interface DiskTreeData {
  available: boolean;
  root?: string;
  depth?: number;
  generated_at?: string;
  duration_sec?: number;
  df?: {
    size_kb: number;
    used_kb: number;
    avail_kb: number;
    percent: number;
    mount: string;
  };
  tree: DiskTreeNode | null;
  hint?: string;
  error?: string;
}

export interface SkillInfo {
  name: string;
  category: string;
  summary: string;
  line_count: number;
  invocable: boolean;
  lifecycle: string;
  /** rivendell | gstack | external | builtin */
  source: string;
  /** rivendell skills/<folder>/ the deployed symlink resolves into */
  folder: string;
  /** frontmatter loop: sales|gov|invest|hr|knowledge|platform|dev|shared */
  loop: string;
  /** frontmatter pdca: plan|do|check|act */
  pdca: string;
}

export interface RoleStage {
  stage: "Plan" | "Do" | "Check" | "Act";
  text: string;
  skills: string[];
  /** 主線：必經，照順序 */
  core: string[];
  /** 視情況：有那個條件才叫 */
  conditional: string[];
  /** 自動：hook / gate，自己會跳出來 */
  automatic: string[];
  gaps: string[];
  external: string[];
  note: string;
  empty?: boolean;
}

export interface RoleJob {
  id: string;
  title: string;
  deep_dive: { label: string; href: string } | null;
  stages: RoleStage[];
  gap_count: number;
  /** telemetry: agent_runs rows + tasks.jsonl records tagged with this job */
  runs: number;
  by_stage: Record<string, number>;
  last_run: string;
}

export interface Role {
  id: string;
  title: string;
  /** 職權層：決策 / 營運 / 市場 / 交付 / 驗證 / 支援 */
  tier: string;
  /** 能決定什麼 · 對誰負責 */
  authority: string;
  intro: string;
  notes: string[];
  jobs: RoleJob[];
  job_count: number;
  gap_count: number;
  runs: number;
}

export interface SkillRolesData {
  path: string;
  updated: string;
  shared: string[];
  /** tier labels in display order */
  tiers: string[];
  roles: Role[];
  /** unavailable = a source could not be read; run counts are partial, not zero */
  evidence: {
    status: "ok" | "empty" | "unavailable";
    error?: string;
    sources: Record<string, { status: string; events?: number; error?: string; bad_lines?: string[] }>;
  };
  totals: { roles: number; jobs: number; gaps: number; jobs_run: number; runs: number };
  content: string;
}

export interface DocContent {
  path: string;
  content: string;
}

export interface SkillDetail extends SkillInfo {
  content: string;
  workflows?: { workflow_id: string; role_id: string; title: string; step_id: string; stage: string }[];
}

export interface SkillUsageDay {
  date: string;
  count: number;
}

export type SkillUsage = Record<string, SkillUsageDay[]>;

// ── Projects ──────────────────────────────────────────────────────────

export interface MissionBrief {
  goal: string;
  commercial_value: string;
  potential_clients: string[];
  expected_revenue: string;
  blockers: string[];
  next_steps: string[];
  resources_needed: string;
  situation_analysis: string;
  deadline: string;
}

export interface GitStatus {
  branch: string;
  last_commit_msg: string;
  last_commit_ago: string;
  ahead: number;
  behind: number;
  recent_files: string[];
  is_git: boolean;
  error: string;
}

export interface GitCommit {
  hash: string;
  message: string;
  author: string;
  ago: string;
}

export interface ProjectInfo {
  name: string;
  repo: string;
  description: string;
  agents: string[];
  agent_count_loaded: number;
  total_cost_usd: number;
  mission: MissionBrief;
  git: GitStatus;
}

export interface ProjectsData {
  projects: ProjectInfo[];
}

export interface ProjectDetailData extends ProjectInfo {
  agent_details: AgentInfo[];
}

export interface GitLogData {
  commits: GitCommit[];
}

// ── Ports ─────────────────────────────────────────────────────────────────────

export interface PortInfo {
  port: number;
  service: string;
  container: string;
  type: "API" | "Frontend" | "Streamlit" | "DB" | "Cache" | "Service";
  web: boolean;
  category: "前端" | "後端" | "資料庫" | "其他";
  project: string;
  status: "live" | "drift" | "wild" | "stopped" | "unknown";
  declared?: boolean;
  source?: "compose" | "listener" | "docker";
  /** Source-code folder behind this port, from the docker compose
   *  `project.working_dir` label. null when the port isn't a docker container. */
  folder?: string | null;
  image?: string;
  /** True for wild listeners identified as desktop/system apps (Discord,
   *  ControlCenter, browser devtools…) — collapsed in the UI by default. */
  system?: boolean;
  listener?: {
    command?: string;
    pid?: string;
    name?: string;
  } | null;
  listener_error?: string;
}

export interface DeploymentHealth {
  status: "ok" | "down" | "unknown";
  detail: string;
  url?: string | null;
}

export interface PortsData {
  ports: PortInfo[];
  listener_error?: string | null;
  docker_error?: string | null;
  /** Per-app deployment health (keyed by project name), from the shared
   *  ops/monitors.toml health checks. Absent for projects with no monitor. */
  health?: Record<string, DeploymentHealth>;
}

export interface AgentFile {
  name: string;
  path: string;
  size: number;
  modified: number;
  type: string;
}

export interface AgentFileContent {
  name: string;
  content: string;
  size: number;
}

// ── Harvest ──────────────────────────────────────────────────────────

export interface HarvestCandidate {
  key: string;
  name: string;
  strength: "strong" | "moderate" | "weak";
  purpose: string;
  trigger: string;
  category: string;
  reasoning: string;
  conclusion: string;
  report_date: string;
  decision: "pending" | "accepted" | "dismissed";
}

export interface HarvestData {
  total: number;
  pending_count: number;
  accepted_count: number;
  dismissed_count: number;
  candidates: HarvestCandidate[];
}

export interface TimelineEvent {
  ts: string;
  type: "tool" | "text" | "thinking" | "result" | "auto_commit" | "auto_push" | string;
  name?: string;
  input?: Record<string, unknown>;
  text?: string;
  preview?: string;
  len?: number;
  model?: string;
  input_tokens?: number;
  output_tokens?: number;
  cost_usd?: number;
  detail?: string;
}

/** Resolve a markdown-relative image path (e.g. "../assets/x.png" from
 *  docs/loops/gov-tender.md) to the /api/docs-asset URL. `docPath` is the
 *  markdown's path relative to rivendell/docs/. */
export function docAssetUrl(docPath: string, src: string): string {
  if (/^(https?:)?\/\//.test(src) || src.startsWith("/")) return src;
  const dir = docPath.includes("/") ? docPath.slice(0, docPath.lastIndexOf("/")) : "";
  const parts = (dir ? dir.split("/") : []).filter(Boolean);
  for (const seg of src.split("/")) {
    if (seg === "..") parts.pop();
    else if (seg !== "." && seg) parts.push(seg);
  }
  return `${API_BASE}/api/docs-asset/${parts.join("/")}`;
}

/** GET /api/health/sensors — SMC temperatures / fans + IOReport power (no root). */
export interface SensorGroup {
  id: string;
  label: string;
  avg: number;
  max: number;
  sensors: Record<string, number>;
}

export interface SensorFan {
  id: number;
  rpm: number;
  min: number | null;
  max: number | null;
  target: number | null;
  mode: "auto" | "forced";
  percent: number | null;
}

export interface SensorPower {
  id: string;
  label: string;
  watts: number;
}

export interface CpuCore {
  id: string;
  core: number;
  /** % of the window in a running DVFS state; null when unreadable */
  active: number | null;
  /** residency-weighted clock while running; null when the pmgr table is ambiguous */
  freq_mhz: number | null;
  freq_max_mhz: number | null;
  watts: number | null;
}

export interface CpuCluster {
  id: string;
  kind: string;
  label: string;
  cores: CpuCore[];
  active: number | null;
  watts: number | null;
}

export interface GpuReading {
  core_count: number | null;
  device_util: number | null;
  renderer_util: number | null;
  tiler_util: number | null;
  memory_in_use: number | null;
  active: number | null;
  freq_mhz: number | null;
  freq_max_mhz: number | null;
  watts: number | null;
  per_core: null;
  per_core_reason: string;
}

export type BatteryReading =
  | { status: "unavailable"; error: string }
  | {
      status: "ok";
      percent: number | null;
      state: "charging" | "discharging" | "assisting" | "full" | "not_charging";
      state_label: string;
      external_connected: boolean;
      /** + into the battery, - out of it */
      amperage_ma: number | null;
      voltage_v: number | null;
      battery_watts: number | null;
      system_watts: number | null;
      adapter_in_watts: number | null;
      adapter: { watts: number | null; description: string | null; voltage_v: number | null; current_ma: number | null } | null;
      minutes_to_full: number | null;
      minutes_to_empty: number | null;
      capacity_mah: number | null;
      full_capacity_mah: number | null;
      design_capacity_mah: number | null;
      health_percent: number | null;
      cycle_count: number | null;
      design_cycle_count: number | null;
      temperature_c: number | null;
      cell_voltages_v: number[];
      charger: { charging_current_ma: number | null; charging_voltage_mv: number | null };
      daily_soc: { min: number | null; max: number | null };
      permanent_failure: boolean;
    };

export type SensorsData =
  | { status: "unavailable"; error: string }
  | {
      status: "ok";
      temperatures: { groups: SensorGroup[]; other: Record<string, number> };
      fans: SensorFan[];
      power: {
        system: SensorPower[];
        components: SensorPower[];
        clusters: Record<string, number>;
        rails: Record<string, number>;
        energy_error: string | null;
        interval_ms: number | null;
      };
      cpu: { clusters: CpuCluster[]; core_count: number; total_active: number | null };
      gpu: GpuReading;
      battery: BatteryReading;
    };

/** GET /api/health/metrics/history — collector store, bucketed server-side. */
export type MetricsHistory =
  | { status: "unavailable"; error: string }
  | {
      status: "ok" | "empty";
      tier: "5s" | "1m" | "1h";
      step: number;
      since: number;
      until: number;
      ts: number[];
      avg: Record<string, (number | null)[]>;
      max: Record<string, (number | null)[]>;
      collector: { last_sample: number | null; running: boolean };
    };
