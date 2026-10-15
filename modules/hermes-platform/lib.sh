# shellcheck shell=bash
# hermes-platform shared helpers, sourced by setup.sh and check.sh. Not executable on its own.
#
# Everything machine-specific is an env var with a default; nothing here names a host or account.
#   HERMES_PLATFORM_HOME              Hermes root state dir (default ~/.hermes). Deliberately NOT HERMES_HOME:
#                                     inside an agent session that variable names a profile dir, and the
#                                     install lives under the root, not under a profile.
#   HERMES_PLATFORM_DIR               the install (default $HERMES_PLATFORM_HOME/hermes-agent)
#   HERMES_REPO_URL                   upstream (default NousResearch/hermes-agent on GitHub; the
#                                     official installer reads the same variable)
#   HERMES_PLATFORM_LEDGER            local-patches ledger (default ~/src/hyp-hermes/ledger/local-patches.jsonl)
#   HERMES_PLATFORM_PATCH_ROOT        base for the ledger's repo-relative patch_file (default: the
#                                     ledger's repo root, i.e. two levels above the ledger file)
#   HERMES_PLATFORM_LAUNCH_AGENT_DIR  where the gateway plist is stowed (default ~/Library/LaunchAgents)

HP_MODULE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
HP_BRANCH="local/hermes-patches"
HP_PLIST_NAME="ai.hermes.gateway.plist"
HP_UPSTREAM_DEFAULT="https://github.com/NousResearch/hermes-agent.git"

hp_init_env() {
    HERMES_HOME="${HERMES_PLATFORM_HOME:-$HOME/.hermes}"
    HP_DIR="${HERMES_PLATFORM_DIR:-$HERMES_HOME/hermes-agent}"
    HP_REPO_URL="${HERMES_REPO_URL:-$HP_UPSTREAM_DEFAULT}"
    HP_LEDGER="${HERMES_PLATFORM_LEDGER:-$HOME/src/hyp-hermes/ledger/local-patches.jsonl}"
    # No lab repo on this machine (a clean Mac, CI): fall back to the copy vendored in this module (vendor-sync.sh keeps
    # it faithful). Only when the variable is unset; an explicit HERMES_PLATFORM_LEDGER that is missing stays an error.
    if [ -z "${HERMES_PLATFORM_LEDGER:-}" ] && [ ! -f "$HP_LEDGER" ] && [ -f "$HP_MODULE_DIR/vendor/ledger/local-patches.jsonl" ]; then
        HP_LEDGER="$HP_MODULE_DIR/vendor/ledger/local-patches.jsonl"
    fi
    HP_PATCH_ROOT="${HERMES_PLATFORM_PATCH_ROOT:-$(dirname "$(dirname "$HP_LEDGER")")}"
    HP_LA_DIR="${HERMES_PLATFORM_LAUNCH_AGENT_DIR:-$HOME/Library/LaunchAgents}"
}

hp_die() { printf 'hermes-platform: %s\n' "$*" >&2; exit "${HP_RC:-1}"; }

# The pin: first non-comment, non-blank token of pin.txt; hex, 7..40 chars. HERMES_PLATFORM_PIN overrides
# it (test hook: tests/run.sh pins its fixture upstream; never set it on a real machine).
hp_read_pin() {
    if [ -n "${HERMES_PLATFORM_PIN:-}" ]; then HP_PIN="$HERMES_PLATFORM_PIN"; return 0; fi
    local f="$HP_MODULE_DIR/pin.txt" line
    [ -f "$f" ] || { echo "pin.txt missing" >&2; return 1; }
    while IFS= read -r line || [ -n "$line" ]; do
        line="${line%%#*}"
        line="${line//[[:space:]]/}"
        [ -n "$line" ] || continue
        if [[ "$line" =~ ^[0-9a-f]{7,40}$ ]]; then HP_PIN="$line"; return 0; fi
        echo "pin.txt: '$line' is not a hex sha" >&2; return 1
    done < "$f"
    echo "pin.txt has no sha" >&2; return 1
}

# Fills parallel arrays from the ledger. Every row not retired is a patch the install must carry,
# in ledger order. Retired rows are history.
#   HP_P_ID[i]  HP_P_FILE[i] (absolute)  HP_P_DESC[i]
hp_load_patches() {
    HP_P_ID=() HP_P_FILE=() HP_P_DESC=()
    command -v jq >/dev/null 2>&1 || { echo "jq not found (module productivity provides it)" >&2; return 1; }
    [ -f "$HP_LEDGER" ] || { echo "patch ledger not found: $HP_LEDGER (set HERMES_PLATFORM_LEDGER)" >&2; return 1; }
    local rows id file desc
    rows=$(jq -r 'select(.status != "retired") | [.id, .patch_file, .narrow_description] | @tsv' "$HP_LEDGER") \
        || { echo "patch ledger is not valid JSON lines: $HP_LEDGER" >&2; return 1; }
    while IFS=$'\t' read -r id file desc; do
        [ -n "$id" ] || continue
        [ -n "$file" ] && [ "$file" != null ] || { echo "ledger row $id has no patch_file" >&2; return 1; }
        case "$file" in /*) ;; *) file="$HP_PATCH_ROOT/$file" ;; esac
        HP_P_ID+=("$id") HP_P_FILE+=("$file") HP_P_DESC+=("$desc")
    done <<< "$rows"
    return 0
}

hp_git() { "$HP_GIT_BIN" -C "$HP_DIR" "$@"; }

# /usr/bin/git can be the xcode-select shim, which costs seconds per call on a loaded Mac; call the
# real binary directly when we can find it.
HP_GIT_BIN=$(command -v git || true)
if [ "$HP_GIT_BIN" = /usr/bin/git ] && _hp_dev=$(xcode-select -p 2>/dev/null) && [ -x "$_hp_dev/usr/bin/git" ]; then
    HP_GIT_BIN="$_hp_dev/usr/bin/git"
fi

# "installed" = the patch's reverse applies cleanly to the work tree (every hunk is present).
hp_patch_applied() { hp_git apply -p1 -R --check "$1" >/dev/null 2>&1; }

# Sorted unique file names a patch touches.
hp_patch_files() { hp_git apply -p1 --numstat "$1" 2>/dev/null | awk -F'\t' '{print $3}' | sort -u; }

# Credentialless doctor verdict (check.sh --credentialless). Reads the output of `hermes doctor`, lists the numbered
# issues under "Found N issue(s) to address:", and succeeds only when there is at least one and EVERY one needs
# credentials or the interactive first-run setup (an API key, a token, a login/auth step, `hermes setup`, the .env
# file), or an npm advisory in upstream's lockfiles (class skipped-upstream, below). Sets HP_DOCTOR_N and
# HP_DOCTOR_SUMMARY. Anything else (a broken install, a missing tool) keeps the check red.
HP_CRED_RE='api[ _-]?key|api[ _-]?token|token|credential|secret|oauth|log[ -]?in|sign[ -]?in|authenticat|hermes (setup|auth|login|model)|\.env|_API_|_KEY\b'
HP_UPSTREAM_RE='npm .*vulnerabilit|vulnerabilit(y|ies)'
hp_doctor_credential_only() {
    local issues other
    issues=$(printf '%s\n' "$1" | sed -E $'s/\033\\[[0-9;]*[A-Za-z]//g' \
        | awk '/Found [0-9]+ issue/ {f=1; next} f && /^ *[0-9]+\. / {sub(/^ *[0-9]+\. /, ""); print}')
    HP_DOCTOR_N=$(printf '%s' "$issues" | grep -c . || true)
    HP_DOCTOR_SUMMARY=$(printf '%s\n' "$issues" | head -3 | cut -c1-70 | paste -sd';' -)
    [ "${HP_DOCTOR_N:-0}" -gt 0 ] || return 1
    # A second class, only ever reached through --credentialless: npm advisories in upstream's own lockfiles. The pin is
    # fixed and doctor itself says the fix is an upstream lockfile bump that `hermes update` would undo, so nothing in
    # this repo can clear them; they stay visible (counted, named skipped-upstream) and clear with a pin bump.
    HP_DOCTOR_CRED_N=$(printf '%s\n' "$issues" | grep -ciE "$HP_CRED_RE" || true)
    HP_DOCTOR_UP_N=$(printf '%s\n' "$issues" | grep -viE "$HP_CRED_RE" | grep -ciE "$HP_UPSTREAM_RE" || true)
    other=$(printf '%s\n' "$issues" | grep -viE "$HP_CRED_RE" | grep -viE "$HP_UPSTREAM_RE" || true)
    [ -z "$other" ]
}

hp_rebase_hint() {
    cat >&2 <<EOF
Rebase rule: on a pin bump (hermes update), run
  git -C "$HP_DIR" rebase <new pin> $HP_BRANCH
then update modules/hermes-platform/pin.txt and rerun setup.sh. A conflict is a loud failure:
resolve it, or retire the patch in the ledger if upstream now carries it.
EOF
}
