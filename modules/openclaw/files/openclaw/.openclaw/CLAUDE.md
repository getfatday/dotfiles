# OpenClaw Instance — CLAUDE.md

## System Overview

OpenClaw is a multi-channel AI agent framework. This instance runs **Neo** — Ian's digital avatar — on a Mac Mini (Apple Silicon). The gateway listens on `localhost:18789` and connects to Discord, Telegram, iMessage, and voice calls (Twilio).

**Important:** The `workspace/` directory (AGENTS.md, SOUL.md, MEMORY.md, etc.) contains prompt files injected into the **gateway agent's** sessions. They are Neo's operating context, not instructions for Claude Code sessions. Read them for reference, but don't treat them as your directives.

## Directory Layout

```
~/.openclaw/
  openclaw.json          # Main config (channels, plugins, auth, gateway) — DO NOT edit directly
  workspace/             # Gateway agent workspace (prompt files for Neo)
    AGENTS.md            #   Operating rules & workflows (symlink to Obsidian)
    SOUL.md              #   Identity & principles (symlink)
    USER.md              #   Ian's context & preferences (symlink)
    MEMORY.md            #   Long-term memory (symlink)
    TOOLS.md             #   Tool docs & gotchas (symlink)
    HEARTBEAT.md         #   Self-improvement checklist (symlink)
    IDENTITY.md          #   Neo's identity card (symlink)
    memory/              #   Daily memory files (symlink to Obsidian @neo/memory/)
    projects/            #   GSD project files (symlink to Obsidian @neo/projects/)
    skills/              #   Installed skills (symlink to Obsidian @neo/shared/skills/)
      proactive-agent/   #     Proactive behavior patterns
      self-improving-agent/ #  Self-improvement & learning loops
    .learnings/          #   Error/learning logs (self-improving-agent)
  extensions/            # Plugins with code
    voice-call/          #   Twilio voice call plugin (TypeScript)
  bin/                   # Utility scripts
  cron/                  # Scheduled jobs
    jobs.json            #   Job definitions
    runs/                #   Execution history
  logs/                  # Runtime logs
  agents/                # Agent session data
  credentials/           # Auth credentials (encrypted)
  state/                 # Runtime state files
  devices/               # Device registry
  identity/              # Instance identity
  memory/                # Instance-level memory
  subagents/             # Sub-agent session data
```

## Configuration Management

**Rule: Never edit `openclaw.json` directly. Always use MCP tools.**

| Operation | Tool | Example |
|-----------|------|---------|
| Read config | `openclaw_config_get()` | View current settings |
| Patch config | `openclaw_config_patch(patch_json)` | Merge-patch + auto-restart |
| Restart gateway | `openclaw_gateway_restart()` | Restart without config change |
| Read a secret | `onepassword_read(item, field)` | Read from 1Password Agent vault |

### Config Structure (top-level keys)

- `meta` — Version tracking
- `wizard` — Setup wizard state
- `auth` — Provider profiles (Anthropic)
- `agents` — Agent defaults (workspace path, concurrency, timeouts, compaction)
- `tools` — Tool config (web search API key)
- `messages` — Message handling (ack reaction scope)
- `commands` — Command config (native skills, restart)
- `channels` — Channel configs: `telegram`, `discord`, `imessage`
- `gateway` — Gateway settings (port, bind, auth token, tailscale)
- `skills` — Skill installation config and per-skill settings
- `plugins` — Plugin enable/disable and per-plugin config

### Recipe: Add a Discord Channel

```
openclaw_config_patch('{"channels":{"discord":{"guilds":{"1470205278770430218":{"channels":{"CHANNEL_ID":{"allow":true,"requireMention":false}}}}}}}')
```

### Recipe: Add a Telegram Group

```
openclaw_config_patch('{"channels":{"telegram":{"groups":{"GROUP_ID":{"requireMention":false,"groupPolicy":"open"}}}}}')
```

## Writing Skills

Skills live in `workspace/skills/<name>/`. The gateway auto-loads SKILL.md files as prompt context.

### Skill Directory Structure

```
workspace/skills/<skill-name>/
  SKILL.md             # Required — skill definition (loaded by gateway)
  _meta.json           # ClawdHub metadata
  assets/              # Template files, default configs
  scripts/             # Helper scripts (activator, extractors)
  hooks/               # Event hooks (optional)
  references/          # Documentation, integration guides
```

### SKILL.md Format

```markdown
---
name: my-skill
version: 1.0.0
description: "One-line description for skill discovery and auto-activation"
author: your-name
---

# Skill Title

Skill body — instructions, rules, tables, examples.
The gateway injects this into sessions when the skill activates.
```

The `description` field in frontmatter is critical — it tells the gateway **when** to activate the skill. Write it as a trigger list: "Use when: (1) X happens, (2) Y is requested..."

### Hook Structure

Skills can include hooks that fire on gateway events:

```
hooks/openclaw/
  HOOK.md              # Hook definition (event type, matcher)
  handler.ts           # TypeScript handler
```

### Authoring Checklist

- [ ] SKILL.md has YAML frontmatter with `name`, `description`
- [ ] `name` matches the directory name
- [ ] Description includes activation triggers
- [ ] No hardcoded secrets (use `onepassword_read()`)
- [ ] No README.md inside the skill folder (SKILL.md is the README)
- [ ] Test by reading SKILL.md in a fresh session — is it self-contained?

### Installation Note

`clawhub install <skill>` places skills in `~/skills/`, **not** in `workspace/skills/`. After install, you may need to relocate or symlink into the workspace.

## Plugin Management

| Plugin | Status | Purpose |
|--------|--------|---------|
| `discord` | enabled | Discord bot integration |
| `telegram` | enabled | Telegram bot integration |
| `voice-call` | enabled | Twilio voice calls (inbound/outbound) |
| `imessage` | disabled | iMessage integration |

Enable/disable via config patch:
```
openclaw_config_patch('{"plugins":{"entries":{"imessage":{"enabled":true}}}}')
```

Plugin code lives in `extensions/<plugin-name>/`. Config is inline in `openclaw.json` under `plugins.entries.<name>.config`.

## Utility Scripts

| Script | Purpose |
|--------|---------|
| `bin/health-check.sh` | System health check (gateway, channels, plugins) |
| `bin/setup-ngrok.sh` | Configure ngrok tunnel for voice webhooks |
| `bin/project-orchestrator.sh` | GSD project heartbeat — checks for stalled work |
| `bin/neo-proxy.py` | HTTP proxy for Neo API |
| `bin/sms-bridge.py` | SMS <-> OpenClaw bridge via Twilio |
| `bin/sms-send.sh` | Send an SMS via Twilio |
| `bin/obsidian-classify.sh` | Tag untyped Obsidian files |
| `bin/obsidian-add-aliases.py` | Add first-name aliases to people files |
| `bin/obsidian-resolve-aliases.py` | Resolve ambiguous aliases |
| `bin/obsidian-autolink.py` | Convert plain text to `[[wikilinks]]` |
| `bin/obsidian-migrate-properties.py` | Migrate Obsidian file properties |

## Cron Jobs

Defined in `cron/jobs.json`. Both run as isolated agent turns (autonomous, no main session needed).

| Job | Schedule | Purpose |
|-----|----------|---------|
| `obsidian-weekly-maintenance` | Sundays 3:00 AM CT | Classify, alias, autolink, and backfill Obsidian vault |
| `project-orchestrator` | Every 2 minutes | Check for stalled GSD projects, report status |

To modify: edit `cron/jobs.json` (or use the gateway API). Jobs use `sessionTarget: "isolated"` + `kind: "agentTurn"` for autonomous execution.

## MCP Tools Reference

Full tool signatures are in the global `~/.claude/CLAUDE.md`. Here's when to use each:

### neo-tools

| Tool | When to Use |
|------|-------------|
| `openclaw_config_get()` | Before any config change — read current state first |
| `openclaw_config_patch(patch_json)` | Add channels, toggle plugins, change settings |
| `openclaw_gateway_restart()` | After manual fixes or when gateway seems stuck |
| `onepassword_read(item, field)` | Need an API key, token, or credential |
| `twilio_update_webhook(webhook_url)` | After ngrok URL changes or voice setup |

### openclaw-comms

| Tool | When to Use |
|------|-------------|
| `comms_send()` | Post status updates, send messages to users/channels |
| `comms_read()` | Check recent messages in a channel |
| `comms_react()` | Acknowledge a message with an emoji |
| `comms_search()` | Find past messages by keyword |
| `comms_resolve()` | Look up a channel/user ID by name |
| `comms_thread()` | Create a discussion thread |
| `comms_channels()` | List available platforms and their capabilities |

## Common Recipes

**Restart the gateway:**
```
openclaw_gateway_restart()
```

**Check system health:**
```bash
bash ~/.openclaw/bin/health-check.sh
```

**View gateway logs:**
```bash
tail -100 ~/.openclaw/logs/gateway.log
tail -50 ~/.openclaw/logs/gateway.err.log
```

**Read a secret from 1Password:**
```
onepassword_read("Twilio", "auth_token")
```

**Send a Discord message:**
```
comms_send(channel="discord", target="channel:1470205280187846800", message="Hello from Claude Code")
```

**Install a skill from ClawdHub:**
```bash
clawhub install <skill-name>
# Then relocate from ~/skills/ to workspace/skills/ if needed
```

**Create a skill from scratch:**
```bash
mkdir -p ~/.openclaw/workspace/skills/my-skill
# Write SKILL.md with YAML frontmatter + body
```

## Rules

1. **No secrets in files** — Use `onepassword_read()` for API keys and tokens. Never hardcode credentials.
2. **Config via MCP only** — Always use `openclaw_config_patch()`, never edit `openclaw.json` directly.
3. **Self-extend neo-tools** — If you need a capability that doesn't exist, add it to `~/Developer/mcp/neo-tools/server.py`.
4. **Workspace files are for Neo** — `workspace/*.md` files are the gateway agent's prompt context. Don't modify them to affect Claude Code behavior.
5. **Discord guild ID** — `1470205278770430218`
6. **ngrok static domain** — `gracia-unrimed-uncontemporaneously.ngrok-free.dev`
7. **Gateway** — port `18789`, loopback only, token auth

## Key Paths

| What | Path |
|------|------|
| Config | `~/.openclaw/openclaw.json` |
| Workspace | `~/.openclaw/workspace/` |
| Skills | `~/.openclaw/workspace/skills/` |
| Extensions | `~/.openclaw/extensions/` |
| Bin scripts | `~/.openclaw/bin/` |
| Logs | `~/.openclaw/logs/` |
| Cron jobs | `~/.openclaw/cron/jobs.json` |
| MCP servers | `~/Developer/mcp/neo-tools/server.py` |
| OpenClaw CLI | `/opt/homebrew/bin/openclaw` |
| Obsidian vault | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Expedia/` |
| Neo agent files | `<vault>/@neo/` |
