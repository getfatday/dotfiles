#!/usr/bin/env bash
# hermes-platform offline test suite.
#
#   bash modules/hermes-platform/tests/run.sh      exit 0 iff every case passes
#
# Hermetic: a fixture "upstream" git repo, a scratch HERMES_PLATFORM_HOME, a fake official installer,
# GIT_CONFIG_GLOBAL=/dev/null (so no signing, no identity), no network, never touches the real install.
# Cases: dry-run changes nothing; clone+branch+patch; idempotent rerun; check green/red verdicts; a patch
# that no longer applies is exit 3; a pin that is not under the branch is exit 3; missing ledger is exit 2;
# the bootstrap runs every installer stage except `repository`, once.
set -u
HERE=$(cd "$(dirname "$0")" && pwd -P)
MOD=$(dirname "$HERE")
BASE=$(mktemp -d "${TMPDIR:-/tmp}/hp-test.XXXXXX") || exit 2
trap 'rm -rf "$BASE"' EXIT
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
GITBIN=$(command -v git)
if [ "$GITBIN" = /usr/bin/git ] && _d=$(xcode-select -p 2>/dev/null) && [ -x "$_d/usr/bin/git" ]; then GITBIN="$_d/usr/bin/git"; fi
g() { "$GITBIN" "$@"; }
gc() { g -c user.name=fixture -c user.email=fixture@localhost -c commit.gpgsign=false "$@"; }

pass=0 failn=0
expect() { # name expected actual
    if [ "$2" = "$3" ]; then pass=$((pass + 1)); printf 'ok    %s\n' "$1"
    else failn=$((failn + 1)); printf 'FAIL  %s: want [%s] got [%s]\n' "$1" "$2" "$3"; fi
}
has() { # name haystack needle
    case "$2" in *"$3"*) pass=$((pass + 1)); printf 'ok    %s\n' "$1" ;; *) failn=$((failn + 1)); printf 'FAIL  %s: output lacks [%s]\n' "$1" "$3" ;; esac
}

# --- fixture upstream: c1 (the pin), c2 (upstream moved on) ---
UP=$BASE/upstream; mkdir -p "$UP/hermes_cli" "$UP/scripts"
printf 'def alive():\n    return 1\n' > "$UP/hermes_cli/dispatch.py"
cat > "$UP/scripts/install.sh" <<'EOS'
#!/usr/bin/env bash
# fake official installer: --manifest lists stages; --stage S records S; `complete` writes the marker.
dir="" stage="" manifest=0
while [ $# -gt 0 ]; do case "$1" in --dir) dir=$2; shift ;; --stage) stage=$2; shift ;; --manifest) manifest=1 ;; esac; shift; done
if [ "$manifest" = 1 ]; then
  echo '{"stages":[{"name":"prerequisites","needs_user_input":false},{"name":"repository","needs_user_input":false},{"name":"python-deps","needs_user_input":false},{"name":"setup","needs_user_input":true},{"name":"complete","needs_user_input":false}]}'; exit 0
fi
echo "$stage" >> "$dir/../stages.log"
if [ "$stage" = complete ]; then
  mkdir -p "$dir/.hermes/bin"; printf '#!/bin/sh\nexit 0\n' > "$dir/.hermes/bin/hermes"; chmod +x "$dir/.hermes/bin/hermes"
  printf '{"pinnedCommit": "%s"}\n' "$(git -C "$dir" rev-parse HEAD)" > "$dir/.hermes-bootstrap-complete"
fi
exit 0
EOS
g init -q -b main "$UP" && g -C "$UP" add -A && gc -C "$UP" commit -q -m c1
PIN=$(g -C "$UP" rev-parse HEAD)
printf 'def alive():\n    return 1\n\n\ndef other():\n    return 2\n' > "$UP/hermes_cli/dispatch.py"
gc -C "$UP" commit -q -am c2
NEWPIN=$(g -C "$UP" rev-parse HEAD)

# --- patch (plain -p1 diff against c1, like the ledger's) and ledger ---
LAB=$BASE/lab; mkdir -p "$LAB/ledger" "$LAB/patches"
cat > "$LAB/patches/p1.patch" <<'EOP'
--- a/hermes_cli/dispatch.py
+++ b/hermes_cli/dispatch.py
@@ -1,2 +1,2 @@
 def alive():
-    return 1
+    return 1 + 0  # local patch
EOP
printf '%s\n' '{"id": "LP-1", "patch_file": "patches/p1.patch", "narrow_description": "fixture patch", "status": "applied-not-live"}' \
    '{"id": "LP-0", "patch_file": "patches/gone.patch", "narrow_description": "retired row is ignored", "status": "retired"}' > "$LAB/ledger/local-patches.jsonl"

export HERMES_REPO_URL="file://$UP" HERMES_PLATFORM_PIN="$PIN" HERMES_PLATFORM_LEDGER="$LAB/ledger/local-patches.jsonl"
export HERMES_PLATFORM_HOME="$BASE/home/.hermes"
LA=$BASE/la; mkdir -p "$LA"; export HERMES_PLATFORM_LAUNCH_AGENT_DIR="$LA"
INST=$HERMES_PLATFORM_HOME/hermes-agent
S=$MOD/setup.sh C=$MOD/check.sh

# 1 dry-run on an empty machine
out=$("$S" --dry-run 2>&1); rc=$?
expect "dry-run exits 0" 0 "$rc"
has "dry-run plans the clone" "$out" "would: git clone"
has "dry-run plans the branch" "$out" "git switch -c local/hermes-patches"
expect "dry-run creates nothing" "no" "$([ -e "$INST" ] && echo yes || echo no)"

# 2 real setup (no bootstrap): clone, branch, one patch commit
out=$("$S" --skip-bootstrap 2>&1); rc=$?
expect "setup exits 0" 0 "$rc"
expect "branch checked out" local/hermes-patches "$(g -C "$INST" symbolic-ref --short HEAD)"
expect "one commit above the pin" 1 "$(g -C "$INST" rev-list --count "$PIN..HEAD")"
expect "parent of the patch commit is the pin" "$PIN" "$(g -C "$INST" rev-parse HEAD^)"
has "patch is in the file" "$(cat "$INST/hermes_cli/dispatch.py")" "return 1 + 0"
has "commit message names the ledger id" "$(g -C "$INST" log -1 --format=%s)" "local(LP-1): fixture patch"
expect "retired rows are not applied" "no" "$(g -C "$INST" log --format=%s | grep -q 'LP-0' && echo yes || echo no)"

# 3 idempotent rerun
head1=$(g -C "$INST" rev-parse HEAD)
out=$("$S" --skip-bootstrap 2>&1); rc=$?
expect "rerun exits 0" 0 "$rc"
expect "rerun leaves HEAD alone" "$head1" "$(g -C "$INST" rev-parse HEAD)"
has "rerun reports the patch present" "$out" "already in the tree"
expect "rerun leaves the tree clean" "" "$(g -C "$INST" status --porcelain)"

# 4 check verdicts
cp "$MOD/files/Library/LaunchAgents/ai.hermes.gateway.plist" "$LA/"
out=$("$C" --no-doctor 2>&1); rc=$?
expect "check green on a fresh install" 0 "$rc"
has "check sees the patch" "$out" "install:patch:LP-1: in the tree"
out=$("$C" --dry-run 2>&1); rc=$?
expect "check --dry-run green" 0 "$rc"
printf '\n' >> "$LA/ai.hermes.gateway.plist"
"$C" --no-doctor >/dev/null 2>&1; expect "check red when the live plist differs" 1 "$?"
cp "$MOD/files/Library/LaunchAgents/ai.hermes.gateway.plist" "$LA/"
echo "# drift" >> "$INST/hermes_cli/dispatch.py"
"$C" --no-doctor >/dev/null 2>&1; expect "check red on an uncommitted install change" 1 "$?"
g -C "$INST" checkout -q -- hermes_cli/dispatch.py
echo "x = 1" > "$INST/hermes_cli/extra.py"; g -C "$INST" add hermes_cli/extra.py; gc -C "$INST" commit -q -m "stray local commit"
out=$("$C" --no-doctor 2>&1); rc=$?
expect "check red on a commit that is not a ledgered patch" 1 "$rc"
has "check names the range" "$out" "2 commit(s) vs 1 ledgered"
g -C "$INST" reset -q --hard HEAD^
g -C "$INST" switch -q -c elsewhere
"$C" --no-doctor >/dev/null 2>&1; expect "check red when HEAD is not on the patch branch" 1 "$?"
g -C "$INST" switch -q local/hermes-patches
"$C" --no-doctor >/dev/null 2>&1; expect "check green again after restoring" 0 "$?"
out=$("$C" --no-doctor --json 2>&1); has "check --json is one object" "$out" '"fails":0'

# 5 a pin that is not under the branch is the rebase rule, exit 3
out=$(HERMES_PLATFORM_PIN="$NEWPIN" "$S" --skip-bootstrap 2>&1); rc=$?
expect "pin bump without rebase exits 3" 3 "$rc"
has "pin bump prints the rebase rule" "$out" "Rebase rule"
"$C" --no-doctor >/dev/null 2>&1; expect "check still green on the old pin" 0 "$?"
HERMES_PLATFORM_PIN="$NEWPIN" "$C" --no-doctor >/dev/null 2>&1; expect "check red on a pin the branch is not based on" 1 "$?"

# 6 a patch that no longer applies (fresh scratch) is exit 3 and leaves no half-applied tree
cat > "$LAB/patches/p1.patch" <<'EOP'
--- a/hermes_cli/dispatch.py
+++ b/hermes_cli/dispatch.py
@@ -1,2 +1,2 @@
 def alive():
-    return 99
+    return 100
EOP
export HERMES_PLATFORM_HOME="$BASE/home2/.hermes"; INST2=$HERMES_PLATFORM_HOME/hermes-agent
out=$("$S" --skip-bootstrap 2>&1); rc=$?
expect "non-applying patch exits 3" 3 "$rc"
has "non-applying patch names the patch" "$out" "patch LP-1 does not apply"
expect "no commit was made" 0 "$(g -C "$INST2" rev-list --count "$PIN..HEAD")"
expect "tree is clean" "" "$(g -C "$INST2" status --porcelain --untracked-files=no)"

# 7 missing ledger is exit 2 and says so
out=$(HERMES_PLATFORM_LEDGER="$BASE/nope.jsonl" "$S" --skip-bootstrap 2>&1); rc=$?
expect "missing ledger exits 2" 2 "$rc"
has "missing ledger is named" "$out" "patch ledger not found"

# 8 bootstrap: every installer stage except repository, user-input stages skipped, once
cat > "$LAB/patches/p1.patch" <<'EOP'
--- a/hermes_cli/dispatch.py
+++ b/hermes_cli/dispatch.py
@@ -1,2 +1,2 @@
 def alive():
-    return 1
+    return 1 + 0  # local patch
EOP
export HERMES_PLATFORM_HOME="$BASE/home3/.hermes"; INST3=$HERMES_PLATFORM_HOME/hermes-agent
out=$("$S" 2>&1); rc=$?
expect "setup with bootstrap exits 0" 0 "$rc"
expect "installer stages run" "prerequisites python-deps complete" "$(tr '\n' ' ' < "$HERMES_PLATFORM_HOME/stages.log" | sed 's/ $//')"
expect "installer left HEAD on the branch" local/hermes-patches "$(g -C "$INST3" symbolic-ref --short HEAD)"
out=$("$S" 2>&1); rc=$?
expect "second setup exits 0" 0 "$rc"
has "second setup skips the bootstrap" "$out" "marker matches HEAD"
expect "installer was not run twice" 3 "$(wc -l < "$HERMES_PLATFORM_HOME/stages.log" | tr -d ' ')"
out=$("$S" --dry-run 2>&1); has "dry-run on a done install says nothing to do" "$out" "marker matches HEAD"

echo
echo "hermes-platform tests: $pass passed, $failn failed"
[ "$failn" = 0 ]
