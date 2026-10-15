#!/usr/bin/env bash
# hermes-platform setup: make the Hermes platform install restorable from this repo.
#
#   setup.sh [--dry-run] [--skip-bootstrap] [-h|--help]
#
# 1. clone NousResearch/hermes-agent to $HERMES_HOME/hermes-agent (once)
# 2. put local/hermes-patches on the pin in pin.txt
# 3. apply every non-retired patch in the local-patches ledger as one commit each
# 4. run the official installer's dependency stages (scripts/install.sh --stage ...), never its
#    `repository` stage: that stage fast-forwards or resets the checkout and would drop the patches
#
# Idempotent: a second run finds the branch, the patches and the bootstrap marker in place and
# changes nothing. It never touches the gateway, launchd, config.yaml or credentials; the gateway
# LaunchAgent plist is a stowed module file, applied by `dotm sync`.
#
# Exit codes: 0 ok, 1 failure, 2 usage / precondition, 3 patch no longer applies (rebase rule).
# Env: see lib.sh. HERMES_PLATFORM_SKIP_BOOTSTRAP=1 is the same as --skip-bootstrap.
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
# shellcheck source=lib.sh
. "$HERE/lib.sh"

DRY=0
SKIP_BOOT="${HERMES_PLATFORM_SKIP_BOOTSTRAP:-0}"
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY=1 ;;
        --skip-bootstrap) SKIP_BOOT=1 ;;
        -h|--help) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
    shift
done

hp_init_env
say() { printf '%s\n' "$*"; }
act() { if [ "$DRY" = 1 ]; then say "[dry-run] would: $*"; else say "do: $*"; fi; }

command -v git >/dev/null 2>&1 || { echo "git not found" >&2; exit 2; }
hp_read_pin || exit 2
hp_load_patches || exit 2
say "pin:     $HP_PIN"
say "install: $HP_DIR"
say "upstream: $HP_REPO_URL"
say "ledger:  $HP_LEDGER (${#HP_P_ID[@]} patch(es): ${HP_P_ID[*]:-none})"
for i in "${!HP_P_ID[@]}"; do
    [ -s "${HP_P_FILE[$i]}" ] || { echo "patch file for ${HP_P_ID[$i]} missing or empty: ${HP_P_FILE[$i]}" >&2; exit 2; }
done

# --- 1. clone ---------------------------------------------------------------------------------
CLONED=0
if [ -d "$HP_DIR/.git" ]; then
    say "clone:   present"
elif [ -e "$HP_DIR" ] && [ -n "$(ls -A "$HP_DIR" 2>/dev/null)" ]; then
    echo "$HP_DIR exists and is not a git checkout; move it aside" >&2; exit 2
else
    act "git clone --filter=blob:none --no-checkout $HP_REPO_URL $HP_DIR (staged, then moved into place)"
    if [ "$DRY" = 0 ]; then
        mkdir -p "$(dirname "$HP_DIR")"
        # Clone beside the destination and publish only a finished checkout: a --no-checkout clone has an
        # empty index, so an interrupted run must never leave one at $HP_DIR (it would read as "all files
        # deleted"). The staging dir is ours; a leftover from an interrupted run is replaced.
        stage="$HP_DIR.staging"
        rm -rf "$stage"
        "$HP_GIT_BIN" clone --filter=blob:none --no-checkout "$HP_REPO_URL" "$stage" || { echo "git clone failed" >&2; exit 1; }
        # Same treeless-clone hygiene as the official installer (#127711).
        "$HP_GIT_BIN" -C "$stage" config maintenance.commit-graph.enabled false
        "$HP_GIT_BIN" -C "$stage" config gc.writeCommitGraph false
        "$HP_GIT_BIN" -C "$stage" config fetch.writeCommitGraph false
        "$HP_GIT_BIN" -C "$stage" cat-file -e "$HP_PIN^{commit}" 2>/dev/null \
            || { echo "pin $HP_PIN is not in $HP_REPO_URL" >&2; rm -rf "$stage"; exit 1; }
        # --force: the empty index of a --no-checkout clone is not a local change.
        "$HP_GIT_BIN" -C "$stage" switch --quiet --force -c "$HP_BRANCH" "$HP_PIN" \
            || { echo "cannot check out the pin" >&2; exit 1; }
        mv "$stage" "$HP_DIR" || { echo "cannot publish the checkout to $HP_DIR" >&2; exit 1; }
        CLONED=1
    fi
fi

if [ "$DRY" = 1 ] && [ ! -d "$HP_DIR/.git" ]; then
    # Nothing on disk to inspect: describe the rest of the plan and stop.
    act "git switch -c $HP_BRANCH $HP_PIN"
    for i in "${!HP_P_ID[@]}"; do act "git apply -p1 ${HP_P_FILE[$i]} && git commit  (local(${HP_P_ID[$i]}))"; done
    [ "$SKIP_BOOT" = 1 ] || act "scripts/install.sh --stage <each dependency stage except repository>"
    say "dry-run complete: no changes made"
    exit 0
fi

# --- 2. pin + branch --------------------------------------------------------------------------
if ! hp_git cat-file -e "$HP_PIN^{commit}" 2>/dev/null; then
    act "git fetch origin (pin not present locally)"
    if [ "$DRY" = 0 ]; then
        hp_git fetch --quiet origin || { echo "git fetch failed" >&2; exit 1; }
    fi
fi
if [ "$DRY" = 0 ]; then
    hp_git cat-file -e "$HP_PIN^{commit}" 2>/dev/null || { echo "pin $HP_PIN is not in $HP_REPO_URL" >&2; exit 1; }
fi

cur=$(hp_git symbolic-ref --short -q HEAD || true)
if hp_git show-ref --verify --quiet "refs/heads/$HP_BRANCH"; then
    if [ "$cur" != "$HP_BRANCH" ]; then
        if [ -n "$(hp_git status --porcelain --untracked-files=no)" ]; then
            echo "$HP_DIR has tracked changes; commit them as a ledgered patch or move them aside" >&2; exit 1
        fi
        act "git switch $HP_BRANCH"
        [ "$DRY" = 1 ] || hp_git switch --quiet "$HP_BRANCH" || exit 1
    else
        say "branch:  $HP_BRANCH checked out"
    fi
    if ! hp_git merge-base --is-ancestor "$HP_PIN" "$HP_BRANCH" 2>/dev/null; then
        echo "$HP_BRANCH is not based on the pin $HP_PIN" >&2
        hp_rebase_hint
        exit 3
    fi
else
    if [ -n "$(hp_git status --porcelain --untracked-files=no 2>/dev/null)" ]; then
        echo "$HP_DIR has tracked changes; commit them as a ledgered patch or move them aside" >&2; exit 1
    fi
    act "git switch -c $HP_BRANCH $HP_PIN"
    [ "$DRY" = 1 ] || hp_git switch --quiet -c "$HP_BRANCH" "$HP_PIN" || exit 1
fi

# --- 3. patches -------------------------------------------------------------------------------
# Identity for the patch commits only when the machine has none; never signs (setup must not need a
# key agent), the ledger commit sha is informational and differs per machine.
ident=()
hp_git config user.name >/dev/null 2>&1 || ident+=(-c "user.name=hermes-platform")
hp_git config user.email >/dev/null 2>&1 || ident+=(-c "user.email=hermes-platform@localhost")
applied=0 skipped=0
for i in "${!HP_P_ID[@]}"; do
    id="${HP_P_ID[$i]}" pf="${HP_P_FILE[$i]}" desc="${HP_P_DESC[$i]}"
    if hp_patch_applied "$pf"; then
        say "patch:   $id already in the tree"
        skipped=$((skipped + 1)); continue
    fi
    if ! err=$(hp_git apply -p1 --check "$pf" 2>&1); then
        echo "patch $id does not apply to $HP_BRANCH:" >&2; printf '%s\n' "$err" | sed 's/^/  /' >&2
        hp_rebase_hint
        exit 3
    fi
    act "git apply -p1 $pf; git commit \"local($id): $desc\""
    if [ "$DRY" = 0 ]; then
        hp_git apply -p1 --index "$pf" || { hp_rebase_hint; exit 3; }
        hp_git "${ident[@]+"${ident[@]}"}" -c commit.gpgsign=false commit --quiet \
            -m "local($id): $desc" -m "Applied by modules/hermes-platform/setup.sh from the local-patches ledger ($pf)." || exit 1
    fi
    applied=$((applied + 1))
done

# --- 4. official bootstrap --------------------------------------------------------------------
marker="$HP_DIR/.hermes-bootstrap-complete"
need_boot=1
if [ "$applied" = 0 ] && [ -x "$HP_DIR/.hermes/bin/hermes" ] && [ -f "$marker" ]; then
    head=$(hp_git rev-parse HEAD 2>/dev/null || true)
    if [ -n "$head" ] && grep -q "\"pinnedCommit\": \"$head\"" "$marker" 2>/dev/null; then need_boot=0; fi
fi
if [ "$SKIP_BOOT" = 1 ]; then
    say "bootstrap: skipped by request"
elif [ "$need_boot" = 0 ]; then
    say "bootstrap: marker matches HEAD, nothing to do"
else
    installer="$HP_DIR/scripts/install.sh"
    if [ "$DRY" = 1 ] && [ "$applied" -gt 0 ]; then
        act "scripts/install.sh --dir $HP_DIR --hermes-home $HERMES_HOME --non-interactive --stage <each dependency stage except repository>"
    elif [ ! -f "$installer" ]; then
        echo "official installer not found: $installer" >&2; exit 1
    else
        command -v jq >/dev/null 2>&1 || { echo "jq not found" >&2; exit 2; }
        stages=$(bash "$installer" --manifest --dir "$HP_DIR" --hermes-home "$HERMES_HOME" \
            | jq -r '.stages[] | select(.needs_user_input | not) | .name') || { echo "installer manifest failed" >&2; exit 1; }
        for s in $stages; do
            [ "$s" = repository ] && continue   # would move HEAD off the patch branch
            act "install.sh --stage $s"
            if [ "$DRY" = 0 ]; then
                HERMES_HOME="$HERMES_HOME" bash "$installer" --dir "$HP_DIR" --hermes-home "$HERMES_HOME" \
                    --non-interactive --stage "$s" || { echo "installer stage $s failed" >&2; exit 1; }
            fi
        done
        # The installer must leave the checkout where setup put it.
        [ "$DRY" = 1 ] || [ "$(hp_git symbolic-ref --short -q HEAD)" = "$HP_BRANCH" ] \
            || { echo "installer moved HEAD off $HP_BRANCH" >&2; exit 1; }
    fi
fi

if [ "$DRY" = 1 ]; then say "dry-run complete: no changes made"; else
    say "setup complete: cloned=$CLONED patches_applied=$applied patches_present=$skipped"
    say "next: modules/hermes-platform/check.sh"
fi
exit 0
