#!/usr/bin/env bash
# create-week-card.sh: the whole job of the `timesheet-weekly` no-agent cron job in the
# Hermes profile `timesheets`. It creates this ISO week's card on the `timesheets` board and
# prints the kanban JSON (task id) on stdout. Idempotent: the key timesheets-<YYYY-Www> makes
# a re-fire return the existing non-archived card instead of a duplicate.
#
# The bootstrap copies this script and receipt-contract.md into $PROFILE/scripts
# (Hermes refuses scripts that resolve outside that dir, so they are copies, not links).
# Mode comes from the sidecar written by hermes-timesheets-bootstrap:
#   canary (default): no assignee, created blocked, so no dispatcher can ever pick it up.
#   live:             assigned to the `timesheets` profile, created ready for the dispatcher.
# Cron scripts run with a sanitized env, so every binary is called by absolute path.
set -euo pipefail
HERMES_BIN="${HERMES_BIN:-/Users/ianderson/.local/bin/hermes}"
PROFILE="/Users/ianderson/.hermes/profiles/timesheets"
SIDECAR="$PROFILE/timesheets.env"
TIMESHEETS_MODE=canary
[ -r "$SIDECAR" ] && . "$SIDECAR"

week="$(date +%G-W%V)"
args=(kanban --board timesheets create "Timesheets $week"
      --idempotency-key "timesheets-$week"
      --max-runtime 2h --max-retries 3
      --created-by timesheet-weekly
      --body-file "$PROFILE/scripts/receipt-contract.md" --json)
case "$TIMESHEETS_MODE" in
  live)   args+=(--assignee timesheets --skill timesheet-runner) ;;
  canary) args+=(--initial-status blocked) ;;
  *) echo "unknown TIMESHEETS_MODE=$TIMESHEETS_MODE" >&2; exit 2 ;;
esac
exec "$HERMES_BIN" "${args[@]}"
