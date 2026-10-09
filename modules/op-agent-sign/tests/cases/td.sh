# B2 cases: T-D1..T-D8 (doctor), T-SU1 (setup), T-B1 (bootstrap), T-G1..T-G3 (git env routing).
# Sourced by run.sh after ts.sh; uses its helpers (t_begin, expect, wsign, mkrepo, ...).
TD_CASES="td01 td02 td03 td04 td05 td06 td07 td08 tsu1 tb01 tg01 tg02 tg03"

route_on() {
  GIT_CONFIG_COUNT=3 GIT_CONFIG_KEY_0=gpg.ssh.program GIT_CONFIG_VALUE_0=$BIN
  GIT_CONFIG_KEY_1=gpg.ssh.allowedSignersFile GIT_CONFIG_VALUE_1=$ALLOWED
  GIT_CONFIG_KEY_2=user.signingkey GIT_CONFIG_VALUE_2="key::$PUBLINE"
  export GIT_CONFIG_COUNT GIT_CONFIG_KEY_0 GIT_CONFIG_VALUE_0 GIT_CONFIG_KEY_1 GIT_CONFIG_VALUE_1 GIT_CONFIG_KEY_2 GIT_CONFIG_VALUE_2
}
route_off() { unset GIT_CONFIG_COUNT GIT_CONFIG_KEY_0 GIT_CONFIG_VALUE_0 GIT_CONFIG_KEY_1 GIT_CONFIG_VALUE_1 GIT_CONFIG_KEY_2 GIT_CONFIG_VALUE_2; }
d_begin() { t_begin "$1"; route_off; rm -rf "$HOME/.hermes" "$HOME/.local/share/op-agent-sign"; }
d_end() { route_off; t_end; }
# doc [args]: run doctor (git routed unless ROUTED=0), output to d.out/d.err; accumulates for the leak scan.
doc() {
  [ "${ROUTED:-1}" = 0 ] || route_on
  "$BIN" doctor "$@" >"$OUT/d.out" 2>"$OUT/d.err" </dev/null
  drc=$?
  cat "$OUT/d.out" >>"$OUT/all.out"; cat "$OUT/d.err" >>"$OUT/all.err"
}
# chk NAME true|false: the --json line for check NAME has that ok value.
chk() { grep -q "\"check\":\"$1\",\"ok\":$2" "$OUT/d.out"; }
# Primed baseline: agent running with the key, config + token present, git routed.
d_prime() { mkdir -p "$RT" && chmod 700 "$RT"; wsign; }

td01() {
  d_begin "T-D1 doctor: healthy baseline passes (marks and --json); missing op flips op to failed"
  d_prime
  expect "primed sign rc 0" [ "$rc" = 0 ]
  doc
  expect "baseline exit 0" [ "$drc" = 0 ]
  expect "baseline prints check marks" grep -q "^✓ op " "$OUT/d.out"
  expect "baseline has no failed mark" absent grep -q "^✗" "$OUT/d.out"
  doc --json
  expect "json baseline exit 0" [ "$drc" = 0 ]
  expect "json summary ok" grep -q '"check":"summary","ok":true,"failed":0' "$OUT/d.out"
  OP_AGENT_SIGN_OP=/nonexistent/op doc --json
  expect "missing op: exit 1" [ "$drc" = 1 ]
  expect "missing op: op check false" chk op false
  expect "missing op: other checks unaffected (key_ref)" chk key_ref true
  d_end
}

td02() {
  d_begin "T-D2 doctor: bad modes (token file 0644, config 0644, runtime dir 0755) each flip their check"
  d_prime
  chmod 644 "$HOME/.config/op-agent-sign/token.env"
  doc --json
  expect "token 0644: exit 1" [ "$drc" = 1 ]
  expect "token 0644: token_file false" chk token_file false
  expect "token 0644: config still true" chk config true
  chmod 600 "$HOME/.config/op-agent-sign/token.env"
  chmod 644 "$HOME/.config/op-agent-sign/config"
  doc --json
  expect "config 0644: exit 1" [ "$drc" = 1 ]
  expect "config 0644: config false" chk config false
  chmod 600 "$HOME/.config/op-agent-sign/config"
  chmod 755 "$RT"
  doc --json
  expect "runtime 0755: runtime_dir false" chk runtime_dir false
  expect "doctor did not chmod it back" [ "$(ls -ld "$RT" | cut -c1-10)" = drwxr-xr-x ]
  chmod 700 "$RT"
  doc --json
  expect "all restored: exit 0" [ "$drc" = 0 ]
  d_end
}

td03() {
  d_begin "T-D3 doctor: git not routed to the wrapper -> git_routing false (routed: false)"
  d_prime
  ROUTED=0 doc --json
  expect "unrouted: exit 1" [ "$drc" = 1 ]
  expect "unrouted: git_routing false" chk git_routing false
  expect "unrouted: says routed: false" grep -q 'routed: false' "$OUT/d.out"
  doc --json
  expect "routed: git_routing true" chk git_routing true
  expect "routed: reports the origin" grep -q 'origin: command line' "$OUT/d.out"
  d_end
}

td04() {
  d_begin "T-D4 doctor: dead agent with a stale socket -> agent false; no agent at all is informational"
  d_prime
  _pid=$(cat "$RT/agent.pid")
  kill -9 "$_pid"; sleep 0.3
  doc --json
  expect "stale socket: exit 1" [ "$drc" = 1 ]
  expect "stale socket: agent false" chk agent false
  "$BIN" flush >/dev/null 2>&1
  doc --json
  expect "no agent, no socket: agent check ok (informational)" chk agent true
  expect "no agent: exit 0" [ "$drc" = 0 ]
  d_end
}

td05() {
  d_begin "T-D5 doctor: bad KEY_REF -> key_ref false; wrong key -> key_reachable false; bad token -> sa_auth false"
  d_prime
  printf 'OP_AGENT_SIGN_KEY_REF="op://not a ref"\n' >"$HOME/.config/op-agent-sign/config"
  doc --json
  expect "bad ref: exit 1" [ "$drc" = 1 ]
  expect "bad ref: key_ref false" chk key_ref false
  mk_config
  FAKE_OP_MODE=wrongkey doc --json
  expect "wrong key: key_reachable false" chk key_reachable false
  expect "wrong key: sa_auth still true" chk sa_auth true
  FAKE_OP_MODE=401 doc --json
  expect "401: sa_auth false" chk sa_auth false
  : >"$HOME/.config/op-agent-sign/token.env"
  doc --json
  expect "no token: token_file false" chk token_file false
  expect "no token: network checks skipped, not failed" chk sa_auth true
  d_end
}

td06() {
  d_begin "T-D6 doctor: missing allowed_signers -> allowed_signers false"
  d_prime
  mv "$ALLOWED" "$ALLOWED.off"
  doc --json
  expect "missing: exit 1" [ "$drc" = 1 ]
  expect "missing: allowed_signers false" chk allowed_signers false
  mv "$ALLOWED.off" "$ALLOWED"
  doc --json
  expect "restored: allowed_signers true" chk allowed_signers true
  d_end
}

td07() {
  d_begin "T-D7 doctor: --json is valid JSON lines, no values; --offline makes 0 fake-op calls"
  d_prime
  : >"$FAKE_OP_DIR/op.calls"
  doc --offline --json
  expect "offline exit 0" [ "$drc" = 0 ]
  expect "offline: 0 fake-op calls" [ "$(ncalls)" = 0 ]
  expect "offline: sa_auth skipped" grep -q '"check":"sa_auth","ok":true,"detail":"skipped (--offline)"' "$OUT/d.out"
  doc --json
  expect "online: made fake-op calls" [ "$(ncalls)" -gt 0 ]
  _n=$(wc -l <"$OUT/d.out" | tr -d ' ')
  expect "json: at least 10 lines" [ "$_n" -ge 10 ]
  if command -v jq >/dev/null 2>&1; then
    expect "every line parses as JSON (jq)" sh -c 'jq -e . "$1" >/dev/null' sh "$OUT/d.out"
  else
    expect "every line looks like a JSON object" sh -c '! grep -v "^{.*}$" "$1"' sh "$OUT/d.out"
  fi
  expect "no token value in doctor output" absent grep -qF "$FAKE_TOKEN" "$OUT/d.out"
  expect "no vault/item name in doctor output (masked to 4 chars)" absent grep -qE 'fakevault|fakeitem' "$OUT/d.out"
  expect "no key body in doctor output" absent grep -qF "$KB2" "$OUT/d.out"
  d_end
}

td08() {
  d_begin "T-D8 doctor --commit-test: signed throwaway commit verifies; failure flips commit_test"
  d_prime
  doc --commit-test --json
  expect "commit-test exit 0" [ "$drc" = 0 ]
  expect "commit_test true" chk commit_test true
  expect "throwaway repo removed" [ -z "$(ls "$RT" | grep '^ct\.')" ]
  FAKE_OP_MODE=wrongkey "$BIN" flush >/dev/null 2>&1
  FAKE_OP_MODE=wrongkey doc --commit-test --json
  expect "wrong key: commit_test false" chk commit_test false
  expect "wrong key: exit 1" [ "$drc" = 1 ]
  d_end
}

tsu1() {
  d_begin "T-SU1 setup: creates 0700 dirs, links the Hermes skill only if ~/.hermes exists, --check never mutates"
  rm -rf "$RT"
  "$BIN" setup --check >"$OUT/d.out" 2>"$OUT/d.err" </dev/null; drc=$?
  expect "--check with missing runtime dir: exit 1" [ "$drc" = 1 ]
  expect "--check created nothing" [ ! -d "$RT" ]
  "$BIN" setup >"$OUT/d.out" 2>"$OUT/d.err" </dev/null; drc=$?
  expect "setup exit 0 (no ~/.hermes, no skill files yet)" [ "$drc" = 0 ]
  expect "runtime dir created 0700" [ "$(ls -ld "$RT" | cut -c1-10)" = drwx------ ]
  expect "no Hermes: skill step informational" grep -q '"step":"hermes_skill","ok":true' "$OUT/d.out"
  expect "claude skill absence is informational" grep -q '"step":"claude_skill","ok":false.*"info":true' "$OUT/d.out"
  "$BIN" setup --check >"$OUT/d.out" 2>"$OUT/d.err" </dev/null; drc=$?
  expect "--check after setup: exit 0" [ "$drc" = 0 ]
  _src=$HOME/.local/share/op-agent-sign/hermes-skills/op-agent-sign
  mkdir -p "$HOME/.hermes" "$_src"; printf '# fake skill\n' >"$_src/SKILL.md"
  "$BIN" setup --check >"$OUT/d.out" 2>"$OUT/d.err" </dev/null; drc=$?
  expect "--check with an unlinked skill: exit 1" [ "$drc" = 1 ]
  expect "--check did not link" [ ! -e "$HOME/.hermes/skills/security/op-agent-sign" ]
  "$BIN" setup >"$OUT/d.out" 2>"$OUT/d.err" </dev/null; drc=$?
  expect "setup links: exit 0" [ "$drc" = 0 ]
  expect "link points at the skill source" [ "$(readlink "$HOME/.hermes/skills/security/op-agent-sign")" = "$_src" ]
  "$BIN" setup >"$OUT/d.out" 2>"$OUT/d.err" </dev/null; drc=$?
  expect "setup is idempotent" [ "$drc" = 0 ]
  rm -f "$HOME/.hermes/skills/security/op-agent-sign"; mkdir -p "$HOME/.hermes/skills/security/op-agent-sign"
  "$BIN" setup >"$OUT/d.out" 2>"$OUT/d.err" </dev/null; drc=$?
  expect "foreign directory at the link path: exit 1, left alone" [ "$drc" = 1 ] 
  expect "foreign directory untouched" [ -d "$HOME/.hermes/skills/security/op-agent-sign" ] 
  expect "foreign directory still not a link" [ ! -L "$HOME/.hermes/skills/security/op-agent-sign" ]
  "$BIN" setup --bogus >/dev/null 2>&1 </dev/null; drc=$?
  expect "unknown option: exit 64" [ "$drc" = 64 ]
  d_end
}

# --- T-B1 helpers ---
# tty_run CMD...: run under a pseudo-terminal (bootstrap needs one); stdout+stderr to b.out (CRs stripped).
tty_run() {
  script -q /dev/null "$@" >"$OUT/b.raw" 2>&1 </dev/null
  brc=$?
  tr -d '\r' <"$OUT/b.raw" >"$OUT/b.out"
  cat "$OUT/b.out" >>"$OUT/all.out"
}
fmode() { ls -l "$1" | cut -c1-10; }

tb01() {
  d_begin "T-B1 bootstrap (fake op, temp HOME): atomic 0600 token file; .env byte-preserving upsert; refusals"
  rm -f "$HOME/.config/op-agent-sign/config" "$HOME/.config/op-agent-sign/token.env"
  route_on
  _TF=$HOME/.config/op-agent-sign/token.env
  _REF="op://fakevault/faketokenitem/credential"
  # 1. dedicated file, created
  FAKE_OP_TOKEN=boot-token-one tty_run "$BIN" bootstrap --token-ref "$_REF" --key-item "fake key" --yes
  expect "bootstrap exit 0" [ "$brc" = 0 ]
  expect "token file created 0600" [ "$(fmode "$_TF")" = -rw------- ]
  expect "token file is exactly one NAME=VALUE line" [ "$(cat "$_TF")" = "OP_SERVICE_ACCOUNT_TOKEN=boot-token-one" ]
  expect "config written 0600" [ "$(fmode "$HOME/.config/op-agent-sign/config")" = -rw------- ]
  expect "config carries the key reference by IDs" grep -qx 'OP_AGENT_SIGN_KEY_REF="op://fakevaultid0123456789/fakeitemid0123456789/private_key?ssh-format=openssh"' "$HOME/.config/op-agent-sign/config"
  expect "default token file: no TOKEN_FILE line" absent grep -q TOKEN_FILE "$HOME/.config/op-agent-sign/config"
  expect "validation step reports match: true" grep -q '"step":"validate","ok":true,"detail":"match: true"' "$OUT/b.out"
  expect "no token value in output" absent grep -qF boot-token-one "$OUT/b.out"
  expect "no full vault/item IDs in output (masked)" absent grep -qE 'fakevaultid0123456789|fakeitemid0123456789' "$OUT/b.out"
  expect "nothing written outside the expected files (no .tmp left)" [ -z "$(ls -A "$HOME/.config/op-agent-sign" | grep '^\.tmp')" ]
  # 2. replace, atomically (new inode, new content)
  _ino=$(ls -i "$_TF" | awk '{print $1}')
  FAKE_OP_TOKEN=boot-token-two tty_run "$BIN" bootstrap --token-ref "$_REF" --yes
  expect "re-bootstrap exit 0" [ "$brc" = 0 ]
  expect "token replaced" [ "$(cat "$_TF")" = "OP_SERVICE_ACCOUNT_TOKEN=boot-token-two" ]
  expect "replaced via mv (new inode)" [ "$(ls -i "$_TF" | awk '{print $1}')" != "$_ino" ]
  expect "still 0600" [ "$(fmode "$_TF")" = -rw------- ]
  # 3. .env variant: every other line byte for byte
  _E=$HOME/envdir/.env; mkdir -p "$HOME/envdir"; chmod 700 "$HOME/envdir"
  printf '# header comment\n\nFOO=bar\n  INDENTED=1\nQUOTED="a b"  # trailing\n# OP_SERVICE_ACCOUNT_TOKEN=commented-out\nOP_SERVICE_ACCOUNT_TOKEN_OTHER=keep\nTAB=\tvalue\nUTF=caf\303\251 \342\234\223\nOP_SERVICE_ACCOUNT_TOKEN=old-token\nLAST=end\n' >"$_E"
  chmod 600 "$_E"; cp "$_E" "$OUT/env.orig"
  sed 's/^OP_SERVICE_ACCOUNT_TOKEN=.*/OP_SERVICE_ACCOUNT_TOKEN=boot-token-three/' "$OUT/env.orig" >"$OUT/env.want"
  FAKE_OP_TOKEN=boot-token-three tty_run "$BIN" bootstrap --token-ref "$_REF" --token-file "$_E" --yes
  expect ".env replace: exit 0" [ "$brc" = 0 ]
  expect ".env replace: byte-identical apart from the token line" cmp "$_E" "$OUT/env.want"
  expect ".env replace: mode 0600" [ "$(fmode "$_E")" = -rw------- ]
  expect "non-default token file recorded in config" grep -qx "OP_AGENT_SIGN_TOKEN_FILE=\"$_E\"" "$HOME/.config/op-agent-sign/config"
  # 4. .env variant: append when absent
  grep -v '^OP_SERVICE_ACCOUNT_TOKEN=' "$OUT/env.orig" >"$_E"; chmod 600 "$_E"
  cp "$_E" "$OUT/env.want"; printf 'OP_SERVICE_ACCOUNT_TOKEN=boot-token-four\n' >>"$OUT/env.want"
  FAKE_OP_TOKEN=boot-token-four tty_run "$BIN" bootstrap --token-ref "$_REF" --token-file "$_E" --yes
  expect ".env append: exit 0" [ "$brc" = 0 ]
  expect ".env append: original lines intact, token line appended" cmp "$_E" "$OUT/env.want"
  # 5. refusals
  _before=$(cat "$_TF")
  OP_SERVICE_ACCOUNT_TOKEN=already-set FAKE_OP_TOKEN=x tty_run "$BIN" bootstrap --token-ref "$_REF" --yes
  expect "token in env: refused (64)" [ "$brc" = 64 ]
  expect "token in env: file untouched" [ "$(cat "$_TF")" = "$_before" ]
  FAKE_OP_TOKEN=x "$BIN" bootstrap --token-ref "$_REF" --yes >"$OUT/b.out" 2>&1 </dev/null; brc=$?
  expect "no terminal: refused (64)" [ "$brc" = 64 ]
  expect "no terminal: file untouched" [ "$(cat "$_TF")" = "$_before" ]
  tty_run "$BIN" bootstrap --bogus
  expect "unknown option: 64" [ "$brc" = 64 ]
  FAKE_OP_TOKEN="two words" tty_run "$BIN" bootstrap --token-ref "$_REF" --yes
  expect "multi-word token: refused (69), file untouched" [ "$brc" = 69 ] 
  expect "multi-word token: file untouched" [ "$(cat "$_TF")" = "$_before" ]
  # 6. Hermes git env (step 6): written with absolute paths, other lines intact, opt-out honoured
  grep -v TOKEN_FILE "$HOME/.config/op-agent-sign/config" >"$OUT/cfg.new"; cat "$OUT/cfg.new" >"$HOME/.config/op-agent-sign/config"
  : >>"$OUT/all.out"; : >>"$OUT/all.err"
  mkdir -p "$HOME/.hermes"; chmod 700 "$HOME/.hermes"
  printf 'HERMES_FOO=1\n# keep me\nOTHER="x y"\n' >"$HOME/.hermes/.env"; chmod 600 "$HOME/.hermes/.env"
  cp "$HOME/.hermes/.env" "$OUT/hermes.orig"
  FAKE_OP_TOKEN=boot-token-five tty_run "$BIN" bootstrap --token-ref "$_REF" --yes --no-hermes-git-env
  expect "hermes: default token file is ~/.hermes/.op.env" [ "$(cat "$HOME/.hermes/.op.env")" = "OP_SERVICE_ACCOUNT_TOKEN=boot-token-five" ]
  expect "hermes: --no-hermes-git-env leaves .env untouched" cmp "$HOME/.hermes/.env" "$OUT/hermes.orig"
  FAKE_OP_TOKEN=boot-token-six tty_run "$BIN" bootstrap --token-ref "$_REF" --yes
  expect "hermes: bootstrap exit 0" [ "$brc" = 0 ]
  { cat "$OUT/hermes.orig"
    printf 'GIT_CONFIG_COUNT=3\nGIT_CONFIG_KEY_0=gpg.ssh.program\nGIT_CONFIG_VALUE_0=%s/.local/bin/op-agent-sign\nGIT_CONFIG_KEY_1=gpg.ssh.allowedSignersFile\nGIT_CONFIG_VALUE_1=%s/.config/op-agent-sign/allowed_signers\nGIT_CONFIG_KEY_2=user.signingkey\nGIT_CONFIG_VALUE_2=key::%s\n' "$HOME" "$HOME" "$PUBLINE"
  } >"$OUT/hermes.want"
  expect "hermes: .env = original + seven absolute GIT_CONFIG_* lines (COUNT=3, agent key)" cmp "$HOME/.hermes/.env" "$OUT/hermes.want"
  FAKE_OP_TOKEN=boot-token-seven tty_run "$BIN" bootstrap --token-ref "$_REF" --yes
  expect "hermes: rerun is idempotent for the GIT_CONFIG_* lines" cmp "$HOME/.hermes/.env" "$OUT/hermes.want"
  printf 'GIT_CONFIG_COUNT=1\nGIT_CONFIG_KEY_0=core.foo\nGIT_CONFIG_VALUE_0=1\n' >>"$HOME/.hermes/.env"
  cp "$HOME/.hermes/.env" "$OUT/hermes.other"
  FAKE_OP_TOKEN=boot-token-eight tty_run "$BIN" bootstrap --token-ref "$_REF" --yes
  expect "hermes: foreign GIT_CONFIG_* lines are never merged or overwritten" cmp "$HOME/.hermes/.env" "$OUT/hermes.other"
  expect "hermes: foreign lines reported" grep -q '"step":"hermes_git_env","ok":false' "$OUT/b.out"
  expect "no token value anywhere in the transcript" absent grep -qE 'boot-token-(one|two|three|four|five|six|seven|eight)' "$OUT/all.out" "$OUT/all.err"
  rm -rf "$HOME/.hermes" "$HOME/envdir"
  d_end
}

# --- T-G: git env routing facts (design section 6); results are recorded in the output ---
g_repo() { # name: repo without gpg.ssh.program/allowedSignersFile in its own config
  _d=$REPOS/$1; mkdir -p "$_d"; git -C "$_d" init -q
  git -C "$_d" config user.name tester; git -C "$_d" config user.email "$PRINCIPAL"
  git -C "$_d" config gpg.format ssh; git -C "$_d" config user.signingkey "key::$PUBLINE"
  git -C "$_d" config commit.gpgsign true
}
g_link() { mkdir -p "$HOME/.local/bin"; ln -sf "$BIN" "$HOME/.local/bin/op-agent-sign"; }

tg01() {
  d_begin "T-G1 GIT_CONFIG_COUNT env in a child shell: git reports origin 'command line' and the wrapper path"
  route_on
  _o=$(sh -c 'git config --show-origin gpg.ssh.program' 2>/dev/null)
  expect "origin is command line" [ "${_o%%	*}" = "command line:" ]
  expect "value is the wrapper path" [ "${_o#*	}" = "$BIN" ]
  echo "    T-G1 RESULT: $(printf '%s' "$_o" | tr '\t' ' ' | sed "s#$HOME#~#g")"
  d_end
}

tg02() {
  d_begin "T-G2 GIT_CONFIG_VALUE with a literal ~ : is ~ expanded for env-sourced gpg.ssh.program / allowedSignersFile?"
  g_link; g_repo g2a; g_repo g2b
  # (a) program given as ~/..., allowed signers absolute
  GIT_CONFIG_COUNT=2 GIT_CONFIG_KEY_0=gpg.ssh.program GIT_CONFIG_VALUE_0='~/.local/bin/op-agent-sign' \
    GIT_CONFIG_KEY_1=gpg.ssh.allowedSignersFile GIT_CONFIG_VALUE_1=$ALLOWED \
    git -C "$REPOS/g2a" commit -q --allow-empty -m g2a >"$OUT/g2a.out" 2>"$OUT/g2a.err" </dev/null; _ra=$?
  if [ "$_ra" = 0 ] && GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=gpg.ssh.allowedSignersFile GIT_CONFIG_VALUE_0=$ALLOWED git -C "$REPOS/g2a" verify-commit HEAD >/dev/null 2>&1; then _pe=true; else _pe=false; fi
  # (b) program absolute, allowed signers given as ~/... (verification reads it)
  GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=gpg.ssh.program GIT_CONFIG_VALUE_0=$BIN \
    git -C "$REPOS/g2b" commit -q --allow-empty -m g2b >"$OUT/g2b.out" 2>"$OUT/g2b.err" </dev/null
  GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=gpg.ssh.allowedSignersFile GIT_CONFIG_VALUE_0='~/.config/op-agent-sign/allowed_signers' \
    git -C "$REPOS/g2b" verify-commit HEAD >"$OUT/g2b.v" 2>&1 </dev/null; _rb=$?
  if [ "$_rb" = 0 ] && [ "$(GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=gpg.ssh.allowedSignersFile GIT_CONFIG_VALUE_0='~/.config/op-agent-sign/allowed_signers' git -C "$REPOS/g2b" log -1 --format=%G? 2>/dev/null)" = G ]; then _ae=true; else _ae=false; fi
  echo "    T-G2 RESULT: program '~/.local/bin/op-agent-sign' from env -> commit rc=$_ra, expanded=$_pe"
  [ "$_pe" = true ] || echo "      git said: $(sed -n 1p "$OUT/g2a.err" | sed "s#$HOME#~#g")"
  echo "    T-G2 RESULT: allowedSignersFile '~/.config/op-agent-sign/allowed_signers' from env -> verify rc=$_rb, expanded=$_ae"
  [ "$_ae" = true ] || echo "      git said: $(sed -n 1p "$OUT/g2b.v" | sed "s#$HOME#~#g")"
  printf 'tg2_program_tilde_expanded=%s\ntg2_allowedsigners_tilde_expanded=%s\n' "$_pe" "$_ae" >"$OUT/tg2.result"
  cat "$OUT/tg2.result" >>"$OUT/all.out"
  expect "experiment ran (result recorded)" [ -s "$OUT/tg2.result" ]
  d_end
}

tg03() {
  d_begin "T-G3 GIT_CONFIG_VALUE=op-agent-sign (bare name) with ~/.local/bin on PATH: git finds the wrapper via PATH"
  g_link; g_repo g3
  PATH=$HOME/.local/bin:$PATH GIT_CONFIG_COUNT=2 GIT_CONFIG_KEY_0=gpg.ssh.program GIT_CONFIG_VALUE_0=op-agent-sign \
    GIT_CONFIG_KEY_1=gpg.ssh.allowedSignersFile GIT_CONFIG_VALUE_1=$ALLOWED \
    git -C "$REPOS/g3" commit -q --allow-empty -m g3 >"$OUT/g3.out" 2>"$OUT/g3.err" </dev/null; _r=$?
  if [ "$_r" = 0 ] && [ "$(git -C "$REPOS/g3" -c gpg.ssh.allowedSignersFile="$ALLOWED" log -1 --format=%G? 2>/dev/null)" = G ]; then _b=true; else _b=false; fi
  echo "    T-G3 RESULT: bare 'op-agent-sign' resolved via PATH -> commit rc=$_r, signed G=$_b"
  [ "$_b" = true ] || echo "      git said: $(sed -n 1p "$OUT/g3.err" | sed "s#$HOME#~#g")"
  printf 'tg3_bare_name_resolved=%s\n' "$_b" >"$OUT/tg3.result"
  cat "$OUT/tg3.result" >>"$OUT/all.out"
  expect "bare name resolved and commit signed" [ "$_b" = true ]
  d_end
}
