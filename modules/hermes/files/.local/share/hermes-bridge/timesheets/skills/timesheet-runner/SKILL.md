---
name: timesheet-runner
description: Work one weekly `Timesheets <YYYY-Www>` kanban card on the `timesheets` board by driving the vault's /timesheet and /vendor-timesheets skills through claude-bridge, then post the receipt and complete the card with the metadata contract from the card body.
---

# timesheet-runner

You are the `timesheets` profile. You do not fill timesheets yourself. The vault skills own
all Clarity, Outlook and Fieldglass logic. You call them through `claude-bridge`, read the
JSON it returns, and keep the card as the receipt.

## Before any bridge call

1. Make a fresh vault worktree pinned to origin/main. Never use the root vault checkout.
   ```
   git -C /Users/ianderson/src/vault fetch origin main
   WT=/Users/ianderson/src/vault/.claude/worktrees/timesheets-<card id>
   git -C /Users/ianderson/src/vault worktree add --detach "$WT" origin/main
   ```
2. Run every bridge call in the FOREGROUND (the profile raises terminal.timeout). Never in
   background mode: if this worker dies, its child chain must die with it.
3. Add `--arg --max-budget-usd --arg 5` to every bridge call.

## Call sequence

Each call returns one JSON object on the last line of stdout:
`{ok, result, session_id, model, cost_usd, turns, subtype, permission_denials}`.
Parse the LAST line only. Record session_id, ok, subtype and cost_usd for every call.

1. Dry-run, both skills:
   ```
   claude-bridge ask --cwd "$WT" --arg --max-budget-usd --arg 5 -- '/timesheet dry-run'
   claude-bridge ask --cwd "$WT" --arg --max-budget-usd --arg 5 -- '/vendor-timesheets dry-run'
   ```
   Post each `result` as a card comment (`kanban_comment`), not an attachment.
2. Apply, both skills (`/timesheet apply` lands with the vault skills-agent-mode PR):
   ```
   claude-bridge ask --cwd "$WT" --arg --max-budget-usd --arg 5 -- '/timesheet apply'
   claude-bridge ask --cwd "$WT" --arg --max-budget-usd --arg 5 -- '/vendor-timesheets apply'
   ```
   Post each result as a comment.
3. Read back with a read-only call (`/timesheet status`, `/vendor-timesheets status`) and
   post the raw JSON as a comment.

## Stop rules

- Any `ok: false`, or any result that says a login is needed: `kanban_block` with reason
  `login needed: <system>` and stop. Do not retry the login.
- Clarity submit counts only when 5 workdays are filled, the read-back matches, and the
  total is at least 40h. Otherwise block with the read-back as the reason.
- Never put billed amounts, rates or invoice totals in a comment or in metadata.

## Complete

`kanban_complete` with a one-line summary and the metadata keys listed in the card body
(fire_week, clarity_periods, fieldglass, auth_status, bridge_sessions, permission_denials,
readback). Then remove the worktree: `git -C /Users/ianderson/src/vault worktree remove "$WT"`.
