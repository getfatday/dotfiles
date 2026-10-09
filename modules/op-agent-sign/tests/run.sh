#!/bin/sh
# op-agent-sign offline test suite: T-S1..T-S16 (docs/03-design.md section 14 of the design repo).
#
#   sh modules/op-agent-sign/tests/run.sh            run everything, exit 0 iff all pass
#   op-agent-sign selftest                           same suite against the installed wrapper
#
# Hermetic by construction: private 0700 base dir (under $TMPDIR, or /tmp when $TMPDIR is too long for a
# unix socket path), temp HOME, throwaway ed25519 keys generated at run time, GIT_CONFIG_GLOBAL=/dev/null,
# PATH starts with tests/bin so `op` is the fake (asserted, else abort), real signer fallback disabled.
# No network, no real token, no key file in the repo. Needs only /bin/sh, /usr/bin/ssh-*, git, perl optional.
#
# Env: OP_AGENT_SIGN_BIN (wrapper under test; default ../files/.local/bin/op-agent-sign), OP_AGENT_SIGN_KEEP=1
# keeps the temp dir for debugging.
HERE=$(cd "$(dirname "$0")" && pwd -P) || exit 2
BIN=${OP_AGENT_SIGN_BIN:-$HERE/../files/.local/bin/op-agent-sign}
BIN=$(cd "$(dirname "$BIN")" && pwd -P)/$(basename "$BIN")
KEEP=${OP_AGENT_SIGN_KEEP:-} CASES=${OP_AGENT_SIGN_CASES:-} TEST_DEADLINE=${OP_AGENT_SIGN_TEST_DEADLINE:-30}
# Timing slack added to DEADLINE in the T-S5/T-S6 elapsed-time bounds (design says 2 s; a loaded Mac needs more).
SLACK=${OP_AGENT_SIGN_TEST_SLACK:-8}
[ -x "$BIN" ] || { echo "wrapper not found or not executable: $BIN" >&2; exit 2; }

# Scrub inherited state that could leak into (or out of) the tests.
for _v in $(env | awk -F= '$1 ~ /^(OP|GIT|SSH|FAKE|HERMES)_/ {print $1}'); do unset "$_v" 2>/dev/null; done

# --- private base dir; socket paths must stay under ~104 bytes ---
BASE=""
for _root in "${TMPDIR:-/tmp}" /tmp; do
  _b=$(mktemp -d "${_root%/}/o.XXXXXX") || continue
  if [ ${#_b} -le 58 ]; then BASE=$_b; break; fi
  rmdir "$_b"
done
[ -n "$BASE" ] || { echo "cannot create a short temp dir" >&2; exit 2; }
chmod 700 "$BASE"
HOME=$BASE/h TMPDIR=$BASE/tmp
OUT=$BASE/o REPOS=$BASE/r VAULT=$BASE/v STRAY=$BASE/s FAKE_OP_DIR=$BASE/f RT=$HOME/.cache/op-agent-sign
mkdir -p "$HOME/.config/op-agent-sign" "$TMPDIR" "$OUT" "$REPOS" "$VAULT" "$STRAY" "$FAKE_OP_DIR"
chmod 700 "$HOME" "$HOME/.config" "$HOME/.config/op-agent-sign" "$TMPDIR" "$OUT" "$REPOS" "$VAULT" "$STRAY" "$FAKE_OP_DIR"
PATH=$HERE/bin:$PATH
GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
export HOME TMPDIR PATH GIT_CONFIG_GLOBAL GIT_CONFIG_NOSYSTEM FAKE_OP_DIR

# /usr/bin/git can be a slow xcode-select shim (~1.6 s per call); call the real binary directly.
GITBIN=$(command -v git)
if [ "$GITBIN" = /usr/bin/git ] && _dev=$(xcode-select -p 2>/dev/null) && [ -x "$_dev/usr/bin/git" ]; then GITBIN=$_dev/usr/bin/git; fi
git() { "$GITBIN" "$@"; }

cleanup() {
  "$BIN" flush >/dev/null 2>&1
  pkill -f "$BASE/h/" 2>/dev/null
  [ -n "$KEEP" ] || rm -rf "$BASE"
}
trap cleanup EXIT
trap 'exit 130' INT TERM HUP

# --- never touch the network: `op` must resolve to the fake ---
case $(command -v op) in
  "$HERE"/bin/op) ;;
  *) echo "ABORT: op resolves to '$(command -v op)', not the fake in $HERE/bin" >&2; exit 2 ;;
esac

# --- throwaway keys (run time only) ---
KG=/usr/bin/ssh-keygen
"$KG" -q -t ed25519 -N '' -C oas-test -f "$VAULT/key" || exit 2
"$KG" -q -t ed25519 -N '' -C oas-other -f "$VAULT/other" || exit 2
cp "$VAULT/key" "$VAULT/enc"
"$KG" -q -p -P '' -N 'throwaway-phrase' -f "$VAULT/enc" >/dev/null || exit 2
cp "$VAULT/other" "$STRAY/key"
cp "$VAULT/key.pub" "$STRAY/key.pub"
PUBFILE=$VAULT/key.pub
PUBLINE=$(cut -d' ' -f1,2 "$PUBFILE")
PRINCIPAL=tester@example.invalid
ALLOWED=$HOME/.config/op-agent-sign/allowed_signers
printf '%s namespaces="git" %s\n' "$PRINCIPAL" "$PUBLINE" >"$ALLOWED"
KB2=$(sed -n 2p "$VAULT/key") KB3=$(sed -n 3p "$VAULT/key")
[ -n "$KB2" ] && [ -n "$KB3" ] || { echo "unexpected key file layout" >&2; exit 2; }
FAKE_TOKEN="fake-sa-token-$(date +%s)-$$-$(awk 'BEGIN { srand(); print int(rand() * 1000000000) }')"
FAKE_OP_KEY=$VAULT/key FAKE_OP_ENC_KEY=$VAULT/enc FAKE_OP_OTHER_KEY=$VAULT/other
FAKE_FB=$HERE/bin/op-ssh-sign
export FAKE_OP_KEY FAKE_OP_ENC_KEY FAKE_OP_OTHER_KEY FAKE_OP_MODE FAKE_OP_DELAY FAKE_OP_SLOW_SECS
export OP_AGENT_SIGN_FALLBACK OP_AGENT_SIGN_TTL OP_AGENT_SIGN_DEADLINE OP_AGENT_SIGN_DEBUG OP_AGENT_SIGN_SSH_KEYGEN

# --- helpers ---
PASSED="" FAILED="" T_NAME="" T_OK=1 RUNNER="" UFLAG=-U rc=0
mk_config() {
  printf 'OP_AGENT_SIGN_KEY_REF="op://fakevault/fakeitem/private_key?ssh-format=openssh"\n' >"$HOME/.config/op-agent-sign/config"
  chmod 600 "$HOME/.config/op-agent-sign/config"
  printf 'OP_SERVICE_ACCOUNT_TOKEN=%s\n' "$FAKE_TOKEN" >"$HOME/.config/op-agent-sign/token.env"
  chmod 600 "$HOME/.config/op-agent-sign/token.env"
}
reset() {
  "$BIN" flush >/dev/null 2>&1
  pkill -f "$RT/agent" 2>/dev/null
  rm -rf "$RT"
  : >"$FAKE_OP_DIR/op.calls"
  rm -f "$FAKE_OP_DIR/fallback.calls" "$FAKE_OP_DIR/op.env" "$FAKE_OP_DIR/kg.env"
  unset PUB FAKE_OP_DELAY FAKE_OP_SLOW_SECS OP_SERVICE_ACCOUNT_TOKEN OP_AGENT_SIGN_SSH_KEYGEN OP_AGENT_SIGN_CONFIG OP_AGENT_SIGN_TOKEN_FILE
  FAKE_OP_MODE=ok OP_AGENT_SIGN_FALLBACK=none OP_AGENT_SIGN_TTL=3600 OP_AGENT_SIGN_DEADLINE=$TEST_DEADLINE
  OP_AGENT_SIGN_DEBUG=$OUT/debug.log RUNNER="" UFLAG=-U
  mk_config
}
ncalls() { wc -l <"$FAKE_OP_DIR/op.calls" | tr -d ' '; }
nfb() { if [ -f "$FAKE_OP_DIR/fallback.calls" ]; then wc -l <"$FAKE_OP_DIR/fallback.calls" | tr -d ' '; else echo 0; fi; }
nagents() { pgrep -f "$RT/agent" | wc -l | tr -d ' '; }
# Agent teardown is asynchronous on a loaded machine: poll for up to ~6 s.
agents_gone() { _n=0; while [ "$(nagents)" != 0 ] && [ "$_n" -lt 12 ]; do sleep 0.5; _n=$((_n + 1)); done; [ "$(nagents)" = 0 ]; }
now() { date +%s; }
# Detach from any controlling terminal so ssh-add can never prompt on /dev/tty.
nottty() { if [ -x /usr/bin/perl ]; then /usr/bin/perl -MPOSIX -e 'POSIX::setsid(); exec @ARGV or exit 127' -- "$@"; else "$@"; fi; }
absent() { ! "$@"; }
errhas() { grep -q -- "$1" "$OUT/last.err"; }
# Call the wrapper directly like git does; outputs go to files (and are accumulated for the leak scan).
wsign() {
  printf 'payload %s\n' "$$" >"$TMPDIR/buf"
  rm -f "$TMPDIR/buf.sig"
  # shellcheck disable=SC2086
  $RUNNER "$BIN" -Y sign -n git -f "${PUB:-$PUBFILE}" $UFLAG "$TMPDIR/buf" >"$OUT/last.out" 2>"$OUT/last.err" </dev/null
  rc=$?
  cat "$OUT/last.out" >>"$OUT/all.out"
  cat "$OUT/last.err" >>"$OUT/all.err"
}
stock_verify() { "$KG" -Y verify -f "$ALLOWED" -I "$PRINCIPAL" -n git -s "$TMPDIR/buf.sig" <"$TMPDIR/buf" >/dev/null 2>&1; }
mkrepo() { # name [signingkey]
  _d=$REPOS/$1
  mkdir -p "$_d"
  git -C "$_d" init -q
  git -C "$_d" config user.name tester
  git -C "$_d" config user.email "$PRINCIPAL"
  git -C "$_d" config gpg.format ssh
  git -C "$_d" config user.signingkey "${2:-key::$PUBLINE}"
  git -C "$_d" config gpg.ssh.program "$BIN"
  git -C "$_d" config gpg.ssh.allowedSignersFile "$ALLOWED"
  git -C "$_d" config commit.gpgsign true
}
gcommit() { $RUNNER git -C "$REPOS/$1" commit -q --allow-empty -m "${2:-t}" >>"$OUT/all.out" 2>>"$OUT/all.err" </dev/null; }
head_is_G() { [ "$(git -C "$REPOS/$1" log -1 --format=%G? 2>/dev/null)" = G ]; }
verifies() { git -C "$REPOS/$1" verify-commit HEAD >/dev/null 2>&1; }
no_commit() { ! git -C "$REPOS/$1" rev-parse -q --verify HEAD >/dev/null 2>&1; }
t_begin() { T_NAME=$1; T_OK=1; reset; }
expect() { _m=$1; shift; "$@" >/dev/null || { T_OK=0; printf '    expect failed: %s\n' "$_m"; }; }
t_end() {
  if [ "$T_OK" = 1 ]; then echo "PASS $T_NAME"; PASSED="$PASSED ${T_NAME%% *}"
  else echo "FAIL $T_NAME"; FAILED="$FAILED ${T_NAME%% *}"; fi
}

echo "op-agent-sign selftest: wrapper=$BIN"
echo "  base=$BASE  fake op=$(command -v op)  $(ssh -V 2>&1 | head -1)  sh=$(readlink /bin/sh 2>/dev/null || echo /bin/sh)"
# shellcheck source=/dev/null
. "$HERE/cases/ts.sh"
# shellcheck source=/dev/null
. "$HERE/cases/td.sh"
for _c in ${CASES:-ts01 ts02 ts03 ts04 ts05 ts06 ts07 ts08 ts10 ts11 ts12 ts13 ts14 ts15 $TD_CASES ts09 ts16}; do "$_c"; done

echo
echo "PASSED:${PASSED:- none}"
echo "FAILED:${FAILED:- none}"
_want=$((16 + $(echo $TD_CASES | wc -w))); [ -z "$CASES" ] || _want=$(echo $CASES | wc -w | tr -d ' ')
if [ -z "$FAILED" ] && [ "$(echo $PASSED | wc -w | tr -d ' ')" = "$_want" ]; then echo "RESULT: all $_want passed"; exit 0; fi
echo "RESULT: failures (or fewer than $_want cases ran)"
exit 1
