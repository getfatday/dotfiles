# dotm-sync-watchdog

A supervisor for the `com.getfatday.dotm-sync` LaunchAgent. It runs `dotm sync` unchanged, writes a
small heartbeat record on every exit, and on a non-zero exit writes a failure manifest and, when this
machine is configured for it, launches one budgeted, tightly sandboxed headless Claude session whose
only job is to file or update a single GitHub issue tracking the failure signature. It never mutates
the machine and never breaks the sync it wraps: it exits 0 once the manifest is written, so the sync's
own exit code lives in the manifest, not in the launchd job state.

## Files (all resolved relative to `watchdog.py`)
- `watchdog.py` - the supervisor. Runs the wrapped command, writes the heartbeat and the manifest, optionally launches the reporter.
- `hook-guard.py` - a PreToolUse guard for the reporter child: denies everything except `Read` and `gh issue list/create/comment`.
- `hook-settings.json` - the child's settings template (the guard is wired in here).
- `prompt.md` - the reporter's instructions: read the manifest, file or comment one issue, stop.

## Default-on

The plist runs the watchdog whenever `watchdog.py` is executable. Plain `dotm sync --quiet` runs only
when the wrapper file is missing (a half-stowed module never loses its sync). `~/.config/dotm/watchdog.env`
is sourced when it exists; it no longer gates the wrapper.

Without `watchdog.env` the wrapper still runs, and nothing leaves the machine:
- the heartbeat is written locally under `~/.local/state/dotm/last-sync.json` (`heartbeat-channel-unset`);
- on a failure the manifest is written and the reporter is not launched, because the deny scan fails closed
  with no deny sources configured (`leak-scan-skip`).

## Heartbeat

On every exit, green or not, the wrapper writes `~/.local/state/dotm/last-sync.json`:

    {"ts", "host", "sha", "rc", "duration", "failed_task", "role_sha"}

`sha` is the dotfiles checkout HEAD; `failed_task` is null on a green run; `role_sha` is the sha of the
Ansible role tree actually installed on this machine (galaxy install metadata or a git checkout under
the roles path), null when it cannot be resolved. When `DOTM_WATCHDOG_HEALTH_REPO` is set, the same bytes
are pushed as one commit per run to the `health/<host>` branch of that repository through the gh API
(the branch holds only `last-sync.json`). The health repo has no default: unset means the record stays
local, so a machine without machine-local configuration cannot push a record anywhere. A fleet reader
can then answer "did every machine sync in the last interval" from records alone, without a shell on any
machine.

## Reporter

On a non-zero exit, after the heartbeat, the wrapper renders a deterministic issue title and body from
the manifest, scans the issue body and the manifest text against the configured deny sources (fail
closed: a hit, a missing or unreadable source, or zero rules all skip the launch; the tracker name is an
operator argument and is not scanned), and launches `claude -p --restricted --tools Read,Bash
--permission-mode dontAsk` with the allowed-tools set above, in an empty cwd, so the machine's own
Claude settings, hooks and plugins never reach it.

The child receives exactly two environment tokens. `GH_TOKEN` comes from `gh auth token --user
$DOTM_WATCHDOG_GH_USER`. `CLAUDE_CODE_OAUTH_TOKEN` comes from the owner's Claude Code login item in the
login Keychain (service `Claude Code-credentials`), read by the wrapper under the real HOME; no token
file is needed. When that item is absent the wrapper falls back to sourcing `DOTM_WATCHDOG_TOKEN_FILE`
in the launch shell, and when neither exists it logs `claude-login-missing` and launches nothing: the
manifest and the heartbeat are still written.

## Configuring a machine (machine-local, never committed)

    # ~/.config/dotm/watchdog.env  (machine-local; do not commit)
    DOTM_WATCHDOG_HEALTH_REPO=<owner>/<private-health-repo>
    DOTM_WATCHDOG_REPO=<owner>/<private-tracker-repo>
    DOTM_WATCHDOG_LABEL=dotm-sync-failure
    DOTM_WATCHDOG_GH_USER=<gh account with push access to both repos>
    DOTM_WATCHDOG_DENY_FILES=<machine-local denylist path>
    DOTM_WATCHDOG_MAX_USD=0.50
    #DOTM_WATCHDOG_LOGIN_SERVICE=Claude Code-credentials   (default)
    #DOTM_WATCHDOG_TOKEN_FILE=<file exporting CLAUDE_CODE_OAUTH_TOKEN>   (fallback only)

`watchdog.py` documents every `DOTM_WATCHDOG_*` variable in its header. Point both repositories at
private repositories you are willing to have the host name, the failed task and a log tail recorded in.
Neither name belongs in this repository or its plist.

launchd does not re-read a changed plist until the job is reloaded. After the module stows a new plist,
or after creating or changing `watchdog.env`, reload the agent:

    launchctl bootout gui/$(id -u)/com.getfatday.dotm-sync
    launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.getfatday.dotm-sync.plist
    launchctl kickstart -k gui/$(id -u)/com.getfatday.dotm-sync
