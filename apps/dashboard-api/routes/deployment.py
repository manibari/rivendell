"""Deployment inventory API and its local read models."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()

# ── Ports ─────────────────────────────────────────────────────────────────────

def _infer_port_type(host_port: int) -> str:
    if host_port == 5432:
        return "DB"
    if host_port == 6379:
        return "Cache"
    if host_port == 8501:
        return "Streamlit"
    if 3000 <= host_port <= 3999:
        return "Frontend"
    if 8000 <= host_port <= 8999:
        return "API"
    return "Service"


def _infer_project(service_name: str) -> str:
    if service_name.startswith("dashboard"):
        return "dashboard"
    if service_name.startswith("nexus"):
        return "nexus"
    return service_name


def _infer_category(port_type: str) -> str:
    if port_type in ("Frontend", "Streamlit"):
        return "前端"
    if port_type == "API":
        return "後端"
    if port_type in ("DB", "Cache"):
        return "資料庫"
    return "其他"


def _parse_compose_host_port(port_spec: Any) -> int | None:
    """Return the host-side TCP port from Docker Compose short/long syntax."""
    if isinstance(port_spec, int):
        return port_spec

    if isinstance(port_spec, dict):
        published = port_spec.get("published")
        if published is None:
            return None
        try:
            return int(str(published))
        except ValueError:
            return None

    if not isinstance(port_spec, str):
        return None

    spec = port_spec.split("/", 1)[0]
    parts = spec.rsplit(":", 2)
    if len(parts) == 1:
        # Expose-only short syntax, no host mapping.
        return None
    try:
        return int(parts[-2])
    except ValueError:
        return None


def _listening_tcp_ports() -> tuple[dict[int, dict[str, str]], str | None]:
    """Return local listening TCP ports from lsof.

    The port map is a drift detector, not just a compose viewer:
    - declared + listening => live
    - declared + not listening => drift
    - listening + not declared => wild
    """
    # Do NOT rely on PATH. On macOS lsof lives in /usr/sbin, which is absent
    # from the PATH the launchd plist sets — so this worked in an interactive
    # shell and silently returned nothing under the service, making every port
    # look idle.
    import shutil

    lsof = next(
        (b for b in (shutil.which("lsof"), "/usr/sbin/lsof", "/usr/bin/lsof")
         if b and Path(b).exists()),
        None,
    )
    if lsof is None:
        return {}, "lsof not found (PATH, /usr/sbin, /usr/bin)"
    try:
        proc = subprocess.run(
            [lsof, "-nP", "-iTCP", "-sTCP:LISTEN"],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception as exc:
        return {}, str(exc)

    if proc.returncode not in (0, 1):
        return {}, (proc.stderr or proc.stdout or f"lsof exited {proc.returncode}").strip()

    listeners: dict[int, dict[str, str]] = {}
    for line in proc.stdout.splitlines()[1:]:
        match = re.search(r":(\d+)(?:\s|\s*\()", line)
        if not match:
            continue
        try:
            port = int(match.group(1))
        except ValueError:
            continue
        cols = line.split()
        listeners[port] = {
            "command": cols[0] if cols else "",
            "pid": cols[1] if len(cols) > 1 else "",
            "name": cols[-2] if len(cols) >= 2 and cols[-1] == "(LISTEN)" else (cols[-1] if cols else ""),
        }
    return listeners, None


def _load_ops_monitors() -> list[dict[str, Any]]:
    """Read the ops central-monitor SoT (~/projects/ops/monitors.toml), the SAME
    file ops/check.sh consumes — health definitions live in ONE place. [] if absent."""
    import tomllib

    p = Path.home() / "projects" / "ops" / "monitors.toml"
    if not p.exists():
        return []
    try:
        return tomllib.loads(p.read_text(encoding="utf-8")).get("app", [])
    except Exception:
        return []


def _deployment_health() -> dict[str, dict[str, Any]]:
    """Per-app deployment health from monitors.toml: health URL == 200 (with the
    optional X-Health-Key from OPS_KEY_<APP>) + no ERR: in the redeploy log tail.
    Keyed by app name (== docker compose project). A health URL unreachable from
    THIS host degrades to 'unknown' — never a false 'down' (the mac can't see WSL
    localhost apps; the WSL-hosted dashboard will)."""
    import subprocess
    import urllib.error
    import urllib.request

    out: dict[str, dict[str, Any]] = {}
    for app in _load_ops_monitors():
        name = app.get("name")
        if not name:
            continue
        status = "ok"
        reasons: list[str] = []

        url = app.get("url")
        if url:
            headers: dict[str, str] = {
                # Cloudflare in front of these apps 403s the default Python-urllib UA.
                "User-Agent": "Mozilla/5.0 (compatible; rivendell-dashboard)",
            }
            key = os.environ.get("OPS_KEY_" + name.upper().replace("-", "_"))
            if key:
                headers["X-Health-Key"] = key
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=4) as resp:
                    if resp.status != 200:
                        status = "down"
                        reasons.append(f"HTTP {resp.status}")
            except urllib.error.HTTPError as exc:
                status = "down"
                reasons.append(f"HTTP {exc.code}")
            except Exception:
                status = "unknown"
                reasons.append("health unreachable from this host")

        log = os.path.expanduser(app.get("redeploy_log") or "")
        if log and os.path.exists(log):
            try:
                tail = subprocess.run(
                    ["tail", "-c", "20000", log], capture_output=True, text=True, timeout=4
                ).stdout
                errs = [ln for ln in tail.splitlines() if "ERR:" in ln]
                if errs:
                    if status != "unknown":
                        status = "down"
                    reasons.append("log ERR: " + errs[-1].strip()[:80])
            except Exception:
                pass

        out[name] = {"status": status, "detail": "; ".join(reasons) or "healthy", "url": url}
    return out


def _docker_running_ports() -> tuple[dict[int, dict[str, Any]], str | None]:
    """Map host_port -> compose metadata (project, source folder, service,
    container) for every RUNNING docker container, via `docker inspect`.

    This is the authoritative owner/folder source — it answers "whose 5432 is
    this?" that a compose-service-name guess cannot, and it covers containers
    from EVERY repo (chimesflow / family-fiscal / tukey / ...), not just the one
    compose file this dashboard reads. Returns ({}, error) on failure.
    """
    import json as _json
    import subprocess

    try:
        ids = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True, timeout=8)
    except FileNotFoundError:
        return {}, "docker not installed"
    except Exception as exc:  # noqa: BLE001
        return {}, f"{type(exc).__name__}: {exc}"
    if ids.returncode != 0:
        return {}, (ids.stderr or "docker ps failed").strip()
    id_list = ids.stdout.split()
    if not id_list:
        return {}, None

    try:
        insp = subprocess.run(["docker", "inspect", *id_list], capture_output=True, text=True, timeout=12)
        data = _json.loads(insp.stdout) if insp.returncode == 0 else []
    except Exception as exc:  # noqa: BLE001
        return {}, f"{type(exc).__name__}: {exc}"

    out: dict[int, dict[str, Any]] = {}
    for c in data:
        cfg = c.get("Config") or {}
        labels = cfg.get("Labels") or {}
        meta = {
            "container": (c.get("Name") or "").lstrip("/"),
            "project": labels.get("com.docker.compose.project"),
            "folder": labels.get("com.docker.compose.project.working_dir"),
            "service": labels.get("com.docker.compose.service"),
            "image": cfg.get("Image"),
        }
        ports = (c.get("NetworkSettings") or {}).get("Ports") or {}
        for cport, bindings in ports.items():
            for b in bindings or []:
                hp = b.get("HostPort")
                if not hp:
                    continue
                try:
                    out.setdefault(int(hp), {**meta, "container_port": cport})
                except ValueError:
                    continue
    return out, None


_DESKTOP_PROJECTS = {"macOS", "tailscale", "Discord", "Steam", "WeChat"}


def _repo_of(path: str | None) -> str | None:
    """~/Code/X/... or ~/Rightek/engineering/repos/X/... -> X (the repo name)."""
    if not path or path == "/":
        return None
    home = str(Path.home())
    for root in ("Code", "code", "Rightek/engineering/repos", "Projects", "Company/engineering/repos"):
        prefix = f"{home}/{root}/"
        if path.startswith(prefix):
            return path[len(prefix):].split("/", 1)[0]
    return None


@router.get("/api/ports", tags=["Ports"])
async def api_ports() -> dict[str, Any]:
    """Registry (data/ports.conf) checked against the kernel and docker by
    lib.port_registry — the same code `sk check ports` runs, so the page and
    the CLI always agree. Status: live / conflict / drift (claimed, idle) /
    wild (unclaimed). rivendell's own docker-compose adds its opt-in profiles
    as declared-only rows."""
    from lib.port_registry import evaluate

    states, errs = evaluate()
    entries_by_port: dict[int, dict[str, Any]] = {}
    for st in states:
        occ = st.occupant
        claim = st.owner or (st.claims[0] if st.claims else None)
        folder = (occ.folder or (occ.cwd if occ.cwd and occ.cwd != "/" else None)) if occ else None
        if claim:
            project = claim.project
        else:
            project = (occ and (occ.compose_project or _repo_of(folder))) or "local"
        port_type = _infer_port_type(st.port)
        entries_by_port[st.port] = {
            "port": st.port,
            "service": claim.service if claim else (occ.container or occ.command if occ else "—"),
            "container": (occ.container if occ and occ.container else (f"pid:{occ.pid}" if occ and occ.pid else "—")),
            "type": port_type,
            "web": port_type not in ("DB", "Cache"),
            "category": _infer_category(port_type),
            "project": project,
            "status": {"idle": "drift"}.get(st.status, st.status),
            "declared": bool(st.claims),
            "source": "docker" if occ and occ.container else ("listener" if occ else "registry"),
            "folder": folder,
            "image": occ.image if occ else None,
            "system": project in _DESKTOP_PROJECTS or bool(st.claims and all(c.owner.startswith("app:") for c in st.claims)),
            "listener": {"command": occ.command, "pid": occ.pid} if occ else None,
            "conflict": st.conflict,
            "detail": st.detail,
            "claims": [{"project": c.project, "service": c.service, "notes": c.notes} for c in st.claims],
        }

    # rivendell's own compose profiles (news-stock / sales / marketing): opt-in,
    # shown as declared-only so the page still says they exist.
    try:
        import yaml
        dc_path = Path(os.environ.get("COMPOSE_FILE", str(Path(__file__).resolve().parent.parent.parent.parent / "docker-compose.yml")))
        dc = yaml.safe_load(dc_path.read_text()) if dc_path.exists() else {}
    except Exception:  # noqa: BLE001
        dc = {}
    for svc_name, svc_cfg in (dc or {}).get("services", {}).items():
        if not isinstance(svc_cfg, dict):
            continue
        for port_spec in svc_cfg.get("ports", []):
            hp = _parse_compose_host_port(port_spec)
            if hp is None or hp in entries_by_port:
                continue
            port_type = _infer_port_type(hp)
            entries_by_port[hp] = {
                "port": hp, "service": svc_name, "container": svc_cfg.get("container_name", svc_name),
                "type": port_type, "web": port_type not in ("DB", "Cache"),
                "category": _infer_category(port_type), "project": _infer_project(svc_name),
                "status": "drift", "declared": True, "source": "compose", "folder": None,
                "listener": None, "conflict": None, "detail": "rivendell docker-compose opt-in profile", "claims": [],
            }

    return {
        "ports": sorted(
            entries_by_port.values(),
            key=lambda e: ((e.get("project") or ""), e["port"], (e.get("service") or "")),
        ),
        "conflicts": sum(1 for e in entries_by_port.values() if e["status"] == "conflict"),
        "listener_error": errs.get("listener_error"),
        "docker_error": errs.get("docker_error"),
        "health": _deployment_health(),
    }
