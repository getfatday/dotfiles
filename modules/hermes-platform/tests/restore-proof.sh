#!/usr/bin/env bash
# restore-proof.sh: restore-from-clean-machine proof for the dotfiles repo and the hermes-platform module.
#
# Provisions a clean macOS environment, applies the dotfiles bootstrap (the steps `dotm bootstrap`
# prints: clone, install uv, first `dotm sync` from the clone) with the hermes-host capability declared,
# then runs the module setup script, every dotm module check and the hermes-platform check, and appends
# ONE row to the lab's ledger/restore-proof.jsonl:
#
#   {ts, environment, bootstrap_sha, checks: [{module, pass, ...}], result, hand_steps: []}
#
# Environment, in order of preference:
#   1. a Tart VM (the `tart` module; needs the tart binary and RP_MIN_FREE_GB of free disk),
#   2. a fresh macOS user account (needs non-interactive sudo; sysadminctl needs admin auth).
# If neither can be provisioned the row is a `fail` with environment "none": each blocker is a hand step.
#
# Any hand step makes result `fail`; hand_steps is the backlog. Credentials are never part of the proof:
# a check that needs a signed-in state (Mac App Store apps) is recorded as pass:null,
# status:"skipped-credential", and does not fail the row.
#
# Known hand step, recorded whenever an environment is reached: the hermes-platform setup reads the
# patch ledger and patch files from the lab repo (hyp-hermes, which has no remote), so that repo's
# ledger/ and patch files are copied in. A clean machine cannot fetch them from dotfiles alone.
#
# Usage:
#   restore-proof.sh              run the proof, append the row
#   restore-proof.sh --preflight  report which environment would be used; change nothing, write no row
#   restore-proof.sh --no-row     run, print the row, do not touch the ledger
#   restore-proof.sh --keep       do not delete the VM / account afterwards
#
# Env: RP_LEDGER (default ~/src/hyp-hermes/ledger/restore-proof.jsonl), RP_LAB_REPO (default
#   ~/src/hyp-hermes), RP_IMAGE (default ghcr.io/cirruslabs/macos-tahoe-base:latest), RP_MIN_FREE_GB
#   (default 60), RP_TART (path to tart), TART_HOME (move VM storage to a bigger volume),
#   RP_ALLOW_USER_ACCOUNT=1 (opt in to the user-account fallback; sudo prompts for admin approval).
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
REPO=$(git -C "$HERE" rev-parse --show-toplevel)
RP_LAB_REPO="${RP_LAB_REPO:-$HOME/src/hyp-hermes}"
RP_LEDGER="${RP_LEDGER:-$RP_LAB_REPO/ledger/restore-proof.jsonl}"
RP_IMAGE="${RP_IMAGE:-ghcr.io/cirruslabs/macos-tahoe-base:latest}"
RP_MIN_FREE_GB="${RP_MIN_FREE_GB:-60}"
MODE=run KEEP=0 WRITE=1
for a in "$@"; do
    case "$a" in
        --preflight) MODE=preflight ;;
        --no-row) WRITE=0 ;;
        --keep) KEEP=1 ;;
        -h|--help) sed -n '2,34p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $a" >&2; exit 2 ;;
    esac
done

WORK=$(mktemp -d "${TMPDIR:-/tmp}/restore-proof.XXXXXX")
CHECKS="$WORK/checks.jsonl"; HANDS="$WORK/hands.txt"; : > "$CHECKS"; : > "$HANDS"
ENV_KIND=none ENV_DESC=none VM="" RP_USER=""

log() { printf 'restore-proof: %s\n' "$*" >&2; }
hand() { printf '%s\n' "$*" >> "$HANDS"; log "HAND STEP: $*"; }
check() { # module pass(true|false|null) detail [status]
    python3 - "$@" >> "$CHECKS" <<'PY'
import json, sys
m, p, d = sys.argv[1:4]
row = {"module": m, "pass": {"true": True, "false": False, "null": None}[p], "detail": d}
if len(sys.argv) > 4:
    row["status"] = sys.argv[4]
print(json.dumps(row))
PY
}

BOOTSTRAP_SHA=$(git -C "$REPO" rev-parse --short=12 HEAD)
dirty=$(git -C "$REPO" status --porcelain --untracked-files=no 2>/dev/null)
[ -z "$dirty" ] || { BOOTSTRAP_SHA="$BOOTSTRAP_SHA+dirty"; log "warning: tracked changes in $REPO; the bundle carries HEAD only"; }
BRANCH=$(git -C "$REPO" rev-parse --abbrev-ref HEAD)

# --- environment selection ---------------------------------------------------------------------
free_gb() { # free GiB on the volume that holds (or would hold) the VM storage
    local d="${TART_HOME:-$HOME/.tart}"
    while [ ! -d "$d" ] && [ "$d" != / ]; do d=$(dirname "$d"); done
    df -g "$d" | awk 'NR==2{print $4}'
}

pick_environment() {
    local tart="${RP_TART:-}" gb ok=1
    [ -n "$tart" ] || tart=$(command -v tart || true)
    [ -n "$tart" ] || { [ -x "$HOME/.local/bin/tart" ] && tart="$HOME/.local/bin/tart"; }
    TART="$tart"
    if [ -z "$tart" ]; then
        ok=0
        check provision:tart-binary false "tart binary not found (module tart needs capability virtualization-host)"
        hand "install tart: declare capability virtualization-host in ~/.config/dotm/config.yml, then dotm sync (module tart), or set RP_TART"
    else
        check provision:tart-binary true "tart at $tart"
    fi
    gb=$(free_gb)
    if [ "${gb:-0}" -lt "$RP_MIN_FREE_GB" ]; then
        ok=0
        check provision:tart-disk false "only ${gb:-?} GiB free for VM storage; a macOS image needs >= $RP_MIN_FREE_GB GiB"
        hand "free disk: $RP_MIN_FREE_GB GiB needed for the macOS VM image, ${gb:-?} GiB free; free space or set TART_HOME to a bigger volume"
    else
        check provision:tart-disk true "${gb} GiB free"
    fi
    if [ "$ok" = 1 ]; then ENV_KIND=tart ENV_DESC="tart:$RP_IMAGE"; return 0; fi

    # Fallback: fresh user account. sudo raises an interactive admin-approval prompt on this Mac, so it
    # is only tried when the operator opts in with RP_ALLOW_USER_ACCOUNT=1 (never from a headless run).
    if [ "${RP_ALLOW_USER_ACCOUNT:-0}" = 1 ] && sudo -n true 2>/dev/null; then
        ENV_KIND=user ENV_DESC="user-account"
        check provision:user-account true "non-interactive sudo available"
    elif [ "${RP_ALLOW_USER_ACCOUNT:-0}" = 1 ]; then
        check provision:user-account false "no non-interactive sudo; creating an account needs admin authorisation"
        hand "authorise sudo for the proof (fresh user account fallback)"
    else
        check provision:user-account false "not attempted: needs admin authorisation (set RP_ALLOW_USER_ACCOUNT=1 to opt in)"
        hand "fresh user account fallback needs admin authorisation; run with RP_ALLOW_USER_ACCOUNT=1 from a shell that can approve sudo"
    fi
}

# --- guest plumbing ----------------------------------------------------------------------------
guest() { # run stdin as a login bash script inside the clean environment
    case "$ENV_KIND" in
        tart) "$TART" exec -i "$VM" bash -l -s ;;
        user) sudo -n -u "$RP_USER" -H bash -l -s ;;
    esac
}
put() { # put <local file> <guest path>
    case "$ENV_KIND" in
        tart) "$TART" exec -i "$VM" sh -c 'cat > "$1"' _ "$2" < "$1" ;;
        user) sudo -n -u "$RP_USER" -H tee "$2" < "$1" > /dev/null ;;
    esac
}

provision() {
    case "$ENV_KIND" in
        tart)
            VM="restore-proof-$(date +%s)"
            log "cloning $RP_IMAGE as $VM"
            "$TART" clone "$RP_IMAGE" "$VM" || return 1
            "$TART" run --no-graphics "$VM" > "$WORK/vm.log" 2>&1 &
            for _ in $(seq 1 90); do
                "$TART" exec "$VM" true 2>/dev/null && return 0
                sleep 5
            done
            log "VM never answered tart exec"; return 1 ;;
        user)
            RP_USER="rproof$(date +%s)"
            # throwaway password for a throwaway account; sudo -u never needs it
            sudo -n sysadminctl -addUser "$RP_USER" -home "/Users/$RP_USER" -password "$(uuidgen)" 2>"$WORK/user.log" \
                && sudo -n createhomedir -c -u "$RP_USER" >/dev/null 2>&1 || { cat "$WORK/user.log" >&2; return 1; } ;;
    esac
}

teardown() {
    [ "$KEEP" = 1 ] && { log "keeping $ENV_DESC ${VM}${RP_USER}"; return 0; }
    case "$ENV_KIND" in
        tart) [ -n "$VM" ] && { "$TART" stop "$VM" >/dev/null 2>&1; "$TART" delete "$VM" >/dev/null 2>&1; } ;;
        user) [ -n "$RP_USER" ] && sudo -n sysadminctl -deleteUser "$RP_USER" >/dev/null 2>&1 ;;
    esac
}

# --- the proof ---------------------------------------------------------------------------------
run_proof() {
    local bundle="$WORK/dotfiles.bundle" labbundle="$WORK/lab.tar" guest_home
    git -C "$REPO" bundle create "$bundle" "$BRANCH" >/dev/null 2>&1 || { check bootstrap:bundle false "git bundle failed"; return 1; }
    guest_home=$(echo 'echo $HOME' | guest | tail -1)
    [ -n "$guest_home" ] || { check bootstrap:guest false "cannot run commands in the environment"; return 1; }
    put "$bundle" "/tmp/dotfiles.bundle" || { check bootstrap:copy false "cannot copy the bundle in"; return 1; }

    # Bootstrap = what `dotm bootstrap` prints. The clone comes from a bundle of this exact commit
    # because the branch under test is not on origin; `dotm sync`'s pull then reads the bundle.
    if guest <<EOF > "$WORK/bootstrap.log" 2>&1
set -e
mkdir -p ~/src ~/.config/dotm
git clone -b '$BRANCH' /tmp/dotfiles.bundle ~/src/dotfiles
command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
printf 'capabilities:\n- hermes-host\n' > ~/.config/dotm/config.yml
export PATH="\$HOME/.local/bin:/opt/homebrew/bin:\$PATH"
uv run --project ~/src/dotfiles/modules/dotm/src dotm sync
EOF
    then check bootstrap:dotm-sync true "clone + uv + first dotm sync"
    else check bootstrap:dotm-sync false "see bootstrap.log: $(tail -3 "$WORK/bootstrap.log" | tr '\n' ' ' | cut -c1-300)"; fi

    # Hand step: the lab repo has no remote, so the patch ledger and patch files are copied in.
    hand "copy the patch ledger and patch files from the lab repo (hyp-hermes has no remote) into ~/src/hyp-hermes on the clean machine; hermes-platform setup needs them"
    python3 - "$RP_LAB_REPO/ledger/local-patches.jsonl" > "$WORK/lab-files.txt" <<'PY'
import json, sys
print("ledger/local-patches.jsonl")
for l in open(sys.argv[1]):
    l = l.strip()
    if l and json.loads(l).get("status") != "retired":
        print(json.loads(l)["patch_file"])
PY
    tar -C "$RP_LAB_REPO" -cf "$labbundle" -T "$WORK/lab-files.txt" 2>/dev/null
    put "$labbundle" /tmp/lab.tar && echo 'mkdir -p ~/src/hyp-hermes && tar -C ~/src/hyp-hermes -xf /tmp/lab.tar' | guest

    # The module's documented apply order: setup script, then its check.
    if guest <<'EOF' > "$WORK/setup.log" 2>&1
set -e
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
~/src/dotfiles/modules/hermes-platform/setup.sh
EOF
    then check hermes-platform:setup true "setup.sh exit 0"
    else check hermes-platform:setup false "setup.sh failed: $(tail -3 "$WORK/setup.log" | tr '\n' ' ' | cut -c1-300)"; fi

    # Every dotm module check, as per-module results; mas apps need an App Store sign-in.
    guest <<'EOF' > "$WORK/verify.json" 2> "$WORK/verify.err"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
cd ~/src/dotfiles/modules/dotm/src && uv run python - <<'PY'
import json
from dotm.verify import run_verification
out = []
for mod, checks in run_verification().items():
    real = [c for c in checks if not c[0].startswith("mas:")]
    skipped = [c for c in checks if c[0].startswith("mas:") and not c[1]]
    bad = [c[0] for c in real if not c[1]]
    out.append({"module": mod, "pass": not bad if (real or not skipped) else None,
                "detail": ("missing: " + ", ".join(bad)) if bad else "ok",
                **({"status": "skipped-credential"} if skipped and not real else {})})
print("VERIFY-JSON " + json.dumps(out))
PY
EOF
    python3 - "$WORK/verify.json" >> "$CHECKS" <<'PY'
import json, sys
for l in open(sys.argv[1]):
    if l.startswith("VERIFY-JSON "):
        for r in json.loads(l[len("VERIFY-JSON "):]):
            print(json.dumps(r))
        break
else:
    print(json.dumps({"module": "dotm:verify", "pass": False, "detail": "no verify output"}))
PY

    if guest <<'EOF' > "$WORK/check.log" 2>&1
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
~/src/dotfiles/modules/hermes-platform/check.sh
EOF
    then check hermes-platform true "check.sh exit 0 (includes local patch branch and hermes doctor)"
    else check hermes-platform false "check.sh: $(grep -E '^FAIL' "$WORK/check.log" | head -4 | tr '\n' ' ' | cut -c1-400)"; fi
}

# --- main --------------------------------------------------------------------------------------
pick_environment
if [ "$MODE" = preflight ]; then
    echo "environment: $ENV_DESC"; echo "bootstrap_sha: $BOOTSTRAP_SHA"
    echo "checks:"; sed 's/^/  /' "$CHECKS"; echo "hand_steps:"; sed 's/^/  - /' "$HANDS"
    rm -rf "$WORK"; [ "$ENV_KIND" != none ]; exit $?
fi

if [ "$ENV_KIND" != none ]; then
    if provision; then run_proof; else check provision:boot false "could not start the $ENV_KIND environment"; hand "provisioning the $ENV_KIND environment failed (see run output)"; fi
    teardown
fi

ROW=$(python3 - "$ENV_DESC" "$BOOTSTRAP_SHA" "$CHECKS" "$HANDS" <<'PY'
import datetime, json, sys
env, sha, cf, hf = sys.argv[1:5]
checks = [json.loads(l) for l in open(cf) if l.strip()]
hands = [l.rstrip("\n") for l in open(hf) if l.strip()]
failed = [c for c in checks if c["pass"] is False]
result = "pass" if env != "none" and not hands and not failed else "fail"
print(json.dumps({"ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "environment": env, "bootstrap_sha": sha, "checks": checks,
                  "result": result, "hand_steps": hands}))
PY
)
echo "$ROW"
if [ "$WRITE" = 1 ]; then mkdir -p "$(dirname "$RP_LEDGER")"; printf '%s\n' "$ROW" >> "$RP_LEDGER"; log "row appended to $RP_LEDGER"; fi
rm -rf "$WORK"
[ "$(python3 -c 'import json,sys;print(json.loads(sys.argv[1])["result"])' "$ROW")" = pass ]
