---
name: Claude to Telegram
loop: platform
pdca: do
description: Guide for setting up a Telegram bridge to remotely control Claude Code sessions from Telegram. Covers two approaches with setup, security, and troubleshooting.
when_to_use: when user wants to interact with Claude Code remotely via Telegram, set up a Telegram bot bridge, or manage Claude Code sessions from mobile
version: 1.0.0
tags: [integration, telegram, remote, automation]
languages: all
user_invocable: true
---

# Claude to Telegram

## Overview

Run Claude Code on your machine, interact with it from Telegram on any device. This enables remote control of Claude Code sessions, tool approval via inline buttons, and mobile-friendly access to your development environment.

**Two approaches exist:**

| Feature | Claude-to-IM-skill | claude-code-telegram |
|---------|-------------------|---------------------|
| **Author** | op7418 (858+ stars) | RichardAtCT (2019+ stars) |
| **Type** | Claude Code skill (integrates natively) | Standalone Python daemon |
| **SDK** | Claude Agent SDK `query()` | Subprocess / API wrapper |
| **Install** | `npx skills add` or git clone | git clone + pip install |
| **Language** | TypeScript | Python |
| **Permission flow** | Inline buttons [Allow]/[Deny] with timeout | Configurable auto-approve or manual |
| **Multi-IM support** | Telegram, Slack, Discord, etc. | Telegram only |
| **Extras** | Lightweight, skill-native | Webhook API, cron scheduler, voice transcription, file upload, cost tracking, project threads |
| **Best for** | Quick setup, skill ecosystem users | Power users wanting full-featured Telegram bot |

**Recommendation:** Start with Claude-to-IM-skill for simplicity. Switch to claude-code-telegram if you need advanced features like scheduling, webhooks, or cost tracking.

## Quick Setup: Claude-to-IM-skill (Recommended)

### Prerequisites

- Node.js >= 20
- Claude Code installed and working
- Telegram bot token (see "Getting a Telegram Bot Token" below)
- Your Telegram user ID (see "Security Best Practices" below)

### Install

**Option A: via skills CLI**

```bash
npx skills add op7418/Claude-to-IM-skill
```

**Option B: manual clone**

```bash
git clone https://github.com/op7418/Claude-to-IM-skill ~/.claude/skills/claude-to-im
```

### Setup

Run inside Claude Code:

```
/claude-to-im setup
```

The interactive wizard will prompt for:
1. IM platform (select Telegram)
2. Bot token
3. Allowed user IDs (your Telegram user ID)
4. Permission timeout (default: 5 minutes)

Configuration is stored at `~/.claude-to-im/`.

### Start the Bridge

```
/claude-to-im start
```

### Management Commands

| Command | Description |
|---------|-------------|
| `/claude-to-im start` | Start the Telegram bridge daemon |
| `/claude-to-im stop` | Stop the daemon |
| `/claude-to-im status` | Check if daemon is running |
| `/claude-to-im logs` | View recent daemon logs |
| `/claude-to-im doctor` | Run diagnostics (connectivity, auth, config) |

### Architecture

- SKILL.md defines the skill interface
- TypeScript daemon runs in the background
- Uses Claude Agent SDK `query()` to interact with Claude Code programmatically
- Messages from Telegram are forwarded to Claude Code as prompts
- Tool use requests trigger inline buttons in Telegram: **[Allow]** / **[Deny]**
- 5-minute timeout on tool approvals (auto-deny if no response)
- All config and state stored at `~/.claude-to-im/`

## Alternative: claude-code-telegram (Feature-Rich)

### Prerequisites

- Python 3.11+
- Telegram bot token
- Claude Code installed and working

### Install

```bash
git clone https://github.com/RichardAtCT/claude-code-telegram.git
cd claude-code-telegram
pip install -r requirements.txt
```

### Configuration

Copy the example config and edit:

```bash
cp .env.example .env
chmod 600 .env
```

Set at minimum:
- `TELEGRAM_BOT_TOKEN` - your bot token
- `ALLOWED_USER_IDS` - comma-separated Telegram user IDs
- `CLAUDE_CODE_PATH` - path to Claude Code binary (usually `claude`)

### Two Modes

**Agentic Mode (default):** Natural conversation interface. Send messages as you would to Claude normally. The bot manages context, threads, and tool approvals.

**Classic Mode:** 13 structured commands for explicit control (e.g., `/ask`, `/project`, `/status`, `/cost`).

### Key Features

- **Webhook API** - trigger Claude Code tasks from external services
- **Cron scheduler** - schedule recurring tasks (e.g., daily code reviews)
- **Project threads** - separate Telegram threads per project directory
- **Voice transcription** - send voice messages, transcribed and forwarded to Claude
- **File upload** - send files via Telegram, available to Claude Code
- **Cost tracking** - monitor token usage and API costs
- **SQLite database** - persistent conversation history and state

### Start

```bash
python main.py
```

Or run as a systemd service for persistence.

## Getting a Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a **display name** for your bot (e.g., "My Claude Code")
4. Choose a **username** ending in `bot` (e.g., `my_claude_code_bot`)
5. BotFather replies with your **bot token** (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. Copy the token immediately

**Security:**
- NEVER commit the token to version control
- Store in environment variables or a config file with `chmod 600`
- If compromised, revoke immediately via BotFather `/revoke`

## Security Best Practices

### Allowed Users Whitelist

Both approaches support restricting access to specific Telegram user IDs. **Always configure this.** Without it, anyone who discovers your bot username can control your machine.

### Get Your Telegram User ID

1. Open Telegram and search for **@userinfobot**
2. Send `/start`
3. The bot replies with your numeric user ID (e.g., `123456789`)
4. Use this ID in your allowed users configuration

### Permission Gateway

Claude-to-IM-skill sends tool approval requests as inline buttons in Telegram. This means:
- File writes, command execution, and other tool uses require explicit approval
- 5-minute timeout auto-denies if you don't respond
- You maintain control even when away from your computer

### Additional Hardening

- **Run on a trusted machine only** - the bridge has the same access as your local Claude Code
- **Use a dedicated bot** - don't reuse a bot token across services
- **Mask secrets in logs** - both tools support log sanitization; verify it is enabled
- **Firewall** - if using claude-code-telegram's webhook mode, restrict inbound access
- **Review sessions** - periodically check `~/.claude-to-im/` logs or SQLite DB for unexpected activity

## Troubleshooting

### Daemon Won't Start

1. Run `/claude-to-im doctor` (or check logs manually)
2. Verify Node.js version: `node --version` (must be >= 20)
3. Check if port is already in use (for webhook mode)
4. Verify bot token is valid: send a test message to your bot, check BotFather

### Bot Not Responding

1. Confirm daemon is running: `/claude-to-im status`
2. Check your Telegram user ID is in the allowed list
3. Verify internet connectivity from the host machine
4. Check Telegram API status (rare, but possible outages)
5. Review logs: `/claude-to-im logs` or `~/.claude-to-im/logs/`

### Permission Denied Errors

1. Ensure Claude Code itself works locally first (`claude` in terminal)
2. Check file permissions on `~/.claude-to-im/` (should be owned by your user)
3. For claude-code-telegram: verify `CLAUDE_CODE_PATH` points to the correct binary

### Log Locations

| Tool | Log Path |
|------|----------|
| Claude-to-IM-skill | `~/.claude-to-im/logs/` |
| claude-code-telegram | `./logs/` in the project directory, or journal if using systemd |

### General Diagnostic Steps

1. Check config file syntax and values
2. Test bot token independently (curl the Telegram Bot API `getMe` endpoint)
3. Verify Claude Code works in isolation before debugging the bridge
4. Check system resources (RAM, disk) if daemon crashes silently
