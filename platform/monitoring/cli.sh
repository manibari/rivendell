# Service status command sourced by bin/sk.

cmd_status() {
  echo -e "${CYAN}=== Service Status ===${NC}"
  echo ""

  # Docker containers
  if command -v docker &>/dev/null; then
    local containers
    containers="$(docker ps --filter "name=sk-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null)"
    if [ -n "$containers" ]; then
      echo -e "${YELLOW}Docker services:${NC}"
      echo "$containers"
    else
      echo -e "${YELLOW}Docker:${NC} No sk- containers running"
    fi
  else
    echo -e "${YELLOW}Docker:${NC} not installed"
  fi

  echo ""

  # Active profile
  local active
  active="$(get_active_profile)"
  echo -e "${YELLOW}Active profile:${NC} ${active:-<none>}"

  echo ""

  # Registered agents (launchd on macOS, systemd --user elsewhere)
  if svc_supported; then
    echo -e "${YELLOW}Agents (${SK_PLATFORM}):${NC}"
    while IFS=$'\t' read -r label pid status; do
      [ -z "$label" ] && continue
      if [ "$pid" != "-" ] && [ "$pid" != "0" ]; then
        echo -e "  ${GREEN}running${NC}  $label (pid=$pid)"
      elif [ "$status" = "0" ]; then
        echo -e "  ${YELLOW}idle${NC}     $label"
      else
        echo -e "  ${RED}error${NC}    $label (exit=$status)"
      fi
    done < <(svc_list)
  fi

  echo ""

  # Skills deployment
  local total
  total="$(find "$SKILLS_DIR" -name "SKILL.md" -maxdepth 3 2>/dev/null | wc -l | tr -d ' ')"
  while IFS= read -r deploy_target; do
    local deployed
    deployed="$(find "$deploy_target" -maxdepth 1 -type l 2>/dev/null | wc -l | tr -d ' ')"
    echo -e "${YELLOW}Skills ($(deploy_label "$deploy_target")):${NC} $deployed/$total deployed"
  done < <(deploy_targets)
}
