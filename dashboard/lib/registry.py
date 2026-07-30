"""Parse the agent registry — one markdown file per agent under agents/registry/.

Single source of truth (SoT) for every scheduled unit. Consumed by:
  - bin/sk-registry-gen (CLI: generate agents.conf lines, validate, drift check)
  - dashboard/lib/agents.py (dashboard agent cards)

Two-layer model: this file IS the knowledge-management layer (agent identity,
persona, skills, mission). The scheduling layer (launchd) consumes the generated
conf. agents.conf itself is an un-committed build artifact — registry is the only
committed SoT. See docs/requirements/agent-registry.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml  # already a declared dependency (dashboard-next/api/requirements.txt)

# ─── Schema constants ───
SCHEMA_VERSION = 2
KINDS = ("script", "claude", "service", "ooda")
PDCA_ROLES = ("plan", "do", "check", "act")
SCHEDULE_TYPES = ("interval", "calendar", "calendar_multi", "keepalive")
LABEL_PREFIX = "com.sk.agent"

# D6: kind:ooda needs the Lever-2 wake executor to run. Until that ships, an
# enabled ooda agent would generate a plist whose entry is empty → a broken,
# no-op launchd job. Flip to True when the executor lands.
OODA_EXECUTOR_AVAILABLE = False

# Fields absorbed from the retired .claude/agents.json (governance layer).
_AGENTS_JSON_DEFAULTS: dict[str, Any] = {
    "merge_strategy": "auto",
    "allowed_paths": list,
    "forbidden_paths": list,
    "max_files_changed": 0,
    "qa_pre_commit": "off",
}


@dataclass
class Finding:
    """One validation result. level is FAIL or WARN."""

    level: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.message}"


@dataclass
class RegistryAgent:
    """One agent's identity, parsed from agents/registry/<name>.md frontmatter.

    The body (mission narrative) is kept verbatim in `body` — the scheduling
    layer never reads it; only the wake executor uses it as prompt material.
    """

    # ── identity / scheduling (all kinds) ──
    name: str
    kind: str
    project: str
    entry: str = ""
    extra_args: str = ""
    enabled: bool = True
    schedule_type: str = ""
    schedule_value: str = ""
    log_dir: str = "reports"
    label_override: str = ""
    schema_version: int = SCHEMA_VERSION

    # ── rule layer (kind: claude | ooda) ──
    skills: list[str] = field(default_factory=list)
    tools: str = ""
    paths_forbid: list[str] = field(default_factory=list)
    budget_usd: float = 0.0

    # ── governance layer (absorbed from agents.json) ──
    merge_strategy: str = "auto"
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    max_files_changed: int = 0
    qa_pre_commit: str = "off"

    # ── autonomy layer (kind: ooda) ──
    pdca_role: str = ""
    mission: str = ""
    mission_metric: str = ""
    memory_dir: str = ""
    observe: list[str] = field(default_factory=list)
    authority: dict[str, Any] = field(default_factory=dict)
    handoff: dict[str, Any] = field(default_factory=dict)
    persona_card: str = ""

    body: str = ""
    source_path: Path | None = None

    @property
    def label(self) -> str:
        """launchd Label. Honors an explicit override (legacy service labels
        like com.sk.dashboard.api); otherwise derives com.sk.agent.<project>.<name>."""
        if self.label_override:
            return self.label_override
        return f"{LABEL_PREFIX}.{self.project}.{self.name}"

    def to_conf_tuple(self) -> tuple[str, str, str, str, str, str, str]:
        """Normalized 7-field tuple matching sk-setup-agents' pipe columns.

        Used for behavior-equivalence checks (compare tuples, not raw text, so
        whitespace/alignment differences never register as drift).
        """
        return (
            self.label,
            self.project,
            self.entry,
            self.schedule_type,
            self.schedule_value,
            self.log_dir,
            self.extra_args,
        )

    def to_conf_line(self) -> str:
        """One agents.conf line. Bash reads with IFS='|' and trims each field."""
        return " | ".join(self.to_conf_tuple())


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split a markdown file into (frontmatter dict, body).

    Frontmatter is the block between the first two `---` fences. Raises
    ValueError if the file has no frontmatter block.
    """
    if not text.startswith("---"):
        raise ValueError("no frontmatter block (file must start with ---)")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("unterminated frontmatter block (missing closing ---)")
    fm = yaml.safe_load(parts[1]) or {}
    if not isinstance(fm, dict):
        raise ValueError("frontmatter is not a mapping")
    return fm, parts[2].lstrip("\n")


def parse_registry_file(path: str | Path) -> RegistryAgent:
    """Parse one registry markdown file into a RegistryAgent.

    Raises ValueError on malformed frontmatter (caller decides FAIL vs skip).
    Structural validation is separate — see validate().
    """
    path = Path(path)
    fm, body = _split_frontmatter(path.read_text())
    sched = fm.get("schedule") or {}

    return RegistryAgent(
        name=str(fm.get("name", "")),
        kind=str(fm.get("kind", "")),
        project=str(fm.get("project", "")),
        entry=str(fm.get("entry", "") or ""),
        extra_args=str(fm.get("extra_args", "") or ""),
        enabled=bool(fm.get("enabled", True)),
        schedule_type=str(sched.get("type", "")),
        schedule_value=str(sched.get("value", "")),
        log_dir=str(fm.get("log_dir", "reports")),
        label_override=str(fm.get("label", "") or ""),
        schema_version=int(fm.get("schema_version", SCHEMA_VERSION)),
        skills=list(fm.get("skills") or []),
        tools=str(fm.get("tools", "") or ""),
        paths_forbid=list(fm.get("paths_forbid") or []),
        budget_usd=float(fm.get("budget_usd", 0) or 0),
        merge_strategy=str(fm.get("merge_strategy", "auto")),
        allowed_paths=list(fm.get("allowed_paths") or []),
        forbidden_paths=list(fm.get("forbidden_paths") or []),
        max_files_changed=int(fm.get("max_files_changed", 0) or 0),
        qa_pre_commit=str(fm.get("qa_pre_commit", "off")),
        pdca_role=str(fm.get("pdca_role", "") or ""),
        mission=str(fm.get("mission", "") or ""),
        mission_metric=str(fm.get("mission_metric", "") or ""),
        memory_dir=str(fm.get("memory_dir", "") or ""),
        observe=list(fm.get("observe") or []),
        authority=dict(fm.get("authority") or {}),
        handoff=dict(fm.get("handoff") or {}),
        persona_card=str(fm.get("persona_card", "") or ""),
        body=body,
        source_path=path,
    )


def validate(
    agent: RegistryAgent,
    known_skills: set[str] | None = None,
) -> list[Finding]:
    """Structural + semantic validation of one agent.

    known_skills: if provided, each skill in the whitelist must be a member
    (built-in Claude Code skills are exempt — the caller pre-filters them).
    Left None to skip the skill-existence check (keeps registry.py filesystem-light).
    """
    findings: list[Finding] = []

    def fail(msg: str) -> None:
        findings.append(Finding("FAIL", msg))

    def warn(msg: str) -> None:
        findings.append(Finding("WARN", msg))

    # ── required fields (all kinds) ──
    if not agent.name:
        fail("missing required field: name")
    if agent.kind not in KINDS:
        fail(f"kind must be one of {KINDS}, got {agent.kind!r}")
    if not agent.project:
        fail("missing required field: project")

    # filename must equal name
    if agent.source_path is not None and agent.name:
        stem = agent.source_path.stem
        if stem != agent.name:
            fail(f"filename {stem!r} != frontmatter name {agent.name!r}")

    # schedule
    if agent.schedule_type not in SCHEDULE_TYPES:
        fail(f"schedule.type must be one of {SCHEDULE_TYPES}, got {agent.schedule_type!r}")
    if agent.schedule_type != "keepalive" and not agent.schedule_value:
        fail(f"schedule.value required for schedule.type={agent.schedule_type}")

    # entry required for runnable kinds; ooda goes through the executor (no entry)
    if agent.kind in ("script", "claude", "service") and not agent.entry:
        fail(f"kind={agent.kind} requires entry")

    # ── kind: ooda autonomy layer ──
    if agent.kind == "ooda":
        if agent.pdca_role not in PDCA_ROLES:
            fail(f"ooda requires pdca_role in {PDCA_ROLES}, got {agent.pdca_role!r}")
        if not agent.mission:
            fail("ooda requires mission")
        if not agent.memory_dir:
            fail("ooda requires memory_dir")
        # D6: enabled ooda with no executor would generate a broken plist
        if agent.enabled and not OODA_EXECUTOR_AVAILABLE:
            fail(
                "kind=ooda + enabled=true but the wake executor (Lever 2) is not "
                "available yet — set enabled=false until it ships"
            )

    # ── skill whitelist existence ──
    if known_skills is not None and agent.kind in ("claude", "ooda"):
        for skill in agent.skills:
            if skill not in known_skills:
                fail(f"skill {skill!r} not found in ~/.claude/skills/ (built-ins are exempt)")

    # ── soft references ──
    if agent.persona_card and agent.source_path is not None:
        ref = agent.source_path.parent.parent / agent.persona_card
        if not ref.exists():
            warn(f"persona_card path not found: {agent.persona_card}")

    return findings


def load_registry_dir(registry_dir: str | Path) -> list[RegistryAgent]:
    """Parse every *.md (except TEMPLATE.md) under registry_dir.

    Malformed files raise ValueError from parse_registry_file — the CLI layer
    decides whether to fail the whole run or report per-file.
    """
    registry_dir = Path(registry_dir)
    agents: list[RegistryAgent] = []
    for md in sorted(registry_dir.glob("*.md")):
        if md.name == "TEMPLATE.md":
            continue
        agents.append(parse_registry_file(md))
    return agents


def check_label_collisions(agents: list[RegistryAgent]) -> list[Finding]:
    """Cross-file check: no two agents may share a name or a derived label."""
    findings: list[Finding] = []
    seen_names: dict[str, str] = {}
    seen_labels: dict[str, str] = {}
    for a in agents:
        src = str(a.source_path) if a.source_path else a.name
        if a.name in seen_names:
            findings.append(Finding("FAIL", f"duplicate name {a.name!r}: {src} vs {seen_names[a.name]}"))
        seen_names[a.name] = src
        if a.label in seen_labels:
            findings.append(Finding("FAIL", f"duplicate label {a.label!r}: {src} vs {seen_labels[a.label]}"))
        seen_labels[a.label] = src
    return findings
