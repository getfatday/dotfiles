# Timesheets for the week this card was created

Worker: the `timesheets` profile, using the `timesheet-runner` skill.

## What done means

Clarity: a week counts as submitted only when 5 workdays are filled, the read-back matches
the entries, and the total is at least 40h. Fieldglass: the vendor skill's own standing rule.

## Receipt contract (kanban_complete metadata)

Every key is required. Use null when a step did not run.

- `fire_week`: ISO week when the cron job fired (`date +%G-W%V`). This is NOT the work week.
- `clarity_periods`: list of {timesheet_id, period_start, period_finish, status_before,
  status_after, hours_per_day, actuals_total, submitted} for every Clarity timesheet acted on.
- `fieldglass`: {approved: [sheet ids], confirm_first: [sheet ids], skipped: [sheet ids]}.
- `auth_status`: {clarity, outlook, fieldglass}, each one of ok, login_needed, error.
- `bridge_sessions`: list of {step, session_id, ok, subtype, cost_usd}.
- `permission_denials`: list from every bridge call. Not gate evidence: an allow-listed
  write produces no denial. The read-back is the gate evidence.
- `readback`: the raw status JSON from a read-only re-read after the last write.

No billed amounts, rates or invoice totals anywhere: not in comments, metadata or files.
