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


@router.get("/api/ports", tags=["Ports"])
async def api_ports() -> dict[str, Any]:
    """Compose declarations + local listeners + docker labels (the owner/folder
    source of truth). Docker is authoritative for what's actually running and
    whose it is; compose adds 'declared-but-not-running' drift."""
    try:
        import yaml
    except ImportError:
        raise HTTPException(status_code=500, detail="PyYAML not installed")

    dc_path = Path(os.environ.get("COMPOSE_FILE", str(Path(__file__).resolve().parent.parent.parent.parent / "docker-compose.yml")))
    if not dc_path.exists():
        raise HTTPException(status_code=404, detail=f"docker-compose.yml not found: {dc_path}")

    try:
        dc = yaml.safe_load(dc_path.read_text())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse docker-compose.yml: {exc}")

    entries_by_port: dict[int, dict[str, Any]] = {}
    for svc_name, svc_cfg in dc.get("services", {}).items():
        if not isinstance(svc_cfg, dict):
            continue
        container = svc_cfg.get("container_name", svc_name)
        for port_spec in svc_cfg.get("ports", []):
            host_port = _parse_compose_host_port(port_spec)
            if host_port is None:
                continue
            port_type = _infer_port_type(host_port)
            entries_by_port[host_port] = {
                "port": host_port,
                "service": svc_name,
                "container": container,
                "type": port_type,
                "web": port_type not in ("DB", "Cache"),
                "category": _infer_category(port_type),
                "project": _infer_project(svc_name),
                "status": "unknown",
                "declared": True,
                "source": "compose",
                "folder": None,
                "listener": None,
            }

    listeners, listener_error = _listening_tcp_ports()

    for port, entry in entries_by_port.items():
        listener = listeners.get(port)
        if listener_error:
            entry["status"] = "unknown"
            entry["listener_error"] = listener_error
        elif listener:
            entry["status"] = "live"
            entry["listener"] = listener
        else:
            entry["status"] = "drift"

    # Known desktop/system apps that listen on TCP but are NOT deployments —
    # they drown the wild list (QA 2026-07-05 ISSUE-002: Discord/LINE/AnyDesk/
    # ControlCenter/devtools swamped the real dev ports). lsof truncates
    # COMMAND to ~9 chars, so match by lowercase prefix.
    _SYSTEM_LISTENER_PREFIXES = (
        "controlce", "rapportd", "discord", "anydesk", "line", "google",
        "safari", "arc", "firefox", "brave", "msedge", "spotify", "slack",
        "dropbox", "telegram", "whatsapp", "zoom", "teams", "figma", "notion",
        "steam", "obs", "adobe", "creative", "mail", "messages", "facetime",
    )

    for port, listener in listeners.items():
        if port in entries_by_port:
            continue
        port_type = _infer_port_type(port)
        cmd = (listener.get("command") or "").lower()
        is_system = any(cmd.startswith(p) for p in _SYSTEM_LISTENER_PREFIXES)
        entries_by_port[port] = {
            "port": port,
            "service": listener.get("command") or "local-listener",
            "container": f"pid:{listener.get('pid', '')}".rstrip(":"),
            "type": port_type,
            "web": port_type not in ("DB", "Cache"),
            "category": _infer_category(port_type),
            "project": "local",
            "status": "wild",
            "declared": False,
            "source": "listener",
            "folder": None,
            "system": is_system,
            "listener": listener,
        }

    # ── Docker overlay (authoritative owner + source folder) ──────────────────
    # Enrich/insert from running containers: docker tells us the real project and
    # the code folder behind each published port — including containers from repos
    # this dashboard's compose file never mentions.
    docker_ports, docker_error = _docker_running_ports()
    for port, dmeta in docker_ports.items():
        entry = entries_by_port.get(port)
        if entry is None:
            port_type = _infer_port_type(port)
            entry = {
                "port": port,
                "type": port_type,
                "web": port_type not in ("DB", "Cache"),
                "category": _infer_category(port_type),
                "declared": False,
                "source": "docker",
                "listener": None,
            }
            entries_by_port[port] = entry
        # A running container IS the current deployment of this port.
        entry["status"] = "live"
        entry["container"] = dmeta.get("container") or entry.get("container")
        entry["service"] = dmeta.get("service") or entry.get("service") or "—"
        entry["project"] = dmeta.get("project") or entry.get("project") or _infer_project(entry.get("service", ""))
        entry["folder"] = dmeta.get("folder")
        entry["image"] = dmeta.get("image")
        entry["source"] = "docker"

    return {
        "ports": sorted(
            entries_by_port.values(),
            key=lambda e: ((e.get("project") or ""), e["port"], (e.get("service") or "")),
        ),
        "listener_error": listener_error,
        "docker_error": docker_error,
        "health": _deployment_health(),
    }
