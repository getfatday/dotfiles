# B5 cases: T-A1..T-A7, the AGENT signing key (D1 = c): agents sign with their own key (vault Agent), injected as
# user.signingkey=key::<pub> through GIT_CONFIG_COUNT=3, while the global (human) user.signingkey is a different key.
# Sourced by run.sh after td.sh; uses its helpers (d_begin, tty_run, route_on, doc, chk, ...). Throwaway keys only:
# $VAULT/key.pub is "the agent key", $VAULT/other.pub plays the human key.
TA_CASES="ta01 ta02 ta03 ta04 ta05 ta06 ta07"

OTHERLINE=$(cut -d' ' -f1,2 "$VAULT/other.pub")
fp_of() { "$KG" -lf "$1" | awk 'NR==1{print $2}'; }
# ta_boot [extra bootstrap args]: bootstrap the way SETUP will (item title, vault Agent), output in b.out, status in brc.
ta_boot() { FAKE_OP_TOKEN=ta-token tty_run "$BIN" bootstrap --token-ref "op://fakevault/faketokenitem/credential" --key-item "Agent signing key" --vault Agent --yes "$@"; }
ta_hermes() { rm -rf "$HOME/.hermes"; mkdir -p "$HOME/.hermes"; chmod 700 "$HOME/.hermes"; }
# ta_want VALUE2: the COUNT=3 block our bootstrap writes, on stdout.
ta_want() {
  printf 'GIT_CONFIG_COUNT=3\nGIT_CONFIG_KEY_0=gpg.ssh.program\nGIT_CONFIG_VALUE_0=%s/.local/bin/op-agent-sign\nGIT_CONFIG_KEY_1=gpg.ssh.allowedSignersFile\nGIT_CONFIG_VALUE_1=%s/.config/op-agent-sign/allowed_signers\nGIT_CONFIG_KEY_2=user.signingkey\nGIT_CONFIG_VALUE_2=key::%s\n' "$HOME" "$HOME" "$1"
}
# ta_old2: a previous (COUNT=2) block of ours, with stale paths, on stdout.
ta_old2() { printf 'GIT_CONFIG_COUNT=2\nGIT_CONFIG_KEY_0=gpg.ssh.program\nGIT_CONFIG_VALUE_0=/old/op-agent-sign\nGIT_CONFIG_KEY_1=gpg.ssh.allowedSignersFile\nGIT_CONFIG_VALUE_1=/old/allowed_signers\n'; }

ta01() {
  d_begin "T-A1 bootstrap reads the item's public key (CRs stripped) and writes GIT_CONFIG_COUNT=3 with the agent key"
  rm -f "$HOME/.config/op-agent-sign/config"; ta_hermes
  printf 'HERMES_FOO=1\n' >"$HOME/.hermes/.env"; chmod 600 "$HOME/.hermes/.env"
  { cat "$HOME/.hermes/.env"; ta_want "$PUBLINE"; } >"$OUT/a1.want"
  FAKE_OP_PUB_MODE=crlf ta_boot
  expect "bootstrap exit 0" [ "$brc" = 0 ]
  expect ".env = original + COUNT=3 block with key::<agent pub>" cmp "$HOME/.hermes/.env" "$OUT/a1.want"
  expect ".env mode 0600" [ "$(fmode "$HOME/.hermes/.env")" = -rw------- ]
  expect "agent_pub step true" grep -q '"step":"agent_pub","ok":true' "$OUT/b.out"
  expect "public key read from the item's public_key field (ref built from the resolved IDs)" grep -qx 'op://fakevaultid0123456789/fakeitemid0123456789/public_key' "$FAKE_OP_DIR/op.pubreads"
  expect "no key body in the transcript" absent grep -qF "$KB2" "$OUT/b.out"
  ta_boot
  expect "rerun is idempotent" cmp "$HOME/.hermes/.env" "$OUT/a1.want"
  # --agent-pub overrides the item read (the item is not consulted: its public_key is broken here)
  ta_want "$PUBLINE" >"$OUT/a1.only"
  ta_hermes
  FAKE_OP_PUB_MODE=bad ta_boot --agent-pub "key::$PUBLINE"
  expect "--agent-pub key::<pub>: exit 0" [ "$brc" = 0 ]
  expect "--agent-pub key::<pub>: block written" cmp "$HOME/.hermes/.env" "$OUT/a1.only"
  ta_hermes
  FAKE_OP_PUB_MODE=bad ta_boot --agent-pub "$PUBLINE agent comment"
  expect "--agent-pub <pub> (bare, with comment): exit 0" [ "$brc" = 0 ]
  expect "--agent-pub bare: comment dropped, block written" cmp "$HOME/.hermes/.env" "$OUT/a1.only"
  d_end
}

ta02() {
  d_begin "T-A2 bootstrap upgrades its own COUNT=2 block in place to COUNT=3; a rotated key replaces VALUE_2 in place"
  ta_hermes
  { printf 'HERMES_FOO=1\n# keep me\n'; ta_old2; printf 'LAST=end\n'; } >"$HOME/.hermes/.env"; chmod 600 "$HOME/.hermes/.env"
  { printf 'HERMES_FOO=1\n# keep me\n'; ta_want "$PUBLINE" | sed -n 1,5p; printf 'LAST=end\n'; ta_want "$PUBLINE" | sed -n 6,7p; } >"$OUT/a2.want"
  ta_boot
  expect "upgrade: exit 0" [ "$brc" = 0 ]
  expect "upgrade: COUNT=3, old lines replaced in place, KEY_2/VALUE_2 added, other lines intact" cmp "$HOME/.hermes/.env" "$OUT/a2.want"
  expect "upgrade: reported as written" grep -q '"step":"hermes_git_env","ok":true' "$OUT/b.out"
  ta_boot
  expect "upgrade: second run is a no-op" cmp "$HOME/.hermes/.env" "$OUT/a2.want"
  # rotation: a new item (other key) in Agent -> re-bootstrap -> only VALUE_2 changes
  sed "s#^GIT_CONFIG_VALUE_2=.*#GIT_CONFIG_VALUE_2=key::$OTHERLINE#" "$OUT/a2.want" >"$OUT/a2.rot"
  FAKE_OP_KEY=$VAULT/other FAKE_OP_PUB=$VAULT/other.pub ta_boot
  expect "rotation: exit 0 (service account reads the new key)" [ "$brc" = 0 ]
  expect "rotation: only VALUE_2 changed" cmp "$HOME/.hermes/.env" "$OUT/a2.rot"
  d_end
}

ta03() {
  d_begin "T-A3 match: true against the AGENT key while the global user.signingkey is a different key"
  printf '[user]\n\tsigningkey = key::%s\n' "$OTHERLINE" >"$HOME/.gitconfig-human"
  ta_hermes
  GIT_CONFIG_GLOBAL=$HOME/.gitconfig-human ta_boot
  expect "bootstrap exit 0 although global user.signingkey is the other key" [ "$brc" = 0 ]
  expect "bootstrap validate: match: true" grep -q '"step":"validate","ok":true,"detail":"match: true"' "$OUT/b.out"
  expect "global key really differs" [ "$(GIT_CONFIG_GLOBAL=$HOME/.gitconfig-human git config --global user.signingkey)" = "key::$OTHERLINE" ]
  # doctor: effective = agent (env), global = human
  d_prime
  GIT_CONFIG_GLOBAL=$HOME/.gitconfig-human OP_AGENT_SIGN_FALLBACK=$FAKE_FB doc --json
  expect "doctor exit 0" [ "$drc" = 0 ]
  expect "key_reachable match: true (agent key)" grep -q '"check":"key_reachable","ok":true,"detail":"match: true"' "$OUT/d.out"
  expect "signing_key shows the agent fingerprint" grep -q "\"check\":\"signing_key\".*effective (agent): $(fp_of "$PUBFILE")" "$OUT/d.out"
  expect "signing_key shows the human fingerprint" grep -q "global (human): $(fp_of "$VAULT/other.pub")" "$OUT/d.out"
  expect "agent_key_distinct true (informational)" grep -q '"check":"agent_key_distinct","ok":true.*"info":true' "$OUT/d.out"
  expect "fallback: unavailable for agent key (informational, not a failure)" grep -q '"check":"fallback","ok":true,"detail":"unavailable for agent key.*"info":true' "$OUT/d.out"
  # same key in both places: not distinct, fallback line goes back to the plain message
  printf '[user]\n\tsigningkey = key::%s\n' "$PUBLINE" >"$HOME/.gitconfig-same"
  GIT_CONFIG_GLOBAL=$HOME/.gitconfig-same OP_AGENT_SIGN_FALLBACK=$FAKE_FB doc --json
  expect "same key: agent_key_distinct false" grep -q '"check":"agent_key_distinct","ok":false.*"info":true' "$OUT/d.out"
  expect "same key: exit still 0" [ "$drc" = 0 ]
  expect "same key: fallback present" grep -q '"check":"fallback","ok":true,"detail":"desktop-app signer present"' "$OUT/d.out"
  rm -f "$HOME/.gitconfig-human" "$HOME/.gitconfig-same"
  d_end
}

ta04() {
  d_begin "T-A4 signed commit with the agent key from env while global user.signingkey is another key: %G? = G, agent fingerprint"
  printf '[user]\n\tsigningkey = key::%s\n' "$OTHERLINE" >"$HOME/.gitconfig-human"
  _d=$REPOS/a4; mkdir -p "$_d"; git -C "$_d" init -q
  git -C "$_d" config user.name tester; git -C "$_d" config user.email "$PRINCIPAL"
  git -C "$_d" config gpg.format ssh; git -C "$_d" config commit.gpgsign true
  route_on
  GIT_CONFIG_GLOBAL=$HOME/.gitconfig-human git -C "$_d" commit -q --allow-empty -m a4 >"$OUT/a4.out" 2>"$OUT/a4.err" </dev/null
  expect "commit succeeds (signing key and program come only from the env)" [ "$?" = 0 ]
  _g=$(GIT_CONFIG_GLOBAL=$HOME/.gitconfig-human git -C "$_d" log -1 --format='%G? %GK')
  expect "%G? is G" [ "${_g%% *}" = G ]
  expect "signed by the agent fingerprint" [ "${_g#* }" = "$(fp_of "$PUBFILE")" ]
  expect "not signed by the human key" [ "${_g#* }" != "$(fp_of "$VAULT/other.pub")" ]
  expect "verify-commit OK" sh -c 'GIT_CONFIG_GLOBAL=$1 git -C "$2" verify-commit HEAD >/dev/null 2>&1' sh "$HOME/.gitconfig-human" "$_d"
  expect "the human key was never fetched: one fake-op read for the agent key" [ "$(ncalls)" = 1 ]
  route_off; rm -f "$HOME/.gitconfig-human"
  d_end
}

ta05() {
  d_begin "T-A5 placeholder key::REPLACE_WITH_AGENT_PUBLIC_KEY makes doctor and setup --check FAIL with a next step"
  _cj=$HOME/.claude/settings.json; mkdir -p "$HOME/.claude"
  "$BIN" setup >/dev/null 2>&1 </dev/null
  d_prime
  doc --json
  expect "no settings.json: claude_env true, doctor exit 0" sh -c "grep -q '\"check\":\"claude_env\",\"ok\":true' \"$OUT/d.out\" && [ $drc = 0 ]"
  printf '{\n  "env": {\n    "GIT_CONFIG_COUNT": "3",\n    "GIT_CONFIG_KEY_2": "user.signingkey",\n    "GIT_CONFIG_VALUE_2": "key::REPLACE_WITH_AGENT_PUBLIC_KEY"\n  }\n}\n' >"$_cj"
  doc --json
  expect "placeholder in settings: doctor exit 1" [ "$drc" = 1 ]
  expect "placeholder in settings: claude_env false" chk claude_env false
  expect "placeholder: names the next step" grep -q 'claude_env.*"fix":"put the agent public key into GIT_CONFIG_VALUE_2' "$OUT/d.out"
  "$BIN" setup --check >"$OUT/d.out" 2>"$OUT/d.err" </dev/null; drc=$?
  expect "placeholder: setup --check exit 1" [ "$drc" = 1 ]
  expect "placeholder: setup --check claude_env false" grep -q '"step":"claude_env","ok":false' "$OUT/d.out"
  sed "s#REPLACE_WITH_AGENT_PUBLIC_KEY#$PUBLINE#" "$_cj" >"$_cj.new" && mv "$_cj.new" "$_cj"
  doc --json
  expect "placeholder replaced: claude_env true, doctor exit 0" sh -c "grep -q '\"check\":\"claude_env\",\"ok\":true' \"$OUT/d.out\" && [ $drc = 0 ]"
  "$BIN" setup --check >"$OUT/d.out" 2>"$OUT/d.err" </dev/null; drc=$?
  expect "placeholder replaced: setup --check exit 0" [ "$drc" = 0 ]
  # the effective key itself being the placeholder is caught even without a settings file
  rm -rf "$HOME/.claude"; route_on; GIT_CONFIG_VALUE_2=key::REPLACE_WITH_AGENT_PUBLIC_KEY; export GIT_CONFIG_VALUE_2
  ROUTED=0 doc --json
  expect "effective user.signingkey is the placeholder: claude_env false" chk claude_env false
  d_end
}

ta06() {
  d_begin "T-A6 foreign GIT_CONFIG_* lines (any shape that is not ours) are never merged or overwritten"
  ta_hermes
  for _shape in 1 2 3 4; do
    case $_shape in
      1) printf 'GIT_CONFIG_COUNT=3\nGIT_CONFIG_KEY_0=gpg.ssh.program\nGIT_CONFIG_VALUE_0=x\nGIT_CONFIG_KEY_1=gpg.ssh.allowedSignersFile\nGIT_CONFIG_VALUE_1=y\nGIT_CONFIG_KEY_2=core.foo\nGIT_CONFIG_VALUE_2=1\n' ;;
      2) printf 'GIT_CONFIG_COUNT=2\nGIT_CONFIG_KEY_0=core.foo\nGIT_CONFIG_VALUE_0=1\nGIT_CONFIG_KEY_1=gpg.ssh.allowedSignersFile\nGIT_CONFIG_VALUE_1=y\n' ;;
      3) printf 'GIT_CONFIG_COUNT=3\nGIT_CONFIG_KEY_0=core.foo\nGIT_CONFIG_VALUE_0=1\nGIT_CONFIG_KEY_1=gpg.ssh.allowedSignersFile\nGIT_CONFIG_VALUE_1=y\nGIT_CONFIG_KEY_2=user.signingkey\nGIT_CONFIG_VALUE_2=z\n' ;;
      4) printf 'GIT_CONFIG_COUNT=1\nGIT_CONFIG_KEY_0=user.signingkey\nGIT_CONFIG_VALUE_0=key::%s\n' "$OTHERLINE" ;;
    esac >"$HOME/.hermes/.env"
    chmod 600 "$HOME/.hermes/.env"; cp "$HOME/.hermes/.env" "$OUT/a6.orig"
    ta_boot
    expect "shape $_shape: .env untouched" cmp "$HOME/.hermes/.env" "$OUT/a6.orig"
    expect "shape $_shape: reported as foreign (hermes_git_env false)" grep -q '"step":"hermes_git_env","ok":false' "$OUT/b.out"
  done
  d_end
}

ta07() {
  d_begin "T-A7 bootstrap exits 69 unless the public key is a single ssh-ed25519 line; nothing is written to Hermes"
  ta_hermes
  for _m in bad multi rsa empty; do
    FAKE_OP_PUB_MODE=$_m ta_boot
    expect "public_key $_m: exit 69" [ "$brc" = 69 ]
    expect "public_key $_m: agent_pub false" grep -q '"step":"agent_pub","ok":false' "$OUT/b.out"
    expect "public_key $_m: no .env written" [ ! -e "$HOME/.hermes/.env" ]
  done
  ta_boot --agent-pub "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7"
  expect "--agent-pub with a non-ed25519 key: exit 69" [ "$brc" = 69 ]
  ta_boot --agent-pub "$PUBLINE
$PUBLINE"
  expect "--agent-pub with two lines: exit 69" [ "$brc" = 69 ]
  ta_boot --agent-pub "$OTHERLINE"
  expect "--agent-pub of a key the service account cannot read: validate false, exit 1" [ "$brc" = 1 ]
  expect "that mismatch is reported as match: false" grep -q '"step":"validate","ok":false,"detail":"match: false' "$OUT/b.out"
  d_end
}
