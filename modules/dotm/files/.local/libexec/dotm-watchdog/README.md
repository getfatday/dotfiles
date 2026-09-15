# dotm-sync-watchdog

A supervisor for the `com.getfatday.dotm-sync` LaunchAgent. It runs `dotm sync` unchanged, and
on a non-zero exit writes a failure manifest and, when enabled on this machine, launches one
budgeted, tightly sandboxed headless Claude session whose only job is to file or update a single
GitHub issue tracking the failure signature. It never mutates the machine and never breaks the
sync it wraps: it exits 0 once the manifest is written, so the sync's own exit code lives in the
manifest, not in the launchd job state.

## Files (all resolved relative to `watchdog.py`)
- `watchdog.py` - the supervisor. Runs the wrapped command, writes the manifest, optionally launches the reporter.
- `hook-guard.py` - a PreToolUse guard for the reporter child: denies everything except `Read` and `gh issue list/create/comment`.
- `hook-settings.json` - the child's settings template (the guard is wired in here).
- `prompt.md` - the reporter's instructions: read the manifest, file or comment one issue, stop.

The child runs `claude -p --restricted --tools Read,Bash --permission-mode dontAsk` with the
allowed-tools set above, in an empty cwd, so the machine's own Claude settings, hooks and plugins
never reach it. It fails closed: with no deny source configured it records the manifest and does
not launch.

## Enabling on a machine (opt-in, per machine, not committed)

The plist runs the watchdog only when `~/.config/dotm/watchdog.env` exists. That file is
machine-local and never committed. Without it, the LaunchAgent runs plain `dotm sync` exactly as
before. To enable, create it with the environment the supervisor reads (`watchdog.py` documents
every `DOTM_WATCHDOG_*` variable in its header):

    # ~/.config/dotm/watchdog.env  (machine-local; do not commit)
    DOTM_WATCHDOG_REPO=<owner>/<private-tracker-repo>
    DOTM_WATCHDOG_LABEL=dotm-sync-failure
    DOTM_WATCHDOG_GH_USER=<gh account with access to that repo>
    DOTM_WATCHDOG_DENY_FILES=<machine-local denylist path>
    DOTM_WATCHDOG_TOKEN_FILE=<file exporting CLAUDE_CODE_OAUTH_TOKEN>

Point `DOTM_WATCHDOG_REPO` at a repository you are willing to have the failure host, the failed
task and a log tail recorded in; a private tracker is the safe default. After creating or
changing the file, reload the agent so the new plist and env take effect:

    launchctl kickstart -k gui/$(id -u)/com.getfatday.dotm-sync
