---
name: claude-code-bridge
description: Manage Claude Code sessions on this Mac through the claude-bridge CLI. Use to ask Claude Code a question, continue a session, list or inspect its sessions, or start a background session. Complements the bundled claude-code skill, which documents the full claude CLI.
version: 2.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [claude-code, orchestration, sessions]
    related_skills: [claude-code]
---

# Claude Code bridge

Use `claude-bridge` (on PATH via ~/.local/bin). It sources the long-lived auth token in the same shell, so you never handle credentials. A "Not logged in" error from a raw `claude -p` is an auth flap, not a reason to log in again.
It adds no policy: Claude Code runs with the user's own settings and permissions.

## Verbs
```
claude-bridge doctor                                   # version, token file readable, session count, no model call
claude-bridge list                                     # all Claude Code sessions as JSON (id,name,state,cwd,sessionId)
claude-bridge ask -- "PROMPT"                          # headless, returns {ok,result,session_id,cost_usd}
claude-bridge ask --resume SESSION_ID -- "NEXT"        # continue that session
claude-bridge ask --cwd ~/src/repo -- "PROMPT"         # run in a repo
claude-bridge ask --extra "--max-turns 5 --permission-mode plan" -- "..."   # any claude flag, per call
claude-bridge spawn [--cwd DIR] NAME "PROMPT"          # background session; check later with list and logs
claude-bridge logs ID_OR_NAME [LINES]                  # recent output of a background session
```

## Notes
- Session state lives in Claude Code, not in your context. After context compression, run `claude-bridge list` to re-find sessions. Store only session ids and names, for example in kanban tasks.
- `claude-bridge list` (backed by `claude agents --json`) is the supported way to enumerate sessions; the files under ~/.claude/jobs are internal.
- For every claude flag, see the bundled `claude-code` skill.
