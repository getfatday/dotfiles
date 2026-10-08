---
name: hermes
description: Delegate a task to the locally installed Hermes Agent (Nous) and read back its answer, continue a Hermes session, or check Hermes health and sessions. Use when the user says "ask Hermes", "have Hermes do", "run this through Hermes", or wants Hermes sessions or skills inspected. Local desktop only.
---

# Hermes from Claude Code

Use `hermes-bridge`. It wraps Hermes' own one-shot mode (`hermes -z`) and returns JSON.
It adds no policy: Hermes runs with its own config, toolsets and approval behavior.
(`hermes -z` is Hermes' non-interactive mode, and Hermes runs it with approvals off.)

## Verbs
```
hermes-bridge status                                   # version + approvals mode, no model call
hermes-bridge doctor                                   # health, no model call
hermes-bridge ask -- "PROMPT"                          # one-shot, returns {ok,result,session_id,cost_usd}
hermes-bridge ask --resume SESSION_ID -- "FOLLOW-UP"   # continue the same Hermes session
hermes-bridge ask --toolsets terminal,file -- "..."    # pick toolsets (default: Hermes' configured set)
hermes-bridge ask --extra "--max-turns 5" -- "..."     # pass any other hermes flag through
hermes-bridge sessions                                 # list Hermes sessions
```
Keep the `session_id` from `ask` and pass it to `--resume` for multi-turn work. Hermes holds that context, so it survives your own compaction.

## Notes
- Per-machine settings live in `~/.config/hermes-bridge/env` (not in git): `HERMES_BIN`, `HERMES_HOME`, `HERMES_BRIDGE_MODEL`, `HERMES_BRIDGE_PROVIDER`. Use it when Hermes is installed somewhere other than `~/.hermes` or signs in with a different provider. Without it the bridge uses `hermes` on PATH and pins claude-haiku-4-5-20251001 on anthropic, because this MacBook's configured default model returns 404.
- `hermes mcp serve` is Hermes' messaging connector (conversations, messages, events). It cannot prompt the agent, so use `hermes-bridge ask` for delegation.
- `ok:false` means the call failed; report the `error`.
