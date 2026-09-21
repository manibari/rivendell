# Deployment profile and service commands sourced by bin/sk.

# Parse profiles.conf — output: type|field1|field2|...
# Usage: parse_profile "dev-full"
parse_profile() {
  local name="$1"
  local in_section=false
  while IFS= read -r line; do
    # Strip comments and blank lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    # Section header
    if [[ "$line" =~ ^\[([a-zA-Z0-9_-]+)\] ]]; then
      if [ "${BASH_REMATCH[1]}" = "$name" ]; then
        in_section=true
      else
        $in_section && break
      fi
      continue
    fi
    $in_section || continue
    # Parse pipe-delimited fields, trim whitespace
    local type="" f1="" f2="" f3="" f4=""
    IFS='|' read -r type f1 f2 f3 f4 <<< "$line"
    type="$(echo "$type" | xargs)"
    f1="$(echo "$f1" | xargs)"
    f2="$(echo "$f2" | xargs)"
    f3="$(echo "$f3" | xargs)"
    f4="$(echo "$f4" | xargs)"
    echo "${type}|${f1}|${f2}|${f3}|${f4}"
  done < "$PROFILES_CONF"
}

# List all profile names
list_profiles() {
  grep -oP '(?<=^\[)[a-zA-Z0-9_-]+(?=\])' "$PROFILES_CONF" 2>/dev/null || \
    sed -n 's/^\[\([a-zA-Z0-9_-]*\)\]/\1/p' "$PROFILES_CONF"
}

get_active_profile() {
  if [ -f "$ACTIVE_PROFILE_FILE" ]; then
    cat "$ACTIVE_PROFILE_FILE"
  else
    echo ""
  fi
}

# Get compose profile flags for a given profile name
get_compose_profiles() {
  local name="$1"
  parse_profile "$name" | while IFS='|' read -r type f1 f2 f3 f4; do
    [ "$type" = "project" ] && echo "$f2"
  done | sort -u
}

cmd_profile() {
  local subcmd="${1:-list}"
  case "$subcmd" in
    list)
      echo -e "${CYAN}Available profiles:${NC}"
      echo ""
      local active
      active="$(get_active_profile)"
      while IFS= read -r name; do
        local desc=""
        desc="$(parse_profile "$name" | grep '^option|description|' | head -1 | cut -d'|' -f3)"
        if [ "$name" = "$active" ]; then
          echo -e "  ${GREEN}* $name${NC}  $desc"
        else
          echo -e "    $name  $desc"
        fi
      done < <(list_profiles)
      ;;
    show)
      local name="${2:?Usage: sk profile show <name>}"
      echo -e "${CYAN}Profile: $name${NC}"
      echo ""
      echo -e "${YELLOW}Projects:${NC}"
      parse_profile "$name" | while IFS='|' read -r type f1 f2 f3 f4; do
        case "$type" in
          project)
            if [ "$f1" = "." ]; then
              echo -e "  rivendell ($f2)"
            else
              echo -e "  $f3  ← $f1  [compose: $f2]"
            fi
            ;;
          agents)
            echo -e "  ${CYAN}agent:${NC} $f1"
            ;;
          option)
            echo -e "  ${YELLOW}$f1:${NC} $f2"
            ;;
        esac
      done
      ;;
    set)
      local name="${2:?Usage: sk profile set <name>}"
      # Validate profile exists
      if ! list_profiles | grep -qx "$name"; then
        echo -e "${RED}Error:${NC} Profile '$name' not found."
        echo "Available: $(list_profiles | tr '\n' ' ')"
        exit 1
      fi
      echo "$name" > "$ACTIVE_PROFILE_FILE"
      echo -e "${GREEN}Active profile set to:${NC} $name"
      ;;
    current)
      local active
      active="$(get_active_profile)"
      if [ -z "$active" ]; then
        echo "No active profile. Run: sk profile set <name>"
      else
        echo "$active"
      fi
      ;;
    *)
      echo "Usage: sk profile <list|show|set|current> [name]"
      ;;
  esac
}

cmd_up() {
  local profile_name=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --profile) profile_name="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  if [ -z "$profile_name" ]; then
    profile_name="$(get_active_profile)"
  fi
  if [ -z "$profile_name" ]; then
    echo -e "${RED}Error:${NC} No profile specified. Use --profile <name> or run: sk profile set <name>"
    exit 1
  fi

  echo -e "${CYAN}Starting services for profile:${NC} $profile_name"

  local flags=""
  while IFS= read -r p; do
    [ -n "$p" ] && flags="$flags --profile $p"
  done < <(get_compose_profiles "$profile_name")

  echo -e "Compose profiles:${YELLOW}$flags${NC}"
  PROJECTS_DIR="$PROJECTS_DIR" docker compose -f "$COMPOSE_FILE" $flags up -d --build
}

cmd_down() {
  local profile_name
  profile_name="$(get_active_profile)"

  if [ -n "$profile_name" ]; then
    local flags=""
    while IFS= read -r p; do
      [ -n "$p" ] && flags="$flags --profile $p"
    done < <(get_compose_profiles "$profile_name")
    PROJECTS_DIR="$PROJECTS_DIR" docker compose -f "$COMPOSE_FILE" $flags down
  else
    docker compose -f "$COMPOSE_FILE" down
  fi
}

cmd_env() {
  local target_project="${1:-}"

  # Collect projects from active profile (or all if no profile)
  local profile_name
  profile_name="$(get_active_profile)"

  if [ -z "$profile_name" ] && [ -z "$target_project" ]; then
    echo -e "${RED}Error:${NC} No active profile. Specify a project or run: sk profile set <name>"
    exit 1
  fi

  _check_env_for_dir() {
    local dir="$1" name="$2"
    local example="$dir/.env.example"
    local actual="$dir/.env"

    if [ ! -f "$example" ]; then
      echo -e "  ${YELLOW}skip${NC}  $name (no .env.example)"
      return
    fi

    if [ ! -f "$actual" ]; then
      echo -e "  ${RED}missing${NC}  $name/.env"
      echo -n "  Copy from .env.example? [Y/n] "
      read -r ans
      if [ "${ans:-y}" != "n" ]; then
        cp "$example" "$actual"
        echo -e "  ${GREEN}created${NC} $actual"
        # Apply shared env if available
        if [ -f "$ENV_SHARED_FILE" ]; then
          while IFS='=' read -r key val; do
            [[ "$key" =~ ^[[:space:]]*# ]] && continue
            [ -z "$key" ] && continue
            if grep -q "^${key}=" "$actual"; then
              # temp+mv, not `sed -i ''` — GNU sed rejects the BSD empty-suffix
              # form and the substitution never lands on Linux.
              _sed_tmp="$(mktemp)"
              sed "s|^${key}=.*|${key}=${val}|" "$actual" > "$_sed_tmp" && mv "$_sed_tmp" "$actual"
              echo -e "  ${GREEN}shared${NC}  $key (from .env.shared)"
            fi
          done < "$ENV_SHARED_FILE"
        fi
        # Warn about empty required keys
        grep -E '^[A-Z_]+=($|your_|changeme|TODO)' "$actual" 2>/dev/null | while IFS='=' read -r key _; do
          echo -e "  ${RED}required${NC}  $key needs a value"
        done
      fi
    else
      # Check for new keys in example not in actual
      local missing=0
      while IFS='=' read -r key _; do
        [[ "$key" =~ ^[[:space:]]*# ]] && continue
        [ -z "$key" ] && continue
        if ! grep -q "^${key}=" "$actual"; then
          echo -e "  ${YELLOW}new key${NC}  $name: $key (in .env.example but not in .env)"
          missing=$((missing + 1))
        fi
      done < "$example"
      if [ "$missing" -eq 0 ]; then
        echo -e "  ${GREEN}ok${NC}  $name"
      fi
    fi
  }

  echo -e "${CYAN}Checking .env files:${NC}"
  echo ""

  if [ -n "$target_project" ]; then
    local dir="$PROJECTS_DIR/$target_project"
    _check_env_for_dir "$dir" "$target_project"
  else
    parse_profile "$profile_name" | while IFS='|' read -r type f1 f2 f3 f4; do
      [ "$type" = "project" ] || continue
      [ "$f1" = "." ] && continue  # rivendell itself has no .env
      local dir="$PROJECTS_DIR/$f3"
      _check_env_for_dir "$dir" "$f3"
    done
  fi
}

cmd_update() {
  local rebuild=false
  [ "${1:-}" = "--rebuild" ] && rebuild=true

  local profile_name
  profile_name="$(get_active_profile)"
  if [ -z "$profile_name" ]; then
    echo -e "${RED}Error:${NC} No active profile. Run: sk profile set <name>"
    exit 1
  fi

  echo -e "${CYAN}Updating repos for profile:${NC} $profile_name"
  echo ""

  # Pull rivendell
  echo -e "${YELLOW}rivendell${NC}"
  git -C "$REPO_DIR" pull --ff-only 2>&1 | sed 's/^/  /'
  echo ""

  # Pull each project
  parse_profile "$profile_name" | while IFS='|' read -r type f1 f2 f3 f4; do
    [ "$type" = "project" ] || continue
    [ "$f1" = "." ] && continue
    local dir="$PROJECTS_DIR/$f3"
    if [ -d "$dir/.git" ]; then
      echo -e "${YELLOW}$f3${NC}"
      git -C "$dir" pull --ff-only 2>&1 | sed 's/^/  /'
    else
      echo -e "${RED}$f3${NC}: not cloned"
    fi
    echo ""
  done

  # Rebuild if requested
  if $rebuild; then
    echo -e "${CYAN}Rebuilding Docker images...${NC}"
    cmd_up --profile "$profile_name"
  fi

  # Skill symlinks are platform-neutral — this used to be gated on Darwin, which
  # meant a switch on linux/WSL silently left ~/.claude/skills/ pointing at the
  # previous machine's paths.
  echo -e "${CYAN}Re-deploying skills...${NC}"
  cmd_deploy
}
