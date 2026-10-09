# T-S1..T-S16 cases, sourced by tests/run.sh (uses its helpers). One function per case.
# T-S9 (leak scan) runs second to last so its sweep covers the artifacts of every other case.

ts01() {
  t_begin "T-S1 git commit -S with key::<pub>, verify-commit, stock ssh-keygen verify"
  mkrepo r1
  gcommit r1
  expect "commit exists" git -C "$REPOS/r1" rev-parse -q --verify HEAD
  expect "verify-commit OK" verifies r1
  expect "%G? is G" head_is_G r1
  wsign
  expect "direct sign rc 0" [ "$rc" = 0 ]
  expect "stock ssh-keygen -Y verify accepts" stock_verify
  expect "one fetch" [ "$(ncalls)" = 1 ]
  t_end
}

ts02() {
  t_begin "T-S2 signingkey=<path>.pub with a stray private key beside it: -U added, stray unused"
  # The stray private key next to key.pub is a DIFFERENT key; if the wrapper did not force -U,
  # ssh-keygen would sign with it and verification against the real key would fail.
  mkrepo r2 "$STRAY/key.pub"
  gcommit r2
  expect "commit exists" git -C "$REPOS/r2" rev-parse -q --verify HEAD
  expect "signed by the agent key (G)" head_is_G r2
  expect "verify-commit OK" verifies r2
  expect "fake op was called" [ "$(ncalls)" = 1 ]
  PUB=$STRAY/key.pub
  UFLAG=""
  wsign
  expect "direct sign without -U rc 0" [ "$rc" = 0 ]
  expect "stock verify accepts (agent key, not stray)" stock_verify
  unset PUB
  UFLAG=-U
  t_end
}

ts03() {
  t_begin "T-S3 CRLF key output from op still signs"
  FAKE_OP_MODE=crlf
  mkrepo r3
  gcommit r3
  expect "commit exists" git -C "$REPOS/r3" rev-parse -q --verify HEAD
  expect "G" head_is_G r3
  expect "one fetch" [ "$(ncalls)" = 1 ]
  t_end
}

ts04() {
  t_begin "T-S4 wrong key: exit 72, no commit, fallback not called"
  FAKE_OP_MODE=wrongkey OP_AGENT_SIGN_FALLBACK=$FAKE_FB
  mkrepo r4
  gcommit r4
  expect "no commit" no_commit r4
  wsign
  expect "exit 72" [ "$rc" = 72 ]
  expect "message names the mismatch" errhas "no key matching"
  expect "fallback not called" [ "$(nfb)" = 0 ]
  t_end
}

ts05() {
  t_begin "T-S5 passphrase-protected key: exit 72 within DEADLINE, no commit"
  FAKE_OP_MODE=encrypted RUNNER=nottty
  mkrepo r5
  _t0=$(now)
  wsign
  _t1=$(now)
  gcommit r5
  expect "no commit" no_commit r5
  expect "exit 72" [ "$rc" = 72 ]
  expect "within DEADLINE ($OP_AGENT_SIGN_DEADLINE s) + slack ($SLACK s)" [ $((_t1 - _t0)) -le $((OP_AGENT_SIGN_DEADLINE + SLACK)) ]
  t_end
}

ts06() {
  t_begin "T-S6 slow op: exit 75 within DEADLINE+2, nothing left behind"
  FAKE_OP_MODE=slow OP_AGENT_SIGN_DEADLINE=3
  export FAKE_OP_SLOW_SECS=47
  for _ttl in 0 3600; do
    OP_AGENT_SIGN_TTL=$_ttl
    _t0=$(now)
    wsign
    _t1=$(now)
    expect "ttl=$_ttl: exit 75" [ "$rc" = 75 ]
    expect "ttl=$_ttl: elapsed $((_t1 - _t0))s <= $((OP_AGENT_SIGN_DEADLINE + SLACK))s (DEADLINE+slack)" [ $((_t1 - _t0)) -le $((OP_AGENT_SIGN_DEADLINE + SLACK)) ]
    expect "ttl=$_ttl: deadline message" errhas "deadline"
    expect "ttl=$_ttl: lock released" [ ! -e "$RT/lock" ]
    expect "ttl=$_ttl: op child killed" [ -z "$(pgrep -f 'sleep 47')" ]
    expect "ttl=$_ttl: no op.err/op.rc left" [ -z "$(ls "$RT" 2>/dev/null | grep -E '^op\.(err|rc)')" ]
    [ "$_ttl" != 0 ] || expect "ttl=0: no agent left" agents_gone
  done
  t_end
}

ts07() {
  t_begin "T-S7 op 429 / 401: exit 75 / 69, fallback called iff configured"
  for _mode in 429 401; do
    case $_mode in 429) _code=75 _msg="rate limited" ;; *) _code=69 _msg="token rejected" ;; esac
    reset
    FAKE_OP_MODE=$_mode
    wsign
    expect "$_mode no fallback: exit $_code" [ "$rc" = "$_code" ]
    expect "$_mode no fallback: message '$_msg'" errhas "$_msg"
    expect "$_mode no fallback: exit code printed" errhas "exit $_code"
    expect "$_mode no fallback: fallback not called" [ "$(nfb)" = 0 ]
    reset
    FAKE_OP_MODE=$_mode OP_AGENT_SIGN_FALLBACK=$FAKE_FB
    wsign
    expect "$_mode with fallback: exit 0" [ "$rc" = 0 ]
    expect "$_mode with fallback: called once" [ "$(nfb)" = 1 ]
    expect "$_mode with fallback: warning printed" errhas "warning: service-account path unavailable"
    expect "$_mode with fallback: signature verifies" stock_verify
  done
  t_end
}

ts08() {
  t_begin "T-S8 no token: fallback set -> called with warning; unset -> exit 69"
  rm -f "$HOME/.config/op-agent-sign/token.env"
  wsign
  expect "no fallback: exit 69" [ "$rc" = 69 ]
  expect "no fallback: message" errhas "no service-account token"
  expect "no fallback: op never called" [ "$(ncalls)" = 0 ]
  OP_AGENT_SIGN_FALLBACK=$FAKE_FB
  wsign
  expect "fallback: exit 0" [ "$rc" = 0 ]
  expect "fallback: called once" [ "$(nfb)" = 1 ]
  expect "fallback: warning on stderr" errhas "warning: service-account path unavailable"
  expect "fallback: op never called" [ "$(ncalls)" = 0 ]
  t_end
}

ts10() {
  t_begin "T-S10 cache: 20 commits with TTL=3600 -> 1 fetch; flush stops the agent"
  mkrepo r10
  _i=0
  while [ "$_i" -lt 20 ]; do _i=$((_i + 1)); gcommit r10 "c$_i"; done
  expect "20 commits" [ "$(git -C "$REPOS/r10" rev-list --count HEAD)" = 20 ]
  expect "all 20 are G" [ "$(git -C "$REPOS/r10" log --format=%G? | sort -u)" = G ]
  expect "fake op called once" [ "$(ncalls)" = 1 ]
  expect "exactly one agent" [ "$(nagents)" = 1 ]
  "$BIN" flush >"$OUT/last.out" 2>"$OUT/last.err"
  expect "flush rc 0" [ $? = 0 ]
  sleep 0.3
  expect "no agent after flush" [ "$(nagents)" = 0 ]
  expect "socket gone" [ ! -e "$RT/agent.sock" ]
  t_end
}

ts11() {
  t_begin "T-S11 8 parallel commits in 8 repos -> all verify, 1 fetch"
  export FAKE_OP_DELAY=1
  _i=0
  while [ "$_i" -lt 8 ]; do _i=$((_i + 1)); mkrepo "p$_i"; done
  _i=0
  while [ "$_i" -lt 8 ]; do
    _i=$((_i + 1))
    ( gcommit "p$_i"; echo $? >"$OUT/prc$_i" ) &
  done
  wait
  _i=0
  while [ "$_i" -lt 8 ]; do
    _i=$((_i + 1))
    expect "p$_i committed (rc $(cat "$OUT/prc$_i"))" [ "$(cat "$OUT/prc$_i")" = 0 ]
    expect "p$_i verifies" verifies "p$_i"
    expect "p$_i is G" head_is_G "p$_i"
  done
  expect "fake op called once" [ "$(ncalls)" = 1 ]
  expect "lock released" [ ! -e "$RT/lock" ]
  t_end
}

ts12() {
  t_begin "T-S12 token only in op's env: wrapper's own env (seen by the signer) never has it"
  printf '#!/bin/sh\nenv | sort >>"%s/kg.env"\nexec /usr/bin/ssh-keygen "$@"\n' "$FAKE_OP_DIR" >"$FAKE_OP_DIR/kg-shim"
  chmod 755 "$FAKE_OP_DIR/kg-shim"
  export OP_AGENT_SIGN_SSH_KEYGEN=$FAKE_OP_DIR/kg-shim
  wsign
  expect "sign rc 0" [ "$rc" = 0 ]
  expect "op env has the token" grep -qx "OP_SERVICE_ACCOUNT_TOKEN=$FAKE_TOKEN" "$FAKE_OP_DIR/op.env"
  expect "op env has OP_LOAD_DESKTOP_APP_SETTINGS=false" grep -qx "OP_LOAD_DESKTOP_APP_SETTINGS=false" "$FAKE_OP_DIR/op.env"
  expect "signer env has no token (token from file)" [ -s "$FAKE_OP_DIR/kg.env" ]
  expect "signer env has no token var" absent grep -q "OP_SERVICE_ACCOUNT_TOKEN" "$FAKE_OP_DIR/kg.env"
  # Token supplied through the environment instead: still stripped before the signer runs.
  reset
  rm -f "$HOME/.config/op-agent-sign/token.env"
  export OP_AGENT_SIGN_SSH_KEYGEN=$FAKE_OP_DIR/kg-shim OP_SERVICE_ACCOUNT_TOKEN=$FAKE_TOKEN
  wsign
  unset OP_SERVICE_ACCOUNT_TOKEN
  expect "env-token: sign rc 0" [ "$rc" = 0 ]
  expect "env-token: op env has the token" grep -qx "OP_SERVICE_ACCOUNT_TOKEN=$FAKE_TOKEN" "$FAKE_OP_DIR/op.env"
  expect "env-token: signer env has no token var" absent grep -q "OP_SERVICE_ACCOUNT_TOKEN" "$FAKE_OP_DIR/kg.env"
  t_end
}

ts13() {
  t_begin "T-S13 stale socket + stale lock: next sign recovers with 1 fetch"
  wsign
  expect "first sign rc 0" [ "$rc" = 0 ]
  _pid=$(cat "$RT/agent.pid")
  kill -9 "$_pid"
  sleep 0.3
  expect "stale socket left behind" [ -S "$RT/agent.sock" ]
  mkdir "$RT/lock"
  sh -c 'echo $$' >"$RT/lock/pid"
  wsign
  expect "recovery rc 0" [ "$rc" = 0 ]
  expect "stock verify" stock_verify
  expect "exactly 1 more fetch (total 2)" [ "$(ncalls)" = 2 ]
  expect "new agent pid" [ "$(cat "$RT/agent.pid")" != "$_pid" ]
  expect "stale lock reclaimed + released" [ ! -e "$RT/lock" ]
  expect "stale lock noted in trace" grep -q "sign:stale-lock" "$OUT/debug.log"
  t_end
}

ts14() {
  t_begin "T-S14 token file 0644 / config 0644: exit 77, no fetch"
  chmod 644 "$HOME/.config/op-agent-sign/token.env"
  wsign
  expect "token file: exit 77" [ "$rc" = 77 ]
  expect "token file: message" errhas "mode 0600"
  expect "token file: no fetch" [ "$(ncalls)" = 0 ]
  reset
  chmod 644 "$HOME/.config/op-agent-sign/config"
  OP_AGENT_SIGN_FALLBACK=$FAKE_FB
  wsign
  expect "config: exit 77" [ "$rc" = 77 ]
  expect "config: no fetch" [ "$(ncalls)" = 0 ]
  expect "config: no fallback on 77" [ "$(nfb)" = 0 ]
  t_end
}

ts15() {
  t_begin "T-S15 verify path: no config read, no fetch, no sign steps"
  wsign
  expect "sign rc 0" [ "$rc" = 0 ]
  : >"$FAKE_OP_DIR/op.calls"
  _n0=$(wc -l <"$OUT/debug.log" | tr -d ' ')
  : >"$OUT/poison"
  chmod 644 "$OUT/poison"
  export OP_AGENT_SIGN_CONFIG=$OUT/poison
  printf 'OP_AGENT_SIGN_TTL=notanumber\n' >"$OUT/poison"
  "$KG" -Y find-principals -f "$ALLOWED" -s "$TMPDIR/buf.sig" >/dev/null 2>&1 # sanity: stock tool works
  _r1=0 _r2=0 _r3=0
  "$BIN" -Y find-principals -f "$ALLOWED" -s "$TMPDIR/buf.sig" >"$OUT/fp.out" 2>/dev/null || _r1=$?
  "$BIN" -Y verify -f "$ALLOWED" -I "$PRINCIPAL" -n git -s "$TMPDIR/buf.sig" <"$TMPDIR/buf" >/dev/null 2>&1 || _r2=$?
  "$BIN" -Y check-novalidate -n git -s "$TMPDIR/buf.sig" <"$TMPDIR/buf" >/dev/null 2>&1 || _r3=$?
  unset OP_AGENT_SIGN_CONFIG
  expect "find-principals rc 0" [ "$_r1" = 0 ]
  expect "find-principals prints the principal" grep -q "$PRINCIPAL" "$OUT/fp.out"
  expect "verify rc 0" [ "$_r2" = 0 ]
  expect "check-novalidate rc 0" [ "$_r3" = 0 ]
  expect "no fake op calls" [ "$(ncalls)" = 0 ]
  tail -n +$((_n0 + 1)) "$OUT/debug.log" >"$OUT/debug.new"
  expect "trace has 3 passthrough lines" [ "$(grep -c 'verify:passthrough' "$OUT/debug.new")" = 3 ]
  expect "trace has no sign steps" absent grep -q 'sign:' "$OUT/debug.new"
  t_end
}

# Search for the fake token or the throwaway key body (two lines) in the given dirs/files.
leaks_in() { grep -rlaF -e "$FAKE_TOKEN" -e "$KB2" -e "$KB3" "$@" 2>/dev/null; }

ts09() {
  t_begin "T-S9 leak scan: token and key body absent from output, trace, runtime dir, TMPDIR, git objects"
  # Extra traffic through success and failure paths first, with the debug trace on.
  for _mode in ok crlf wrongkey 429 401 empty; do reset; FAKE_OP_MODE=$_mode; wsign; done
  reset
  mkrepo r9
  gcommit r9
  expect "final commit is G" head_is_G r9
  expect "stdout+stderr+trace captured" [ -s "$OUT/debug.log" ]
  # Positive control: the scanner must see a planted token, otherwise a clean result means nothing.
  printf '%s\n' "$FAKE_TOKEN" >"$TMPDIR/.control"
  expect "scanner control detects planted token" [ -n "$(leaks_in "$TMPDIR")" ]
  rm -f "$TMPDIR/.control"
  _hits=$(leaks_in "$OUT" "$RT" "$TMPDIR")
  expect "no hits in stdout/stderr/trace/runtime dir/TMPDIR${_hits:+ ($_hits)}" [ -z "$_hits" ]
  for _r in "$REPOS"/*; do
    [ -d "$_r/.git" ] || continue
    _raw=$(leaks_in "$_r/.git")
    _dump=$(git -C "$_r" cat-file --batch-all-objects --batch 2>/dev/null | grep -aF -e "$FAKE_TOKEN" -e "$KB2" -e "$KB3")
    expect "no hits in $(basename "$_r")/.git" [ -z "$_raw$_dump" ]
  done
  t_end
}

ts16() {
  t_begin "T-S16 shellcheck -s sh, sh -n, hygiene greps"
  expect "sh -n" sh -n "$BIN"
  _sc=$(command -v shellcheck || { [ -x /opt/homebrew/bin/shellcheck ] && echo /opt/homebrew/bin/shellcheck; })
  if [ -n "$_sc" ]; then expect "shellcheck -s sh" "$_sc" -s sh "$BIN"; else echo "    note: shellcheck not installed here; only sh -n checked"; fi
  _lines=$(wc -l <"$BIN" | tr -d ' ')
  echo "    wrapper: $_lines lines"
  expect "wrapper <= 700 lines (R3)" [ "$_lines" -le 700 ]
  _mod=$(cd "$HERE/.." && pwd -P)
  # Patterns are split so this file does not match itself.
  _bad='exp''edia|\beg\b|ops_[A-Za-z0-9]|getfat''day|1password''\.com'
  expect "no employer/account strings in the module (allowed_signers holds the owner's public principal)" [ -z "$(grep -riE --exclude=allowed_signers "$_bad" "$_mod" 2>/dev/null)" ]
  expect "no scanner-flagged literals in the module" [ -z "$(grep -rniE -- '-----BEG''IN.*PRIVATE KEY-----|(pass''word|passwd|pwd)[[:space:]]*[:=]|bear''er[[:space:]]+[A-Za-z0-9_.~+/=-]{20,}' "$_mod" 2>/dev/null)" ]
  t_end
}
