"""Port registry check: intent (ports.conf) against reality (kernel + docker).

One implementation shared by the dashboard (/api/ports) and `sk check ports`,
so the two can never disagree about what a conflict is.

ports.conf line:  PORT | PROJECT | SERVICE | OWNER | NOTES
OWNER says how to recognise the rightful occupant of a live port:
    ~/Code/X or /abs/path   listener's working dir, or docker compose
                            working_dir label, starts with this path
    docker:<container>      that docker container publishes the port
    app:<prefix>            listener command starts with <prefix> (desktop apps)
    -                       claimed, occupant not checked

Statuses per port:
    live       listening, and the occupant matches a claim
    conflict   listening but NOT by any claimant (occupied), or two projects
               claim the same port (duplicate) -- the 8081 case, where
               mops_dbs and trip-atlas both expected it
    idle       claimed, nothing listening (reserved)
    wild       listening, nobody claimed it

Added 2026-09-27 (Peter): trip-atlas OTP sat on mops_dbs's 8081 and nothing
said so, because the old check only asked "is this port registered", never
"is the registered project the one using it".
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CONF = HERE / "ports.conf"
EPHEMERAL = 49152  # IANA dynamic range: a new number every boot, never registered


@dataclass
class Claim:
    port: int
    project: str
    service: str
    owner: str
    notes: str = ""


@dataclass
class Occupant:
    command: str = ""
    pid: str = ""
    cwd: str | None = None
    container: str | None = None
    folder: str | None = None       # docker compose working_dir
    compose_project: str | None = None
    image: str | None = None


@dataclass
class PortState:
    port: int
    status: str
    claims: list[Claim] = field(default_factory=list)
    occupant: Occupant | None = None
    owner: Claim | None = None      # the claim the occupant matched
    conflict: str | None = None     # "occupied" | "duplicate"
    detail: str = ""


def parse_conf(path: Path = CONF) -> list[Claim]:
    claims: list[Claim] = []
    if not path.exists():
        return claims
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if not parts[0].isdigit():
            continue
        parts += [""] * (5 - len(parts))
        claims.append(Claim(int(parts[0]), parts[1], parts[2], parts[3] or "-", parts[4]))
    return claims


def _lsof() -> str | None:
    # launchd's PATH lacks /usr/sbin, where macOS keeps lsof.
    return next((b for b in (shutil.which("lsof"), "/usr/sbin/lsof", "/usr/bin/lsof")
                 if b and Path(b).exists()), None)


def listeners() -> tuple[dict[int, Occupant], str | None]:
    lsof = _lsof()
    if lsof is None:
        return {}, "lsof not found"
    try:
        out = subprocess.run([lsof, "-nP", "-iTCP", "-sTCP:LISTEN"],
                             capture_output=True, text=True, timeout=8).stdout
    except Exception as exc:  # noqa: BLE001
        return {}, str(exc)
    occ: dict[int, Occupant] = {}
    for line in out.splitlines()[1:]:
        m = re.search(r":(\d+)(?:\s|\s*\()", line)
        if not m:
            continue
        cols = line.split()
        occ.setdefault(int(m.group(1)), Occupant(command=cols[0], pid=cols[1] if len(cols) > 1 else ""))
    pids = sorted({o.pid for o in occ.values() if o.pid})
    cwds: dict[str, str] = {}
    if pids:
        try:
            res = subprocess.run([lsof, "-a", "-d", "cwd", "-Fpn", "-p", ",".join(pids)],
                                 capture_output=True, text=True, timeout=8).stdout
            pid = ""
            for ln in res.splitlines():
                if ln.startswith("p"):
                    pid = ln[1:]
                elif ln.startswith("n") and pid:
                    cwds[pid] = ln[1:]
        except Exception:  # noqa: BLE001
            pass
    for o in occ.values():
        o.cwd = cwds.get(o.pid)
    return occ, None


def docker_ports() -> tuple[dict[int, Occupant], str | None]:
    try:
        ids = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True, timeout=8)
    except FileNotFoundError:
        return {}, "docker not installed"
    except Exception as exc:  # noqa: BLE001
        return {}, str(exc)
    if ids.returncode != 0:
        return {}, (ids.stderr or "docker ps failed").strip()
    if not ids.stdout.split():
        return {}, None
    try:
        data = json.loads(subprocess.run(["docker", "inspect", *ids.stdout.split()],
                                         capture_output=True, text=True, timeout=12).stdout or "[]")
    except Exception as exc:  # noqa: BLE001
        return {}, str(exc)
    out: dict[int, Occupant] = {}
    for c in data:
        labels = (c.get("Config") or {}).get("Labels") or {}
        for bindings in ((c.get("NetworkSettings") or {}).get("Ports") or {}).values():
            for b in bindings or []:
                hp = b.get("HostPort")
                if hp and hp.isdigit():
                    out.setdefault(int(hp), Occupant(
                        command="docker",
                        container=(c.get("Name") or "").lstrip("/"),
                        folder=labels.get("com.docker.compose.project.working_dir"),
                        compose_project=labels.get("com.docker.compose.project"),
                        image=(c.get("Config") or {}).get("Image"),
                    ))
    return out, None


def _under(path: str | None, prefix: str) -> bool:
    if not path:
        return False
    p = os.path.realpath(path).lower()
    q = os.path.realpath(os.path.expanduser(prefix)).lower().rstrip("/")
    return p == q or p.startswith(q + "/")


def matches(claim: Claim, occ: Occupant) -> bool:
    o = claim.owner
    if o in ("", "-"):
        return True
    if o.startswith("docker:"):
        return occ.container == o[len("docker:"):]
    if o.startswith("app:"):
        return occ.command.lower().startswith(o[len("app:"):].lower())
    return _under(occ.folder, o) or _under(occ.cwd, o)


def describe(occ: Occupant) -> str:
    if occ.container:
        return f"docker {occ.container}" + (f" ({occ.folder})" if occ.folder else "")
    where = f" in {occ.cwd}" if occ.cwd and occ.cwd != "/" else ""
    return f"{occ.command} pid {occ.pid}{where}"


def evaluate(conf: Path | None = None) -> tuple[list[PortState], dict[str, str | None]]:
    claims = parse_conf(conf or Path(os.environ.get("RIVENDELL_PORTS_CONF", CONF)))
    lst, lerr = listeners()
    dck, derr = docker_ports()
    live: dict[int, Occupant] = {}
    for port, occ in lst.items():
        if port < EPHEMERAL:
            live[port] = occ
    for port, occ in dck.items():
        base = live.get(port)
        if base is not None:  # keep the lsof pid/cwd, add docker identity
            occ.pid, occ.cwd = base.pid, base.cwd
        live[port] = occ

    by_port: dict[int, list[Claim]] = {}
    for c in claims:
        by_port.setdefault(c.port, []).append(c)

    states: list[PortState] = []
    for port in sorted(set(by_port) | set(live)):
        cl = by_port.get(port, [])
        occ = live.get(port)
        projects = sorted({c.project for c in cl})
        if occ is None:
            st = PortState(port, "idle", cl)
            if len(projects) > 1:
                st.status, st.conflict = "conflict", "duplicate"
                st.detail = f"{' 與 '.join(projects)} 都登記了 {port}，只能有一個能啟動"
            states.append(st)
            continue
        if not cl:
            states.append(PortState(port, "wild", cl, occ, detail=f"未登記：{describe(occ)}"))
            continue
        owner = next((c for c in cl if matches(c, occ)), None)
        st = PortState(port, "live", cl, occ, owner)
        if owner is None:
            st.status, st.conflict = "conflict", "occupied"
            st.detail = f"登記給 {', '.join(projects)}，實際被 {describe(occ)} 佔用"
        elif len(projects) > 1:
            st.status, st.conflict = "conflict", "duplicate"
            others = [p for p in projects if p != owner.project]
            st.detail = f"{owner.project} 正在用；{', '.join(others)} 也登記了 {port}，啟動時會撞"
        states.append(st)
    return states, {"listener_error": lerr, "docker_error": derr}


def main(argv: list[str]) -> int:
    states, errs = evaluate()
    conflicts = [s for s in states if s.status == "conflict"]
    wild = [s for s in states if s.status == "wild"]
    if "--json" in argv:
        print(json.dumps({"conflicts": len(conflicts), "wild": len(wild),
                          "ports": [asdict(s) for s in states], **errs}, ensure_ascii=False))
        return 1 if conflicts or wild else 0
    for label, group in (("Conflicts", conflicts), ("Unclaimed listeners", wild)):
        if not group:
            continue
        print(f"{label} ({len(group)}):")
        for s in group:
            print(f"  {s.port:<6} {s.detail}")
        print()
    idle = [s for s in states if s.status == "idle"]
    if idle and "--quiet" not in argv:
        print(f"Claimed but idle ({len(idle)}):")
        for s in idle:
            print(f"  {s.port:<6} {' / '.join(f'{c.project} {c.service}' for c in s.claims)}")
        print()
    print(f"Total: {len(conflicts)} conflict, {len(wild)} unclaimed")
    return 1 if conflicts or wild else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
