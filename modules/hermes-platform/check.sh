#!/usr/bin/env bash
# hermes-platform check: read-only. Reports ok / FAIL per item, exits 1 when any item fails.
#
#   check.sh              full check of this machine's install
#   check.sh --dry-run    structure only: module files, pin, ledger, patch files, plist well-formed.
#                         Does not look at the install; safe on any machine that has the repo.
#   check.sh --no-doctor  full check but skip `hermes doctor` (scratch installs that are not bootstrapped)
#   check.sh --json       one JSON line instead of the report (same exit code)
#
# Full check, per the module contract:
#   install dir exists and is a git checkout; HEAD is on local/hermes-patches; the pin is an ancestor
#   of HEAD; `git log <pin>..HEAD` and `git log origin/main..HEAD` each hold exactly the ledger's
#   patches (count, every patch present in the tree, same files changed); tracked files are clean;
#   the gateway plist matches the module's file; `hermes doctor` exits 0.
# Env: see lib.sh.
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
# shellcheck source=lib.sh
. "$HERE/lib.sh"

DRY=0 DOCTOR=1 JSON=0
for a in "$@"; do
    case "$a" in
        --dry-run) DRY=1 ;;
        --no-doctor) DOCTOR=0 ;;
        --json) JSON=1 ;;
        -h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $a" >&2; exit 2 ;;
    esac
done
hp_init_env

fails=0
lines=()
rec() { # status name detail
    lines+=("$1|$2|$3")
    [ "$JSON" = 1 ] || printf '%-5s %s: %s\n' "$1" "$2" "$3"
    [ "$1" = FAIL ] && fails=$((fails + 1))
    return 0
}
ok() { rec ok "$1" "$2"; }
no() { rec FAIL "$1" "$2"; }

# --- module structure (both modes) -----------------------------------------------------------
M="$HP_MODULE_DIR"
for f in config.yml pin.txt README.md lib.sh files/Library/LaunchAgents/$HP_PLIST_NAME; do
    [ -f "$M/$f" ] && ok "module:$f" present || no "module:$f" missing
done
for f in setup.sh check.sh; do
    [ -x "$M/$f" ] && ok "module:$f" executable || no "module:$f" "missing or not executable"
done
grep -q "^requires: \[macos, hermes-host\]" "$M/config.yml" 2>/dev/null \
    && ok module:requires "macos + hermes-host" || no module:requires "config.yml must say requires: [macos, hermes-host]"
grep -q "$HP_BRANCH" "$M/setup.sh" 2>/dev/null && ok module:branch "setup.sh creates $HP_BRANCH" || no module:branch "setup.sh does not name $HP_BRANCH"

if hp_read_pin 2>/dev/null; then ok pin "$HP_PIN"; else no pin "pin.txt unreadable or not a hex sha"; fi
if hp_load_patches 2>/dev/null; then
    ok ledger "${#HP_P_ID[@]} patch(es): ${HP_P_ID[*]:-none}"
    for i in "${!HP_P_ID[@]}"; do
        [ -s "${HP_P_FILE[$i]}" ] && ok "patch-file:${HP_P_ID[$i]}" "${HP_P_FILE[$i]}" || no "patch-file:${HP_P_ID[$i]}" "missing or empty: ${HP_P_FILE[$i]}"
    done
else
    no ledger "$(hp_load_patches 2>&1 | head -1)"
fi
plist="$M/files/Library/LaunchAgents/$HP_PLIST_NAME"
if [ -f "$plist" ]; then
    if command -v plutil >/dev/null 2>&1; then
        plutil -lint "$plist" >/dev/null 2>&1 && ok plist:wellformed "plutil -lint" || no plist:wellformed "plutil -lint failed"
    fi
    grep -q '<string>ai.hermes.gateway</string>' "$plist" && ok plist:label ai.hermes.gateway || no plist:label "label is not ai.hermes.gateway"
fi

# --- the install (full mode only) ------------------------------------------------------------
if [ "$DRY" = 0 ]; then
    if [ ! -d "$HP_DIR/.git" ]; then
        no install:dir "no git checkout at $HP_DIR (run modules/hermes-platform/setup.sh)"
    else
        ok install:dir "$HP_DIR"
        cur=$(hp_git symbolic-ref --short -q HEAD || true)
        [ "$cur" = "$HP_BRANCH" ] && ok install:branch "$cur" || no install:branch "HEAD is '${cur:-detached}', want $HP_BRANCH"

        if [ -n "${HP_PIN:-}" ] && hp_git merge-base --is-ancestor "$HP_PIN" HEAD 2>/dev/null; then
            ok install:pin "pin ${HP_PIN:0:10} is an ancestor of HEAD $(hp_git rev-parse --short=10 HEAD)"
            want_n=${#HP_P_ID[@]}
            want_files=$(for i in "${!HP_P_FILE[@]}"; do hp_patch_files "${HP_P_FILE[$i]}"; done | sort -u)
            for range in "$HP_PIN..HEAD" "origin/main..HEAD"; do
                if [ "$range" = "origin/main..HEAD" ]; then
                    if ! hp_git rev-parse --verify -q origin/main >/dev/null || ! hp_git merge-base --is-ancestor "$HP_PIN" origin/main 2>/dev/null; then
                        ok "install:log[origin/main..HEAD]" "skipped (origin/main absent or does not contain the pin)"; continue
                    fi
                fi
                got_n=$(hp_git rev-list --count "$range")
                got_files=$(hp_git diff --name-only "${range%..HEAD}...HEAD" | sort -u)
                if [ "$got_n" = "$want_n" ] && [ "$got_files" = "$want_files" ]; then
                    ok "install:log[$range]" "$got_n commit(s), files match the ledger's patches"
                else
                    no "install:log[$range]" "$got_n commit(s) vs $want_n ledgered patch(es); changed files differ: $(printf '%s\n%s\n' "$got_files" "$want_files" | sort | uniq -u | head -5 | tr '\n' ' ')"
                fi
            done
            for i in "${!HP_P_ID[@]}"; do
                hp_patch_applied "${HP_P_FILE[$i]}" && ok "install:patch:${HP_P_ID[$i]}" "in the tree" \
                    || no "install:patch:${HP_P_ID[$i]}" "not (fully) in the tree"
            done
        else
            no install:pin "pin ${HP_PIN:-?} is not an ancestor of HEAD (pin bump without rebase? see README rebase rule)"
        fi
        dirty=$(hp_git status --porcelain --untracked-files=no)
        [ -z "$dirty" ] && ok install:clean "no uncommitted changes to tracked files" || no install:clean "uncommitted changes: $(printf '%s' "$dirty" | head -3 | tr '\n' ';')"
    fi

    # plist: the stowed module file is the owner. A symlink into the module is the end state; an identical
    # regular file is the hand-installed state before the first `dotm sync` (reported, not failed).
    live="$HP_LA_DIR/$HP_PLIST_NAME"
    if [ -L "$live" ]; then
        target=$(cd "$(dirname "$live")" && cd "$(dirname "$(readlink "$live")")" 2>/dev/null && printf '%s/%s' "$(pwd -P)" "$(basename "$(readlink "$live")")")
        if [ "$target" = "$plist" ] || cmp -s "$live" "$plist"; then ok plist:live "stowed from the module ($live)"; else no plist:live "symlink does not lead to the module file: $(readlink "$live")"; fi
    elif [ -f "$live" ]; then
        cmp -s "$live" "$plist" && ok plist:live "identical to the module file, not yet stowed (unmanaged until dotm sync)" \
            || no plist:live "differs from the module file: diff $live $plist"
    else
        no plist:live "missing: $live (dotm sync stows it)"
    fi

    # doctor
    if [ "$DOCTOR" = 1 ]; then
        hbin="$HP_DIR/.hermes/bin/hermes"
        [ -x "$hbin" ] || hbin=$(command -v hermes || true)
        if [ -z "$hbin" ]; then
            no doctor "no hermes binary"
        else
            out=$(HERMES_HOME="$HERMES_HOME" "$hbin" doctor 2>&1 </dev/null); rc=$?
            if [ "$rc" = 0 ]; then ok doctor "hermes doctor exit 0"
            else no doctor "hermes doctor exit $rc: $(printf '%s\n' "$out" | grep -E 'Found [0-9]+ issue' | head -1 | sed 's/^ *//')"; fi
        fi
    else
        ok doctor "skipped (--no-doctor)"
    fi
fi

mode=full; [ "$DRY" = 1 ] && mode=dry-run
if [ "$JSON" = 1 ]; then
    printf '%s\n' "${lines[@]}" | jq -R -s --arg mode "$mode" --argjson fails "$fails" \
        '{mode:$mode, fails:$fails, checks:(split("\n")|map(select(length>0)|split("|")|{status:.[0],name:.[1],detail:(.[2:]|join("|"))}))}' | jq -c .
else
    printf '%s: %s, %d failure(s)\n' "hermes-platform check" "$mode" "$fails"
fi
[ "$fails" = 0 ]
