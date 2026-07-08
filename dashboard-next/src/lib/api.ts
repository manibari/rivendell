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
  daily: {
    date: string;
    sessions: number;
    messages: number;
    tokens_total: number;
    cost_usd: number;
  }[];
  models: {
    model: string;
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
  }[];
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
}

export interface SkillDetail extends SkillInfo {
  content: string;
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
