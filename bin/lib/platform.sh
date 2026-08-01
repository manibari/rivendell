#!/usr/bin/env bash
# platform.sh — Service-manager adapter for the sk agent fleet.
#
# rivendell was born on macOS/launchd. This file is the ONLY place that knows
# which service manager is underneath; everything else calls svc_* and stays
# platform-neutral. When adding a third platform, this file is the whole diff.
#
# Interface (all take the plist/unit label, except where noted):
#   sk_platform                  -> darwin | wsl | linux
#   svc_dir                      -> where unit files live
#   svc_logdir                   -> where the service manager's own stdout/stderr go
#   svc_supported                -> 0 if this host can run agents at all
#   svc_generate proj_dir proj_name agent_name
#                                -> write unit file(s) for a scheduled agent
#   svc_generate_raw label proj_dir script sched_type sched_val [extra_args]
#                                -> same, from agents.conf's schema (the only
#                                   one that can express a keepalive service)
#   svc_load label               -> install + activate
#   svc_unload label             -> deactivate + remove unit file(s)
#   svc_is_loaded label          -> 0 if registered with the service manager
#   svc_is_running label         -> 0 if a process is live right now
#   svc_restart label            -> force a restart (watchdog path)
#   svc_last_exit label          -> last exit status, or "?" if unknown
#   svc_list                     -> "label<TAB>pid<TAB>status" for every com.sk.* unit
#   svc_boot_persist             -> make agents survive logout/reboot (no-op on darwin)
#
# Callers must source this AFTER setting REPO_DIR.
set -uo pipefail

# --- Platform detection -----------------------------------------------------
# WSL must be checked before generic linux: it IS linux, but its systemd is
# opt-in via /etc/wsl.conf and it has no boot-time login, so linger matters.
sk_platform() {
  case "$(uname -s)" in
    Darwin) echo "darwin" ;;
    Linux)
      if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
        echo "wsl"
      else
        echo "linux"
      fi
      ;;
    *) echo "unsupported" ;;
  esac
}

SK_PLATFORM="${SK_PLATFORM:-$(sk_platform)}"

# systemd is a hard requirement on linux/wsl. On WSL it only exists when
# /etc/wsl.conf has [boot] systemd=true — without it, pid 1 is init and every
# systemctl call fails with a confusing error rather than a clear one.
svc_supported() {
  case "$SK_PLATFORM" in
    darwin) command -v launchctl >/dev/null 2>&1 ;;
    wsl|linux)
      command -v systemctl >/dev/null 2>&1 && [ "$(ps -p 1 -o comm= 2>/dev/null)" = "systemd" ]
      ;;
    *) return 1 ;;
  esac
}

svc_unsupported_reason() {
  case "$SK_PLATFORM" in
    darwin) echo "launchctl not found — is this really macOS?" ;;
    wsl)
      if [ "$(ps -p 1 -o comm= 2>/dev/null)" != "systemd" ]; then
        echo "systemd is not pid 1. Add '[boot]\\nsystemd=true' to /etc/wsl.conf, then run 'wsl --shutdown' from Windows and reopen."
      else
        echo "systemctl not found."
      fi
      ;;
    linux) echo "systemd not available (systemctl missing or not pid 1)." ;;
    *) echo "Unsupported platform: $(uname -s)" ;;
  esac
}

# --- Paths ------------------------------------------------------------------
# SK_SVC_DIR redirects unit output somewhere harmless — used by --dry-run, which
# must render a unit without touching the live service manager's directory.
svc_dir() {
  if [ -n "${SK_SVC_DIR:-}" ]; then echo "$SK_SVC_DIR"; return; fi
  case "$SK_PLATFORM" in
    darwin) echo "$HOME/Library/LaunchAgents" ;;
    *)      echo "$HOME/.config/systemd/user" ;;
  esac
}

# On macOS this is deliberately ~/Library/Logs and NOT the project dir: launchd
# runs outside the TCC grant, so writing into ~/Documents/ silently fails.
# Linux has no such restriction, but keeping logs out of the repo is still right.
svc_logdir() {
  case "$SK_PLATFORM" in
    darwin) echo "$HOME/Library/Logs/sk-agent" ;;
    *)      echo "${XDG_STATE_HOME:-$HOME/.local/state}/sk-agent/log" ;;
  esac
}

# --- Unit generation --------------------------------------------------------
# Reads the same .claude/agents.json schema on every platform. The caller
# (bin/sk) owns agent_get_config; we re-read via python3 to stay self-contained.
_svc_cfg() {
  local agents_file="$1" agent_name="$2" field="$3"
  python3 -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
    val = data['agents'][sys.argv[2]]
    for key in sys.argv[3].split('.'):
        if isinstance(val, dict):
            val = val.get(key, '')
        else:
            val = ''
    if isinstance(val, list):
        print(' '.join(str(v) for v in val))
    else:
        print(val if val is not None else '')
except Exception:
    print('')
" "$agents_file" "$agent_name" "$field" 2>/dev/null
}

svc_label() {
  echo "com.sk.agent.${1}.${2}"
}

# launchd Weekday: 0 and 7 both mean Sunday, 1=Mon .. 6=Sat.
# systemd wants day names. Keep the agents.json schema (numeric, launchd-style)
# as the source of truth and translate here — the config format is the contract,
# not the platform.
_svc_weekday_name() {
  case "$1" in
    0|7) echo "Sun" ;;
    1) echo "Mon" ;;
    2) echo "Tue" ;;
    3) echo "Wed" ;;
    4) echo "Thu" ;;
    5) echo "Fri" ;;
    6) echo "Sat" ;;
    *) echo "Mon" ;;
  esac
}

_svc_generate_plist() {
  local proj_dir="$1" proj_name="$2" agent_name="$3"
  local agents_file="$proj_dir/.claude/agents.json"
  local label; label="$(svc_label "$proj_name" "$agent_name")"

  local script args_raw sched_type sched_hour sched_minute sched_weekday sched_interval logs_dir
  script="$(_svc_cfg "$agents_file" "$agent_name" script)"
  args_raw="$(_svc_cfg "$agents_file" "$agent_name" args)"
  sched_type="$(_svc_cfg "$agents_file" "$agent_name" schedule.type)"
  sched_hour="$(_svc_cfg "$agents_file" "$agent_name" schedule.hour)"
  sched_minute="$(_svc_cfg "$agents_file" "$agent_name" schedule.minute)"
  sched_weekday="$(_svc_cfg "$agents_file" "$agent_name" schedule.weekday)"
  sched_interval="$(_svc_cfg "$agents_file" "$agent_name" schedule.interval)"
  logs_dir="$(_svc_cfg "$agents_file" "$agent_name" logs)"
  [ -z "$logs_dir" ] && logs_dir="reports/"

  local full_logs="$proj_dir/$logs_dir"
  mkdir -p "$full_logs"

  local unit_dir; unit_dir="$(svc_dir)"
  mkdir -p "$unit_dir"
  local dest="$unit_dir/${label}.plist"

  local wrapper="$HOME/.local/bin/sk-agent-run"
  local prog_args="        <string>$wrapper</string>
        <string>$proj_dir</string>
        <string>$script</string>"
  if [ -n "$args_raw" ]; then
    for arg in $args_raw; do
      prog_args+="
        <string>$arg</string>"
    done
  fi

  local schedule_xml=""
  case "$sched_type" in
    daily)
      schedule_xml="    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>$sched_hour</integer>
        <key>Minute</key><integer>$sched_minute</integer>
    </dict>" ;;
    weekdays)
      schedule_xml="    <key>StartCalendarInterval</key>
    <array>"
      for wd in 1 2 3 4 5; do
        schedule_xml+="
        <dict>
            <key>Weekday</key><integer>$wd</integer>
            <key>Hour</key><integer>$sched_hour</integer>
            <key>Minute</key><integer>$sched_minute</integer>
        </dict>"
      done
      schedule_xml+="
    </array>" ;;
    weekly)
      schedule_xml="    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key><integer>$sched_weekday</integer>
        <key>Hour</key><integer>$sched_hour</integer>
        <key>Minute</key><integer>$sched_minute</integer>
    </dict>" ;;
    interval)
      schedule_xml="    <key>StartInterval</key>
    <integer>$sched_interval</integer>" ;;
  esac

  cat > "$dest" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$label</string>

    <key>ProgramArguments</key>
    <array>
$prog_args
    </array>

$schedule_xml

    <key>StandardOutPath</key>
    <string>${full_logs}${agent_name}-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>${full_logs}${agent_name}-stderr.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:$HOME/.npm-global/bin:$HOME/.local/bin</string>
    </dict>
</dict>
</plist>
PLIST

  echo "$dest"
}

# systemd splits what launchd fuses: the plist is one file describing both the
# job and its schedule; systemd needs a .service (the job) plus a .timer (when).
# An agent with no schedule gets a bare .service the caller starts directly.
_svc_generate_systemd() {
  local proj_dir="$1" proj_name="$2" agent_name="$3"
  local agents_file="$proj_dir/.claude/agents.json"
  local label; label="$(svc_label "$proj_name" "$agent_name")"
  local unit_dir; unit_dir="$(svc_dir)"
  mkdir -p "$unit_dir"

  local script args_raw sched_type sched_hour sched_minute sched_weekday sched_interval logs_dir
  script="$(_svc_cfg "$agents_file" "$agent_name" script)"
  args_raw="$(_svc_cfg "$agents_file" "$agent_name" args)"
  sched_type="$(_svc_cfg "$agents_file" "$agent_name" schedule.type)"
  sched_hour="$(_svc_cfg "$agents_file" "$agent_name" schedule.hour)"
  sched_minute="$(_svc_cfg "$agents_file" "$agent_name" schedule.minute)"
  sched_weekday="$(_svc_cfg "$agents_file" "$agent_name" schedule.weekday)"
  sched_interval="$(_svc_cfg "$agents_file" "$agent_name" schedule.interval)"
  logs_dir="$(_svc_cfg "$agents_file" "$agent_name" logs)"
  [ -z "$logs_dir" ] && logs_dir="reports/"

  local full_logs="$proj_dir/$logs_dir"
  mkdir -p "$full_logs"

  # No sk-agent-run wrapper here. That launcher exists only to setenv REPO_DIR
  # and chdir before exec'ing bash, because launchd runs outside the macOS TCC
  # grant and $(pwd) fails there. systemd gives us WorkingDirectory= and
  # Environment= natively, so going through the wrapper would add a compiled
  # C dependency to buy something the unit file already expresses.
  local exec_line="/bin/bash ${proj_dir}/${script}"
  [ -n "$args_raw" ] && exec_line+=" $args_raw"

  # Pad H:M — systemd's OnCalendar rejects a bare "9:5" that launchd accepts.
  local hh mm
  hh="$(printf '%02d' "${sched_hour:-0}" 2>/dev/null || echo 00)"
  mm="$(printf '%02d' "${sched_minute:-0}" 2>/dev/null || echo 00)"

  cat > "$unit_dir/${label}.service" <<SERVICE
[Unit]
Description=sk agent ${proj_name}/${agent_name}
After=network-online.target

[Service]
Type=oneshot
ExecStart=${exec_line}
WorkingDirectory=${proj_dir}
Environment=REPO_DIR=${proj_dir}
Environment=PATH=/usr/local/bin:/usr/bin:/bin:${HOME}/.npm-global/bin:${HOME}/.local/bin
StandardOutput=append:${full_logs}${agent_name}-stdout.log
StandardError=append:${full_logs}${agent_name}-stderr.log
SERVICE

  local on_calendar="" timer_body=""
  case "$sched_type" in
    daily)    on_calendar="*-*-* ${hh}:${mm}:00" ;;
    weekdays) on_calendar="Mon..Fri *-*-* ${hh}:${mm}:00" ;;
    weekly)   on_calendar="$(_svc_weekday_name "${sched_weekday:-1}") *-*-* ${hh}:${mm}:00" ;;
    interval)
      # launchd StartInterval fires N seconds after load and after each run.
      # OnActiveSec (relative to timer activation) + OnUnitActiveSec (after each
      # run) is the faithful analogue. NOT OnBootSec: on a host whose user
      # manager booted more than N seconds ago (linger keeps it up for weeks),
      # OnBootSec is already in the past and the timer fires the instant it
      # loads — an unwanted immediate run for a costly agent.
      timer_body="OnActiveSec=${sched_interval}
OnUnitActiveSec=${sched_interval}" ;;
  esac

  if [ -n "$on_calendar" ]; then
    timer_body="OnCalendar=${on_calendar}
Persistent=true"
  fi

  if [ -n "$timer_body" ]; then
    cat > "$unit_dir/${label}.timer" <<TIMER
[Unit]
Description=sk agent ${proj_name}/${agent_name} schedule

[Timer]
${timer_body}
Unit=${label}.service

[Install]
WantedBy=timers.target
TIMER
  else
    rm -f "$unit_dir/${label}.timer"
  fi

  systemctl --user daemon-reload 2>/dev/null || true
  echo "$unit_dir/${label}.service"
}

svc_generate() {
  case "$SK_PLATFORM" in
    darwin) _svc_generate_plist "$@" ;;
    *)      _svc_generate_systemd "$@" ;;
  esac
}

# --- Raw (agents.conf-driven) unit generation -------------------------------
# agents.conf speaks a different schedule vocabulary than .claude/agents.json:
#
#   keepalive | interval <sec> | calendar <[W:]H:M> | calendar_multi <W:H:M,...>
#
# It exists because the long-running services (dashboard api/web) are only
# declared there, and `keepalive` is the one thing the agents.json schema cannot
# express — that schema assumes every agent starts, works, and exits. Until the
# two files are merged, this path is what keeps a service alive.
#
#   svc_generate_raw label proj_dir script sched_type sched_val [extra_args]
svc_generate_raw() {
  case "$SK_PLATFORM" in
    darwin) _svc_generate_raw_plist "$@" ;;
    *)      _svc_generate_raw_systemd "$@" ;;
  esac
}

# "17:30" -> "17:30:00"; "3:17:30" -> "Wed *-*-* 17:30:00"
_svc_calendar_to_oncalendar() {
  local val="$1"
  local -a p; IFS=':' read -ra p <<< "$val"
  local wd="" hh mm
  if [ "${#p[@]}" -eq 3 ]; then
    wd="$(_svc_weekday_name "${p[0]}") "
    hh="${p[1]}"; mm="${p[2]}"
  else
    hh="${p[0]}"; mm="${p[1]}"
  fi
  # 10# strips the leading zero that would otherwise be read as octal.
  printf '%s*-*-* %02d:%02d:00' "$wd" "$((10#${hh:-0}))" "$((10#${mm:-0}))"
}

_svc_generate_raw_systemd() {
  local label="$1" proj_dir="$2" script="$3" sched_type="$4" sched_val="$5" extra_args="${6:-}"
  local unit_dir; unit_dir="$(svc_dir)"
  local log_dir; log_dir="$(svc_logdir)"
  mkdir -p "$unit_dir" "$log_dir"

  # No sk-agent-run wrapper on this path either — see _svc_generate_systemd.
  local exec_line="/bin/bash ${proj_dir}/${script}"
  [ -n "$extra_args" ] && exec_line+=" $extra_args"

  local svc_type="oneshot" extra_service="" install_block=""
  local timer_body=""

  case "$sched_type" in
    keepalive)
      # The launchd analogue of KeepAlive+RunAtLoad. WantedBy=default.target is
      # what makes it come back after a reboot; Restart=always is what makes it
      # come back after a crash or a stray kill.
      svc_type="simple"
      extra_service="Restart=always
RestartSec=5"
      install_block="
[Install]
WantedBy=default.target"
      ;;
    interval)
      # OnActiveSec (load-relative), not OnBootSec: on a long-lived user manager
      # OnBootSec is already elapsed and the timer fires the instant it loads.
      # See the matching note in _svc_generate_systemd.
      timer_body="OnActiveSec=${sched_val}
OnUnitActiveSec=${sched_val}"
      ;;
    calendar)
      timer_body="OnCalendar=$(_svc_calendar_to_oncalendar "$sched_val")
Persistent=true"
      ;;
    calendar_multi)
      # Repeated OnCalendar= lines accumulate — one firing per entry.
      local entry
      local -a entries; IFS=',' read -ra entries <<< "$sched_val"
      for entry in "${entries[@]}"; do
        entry="$(echo "$entry" | xargs)"
        [ -z "$entry" ] && continue
        timer_body+="OnCalendar=$(_svc_calendar_to_oncalendar "$entry")
"
      done
      timer_body+="Persistent=true"
      ;;
  esac

  cat > "$unit_dir/${label}.service" <<SERVICE
[Unit]
Description=sk service ${label}
After=network-online.target

[Service]
Type=${svc_type}
ExecStart=${exec_line}
WorkingDirectory=${proj_dir}
Environment=REPO_DIR=${proj_dir}
Environment=PATH=${SK_AGENT_PATH:-/usr/local/bin:/usr/bin:/bin:${HOME}/.npm-global/bin:${HOME}/.local/bin}
StandardOutput=append:${log_dir}/${label}-stdout.log
StandardError=append:${log_dir}/${label}-stderr.log
${extra_service}
${install_block}
SERVICE

  if [ -n "$timer_body" ]; then
    cat > "$unit_dir/${label}.timer" <<TIMER
[Unit]
Description=sk service ${label} schedule

[Timer]
${timer_body}
Unit=${label}.service

[Install]
WantedBy=timers.target
TIMER
  else
    rm -f "$unit_dir/${label}.timer"
  fi

  systemctl --user daemon-reload 2>/dev/null || true
  echo "$unit_dir/${label}.service"
}

_svc_generate_raw_plist() {
  local label="$1" proj_dir="$2" script="$3" sched_type="$4" sched_val="$5" extra_args="${6:-}"
  local unit_dir; unit_dir="$(svc_dir)"
  local log_dir; log_dir="$(svc_logdir)"
  mkdir -p "$unit_dir" "$log_dir"

  local runner="${SK_AGENT_RUN:-$HOME/.local/bin/sk-agent-run}"
  local prog_args="        <string>${runner}</string>
        <string>${proj_dir}</string>
        <string>${script}</string>"
  [ -n "$extra_args" ] && prog_args+="
        <string>${extra_args}</string>"

  local schedule=""
  case "$sched_type" in
    keepalive)
      schedule="    <key>KeepAlive</key>
    <true/>
    <key>RunAtLoad</key>
    <true/>" ;;
    interval)
      schedule="    <key>StartInterval</key>
    <integer>${sched_val}</integer>" ;;
    calendar)
      schedule="$(_svc_plist_calendar "$sched_val")" ;;
    calendar_multi)
      schedule="$(_svc_plist_calendar_multi "$sched_val")" ;;
  esac

  cat > "$unit_dir/${label}.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${label}</string>

    <key>ProgramArguments</key>
    <array>
${prog_args}
    </array>

${schedule}

    <key>StandardOutPath</key>
    <string>${log_dir}/${label}-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>${log_dir}/${label}-stderr.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>${SK_AGENT_PATH:-/usr/local/bin:/usr/bin:/bin}</string>
    </dict>
</dict>
</plist>
PLIST

  echo "$unit_dir/${label}.plist"
}

_svc_plist_calendar() {
  local -a p; IFS=':' read -ra p <<< "$1"
  local wd="" hh mm
  if [ "${#p[@]}" -eq 3 ]; then wd="${p[0]}"; hh="${p[1]}"; mm="${p[2]}"
  else hh="${p[0]}"; mm="${p[1]}"; fi
  echo "    <key>StartCalendarInterval</key>"
  echo "    <dict>"
  [ -n "$wd" ] && echo "        <key>Weekday</key><integer>$((10#$wd))</integer>"
  echo "        <key>Hour</key><integer>$((10#${hh:-0}))</integer>"
  echo "        <key>Minute</key><integer>$((10#${mm:-0}))</integer>"
  echo "    </dict>"
}

_svc_plist_calendar_multi() {
  local entry
  local -a entries; IFS=',' read -ra entries <<< "$1"
  echo "    <key>StartCalendarInterval</key>"
  echo "    <array>"
  for entry in "${entries[@]}"; do
    entry="$(echo "$entry" | xargs)"
    [ -z "$entry" ] && continue
    local -a p; IFS=':' read -ra p <<< "$entry"
    echo "        <dict>"
    [ "${#p[@]}" -eq 3 ] && echo "            <key>Weekday</key><integer>$((10#${p[0]}))</integer>"
    local h="${p[$((${#p[@]}-2))]}" m="${p[$((${#p[@]}-1))]}"
    echo "            <key>Hour</key><integer>$((10#$h))</integer>"
    echo "            <key>Minute</key><integer>$((10#$m))</integer>"
    echo "        </dict>"
  done
  echo "    </array>"
}

# --- Lifecycle --------------------------------------------------------------
_svc_has_timer() {
  [ -f "$(svc_dir)/${1}.timer" ]
}

svc_load() {
  local label="$1"
  case "$SK_PLATFORM" in
    darwin)
      launchctl load "$(svc_dir)/${label}.plist" 2>/dev/null
      ;;
    *)
      systemctl --user daemon-reload 2>/dev/null || true
      if _svc_has_timer "$label"; then
        systemctl --user enable --now "${label}.timer" 2>/dev/null
      else
        systemctl --user enable --now "${label}.service" 2>/dev/null
      fi
      ;;
  esac
}

svc_unload() {
  local label="$1"
  local dir; dir="$(svc_dir)"
  case "$SK_PLATFORM" in
    darwin)
      launchctl unload "$dir/${label}.plist" 2>/dev/null
      rm -f "$dir/${label}.plist"
      ;;
    *)
      if _svc_has_timer "$label"; then
        systemctl --user disable --now "${label}.timer" 2>/dev/null
      fi
      systemctl --user disable --now "${label}.service" 2>/dev/null
      rm -f "$dir/${label}.service" "$dir/${label}.timer"
      systemctl --user daemon-reload 2>/dev/null || true
      ;;
  esac
}

svc_is_loaded() {
  local label="$1"
  case "$SK_PLATFORM" in
    darwin) launchctl list "$label" &>/dev/null ;;
    *)
      # A timer-driven agent is "loaded" when its timer is enabled, even though
      # the .service sits inactive between runs — checking the service alone
      # would report every scheduled agent as dead.
      if _svc_has_timer "$label"; then
        systemctl --user is-enabled "${label}.timer" &>/dev/null
      else
        systemctl --user is-enabled "${label}.service" &>/dev/null
      fi
      ;;
  esac
}

svc_is_running() {
  local label="$1"
  case "$SK_PLATFORM" in
    darwin)
      local pid
      pid="$(launchctl list 2>/dev/null | awk -v l="$label" '$3 == l {print $1}')"
      [ -n "$pid" ] && [ "$pid" != "-" ] && [ "$pid" != "0" ]
      ;;
    *) systemctl --user is-active "${label}.service" &>/dev/null ;;
  esac
}

svc_restart() {
  local label="$1"
  case "$SK_PLATFORM" in
    darwin) launchctl kickstart -k "gui/$(id -u)/${label}" 2>/dev/null ;;
    *)      systemctl --user restart "${label}.service" 2>/dev/null ;;
  esac
}

svc_last_exit() {
  local label="$1"
  case "$SK_PLATFORM" in
    darwin)
      local st
      st="$(launchctl list "$label" 2>/dev/null | awk '/"LastExitStatus"/ {gsub(/[^0-9]/,"",$3); print $3}')"
      [ -z "$st" ] && st="$(launchctl list 2>/dev/null | awk -v l="$label" '$3 == l {print $2}')"
      echo "${st:-?}"
      ;;
    *)
      local st
      st="$(systemctl --user show "${label}.service" -p ExecMainStatus --value 2>/dev/null)"
      echo "${st:-?}"
      ;;
  esac
}

# Emits: label<TAB>pid<TAB>last_exit — one line per com.sk.* unit.
svc_list() {
  case "$SK_PLATFORM" in
    darwin)
      launchctl list 2>/dev/null | grep 'com\.sk' | awk '{print $3"\t"$1"\t"$2}'
      ;;
    *)
      local dir; dir="$(svc_dir)"
      [ -d "$dir" ] || return 0
      for unit in "$dir"/com.sk.*.service; do
        [ -f "$unit" ] || continue
        local label; label="$(basename "$unit" .service)"
        local pid st
        pid="$(systemctl --user show "${label}.service" -p MainPID --value 2>/dev/null)"
        if [ -z "$pid" ] || [ "$pid" = "0" ]; then
          pid="-"
        fi
        st="$(systemctl --user show "${label}.service" -p ExecMainStatus --value 2>/dev/null)"
        echo -e "${label}\t${pid}\t${st:-0}"
      done
      ;;
  esac
}

# launchd user agents start at login and die at logout — that's the macOS model
# and there's nothing to enable. systemd --user is the same by default, but
# linger makes the user manager start at boot and survive logout. On WSL this
# is what makes agents run without a terminal open.
svc_boot_persist() {
  case "$SK_PLATFORM" in
    darwin) return 0 ;;
    *)
      if loginctl show-user "$USER" -p Linger --value 2>/dev/null | grep -q yes; then
        return 0
      fi
      loginctl enable-linger "$USER" 2>/dev/null
      ;;
  esac
}
