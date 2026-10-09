---
name: op-agent-sign
description: Use before any git commit to sign it unattended. Make SIGNED git commits with the op-agent-sign wrapper, which fetches the SSH signing key from 1Password through a service account into a private in-memory ssh-agent. Applies to kanban workers, cron jobs and delegated children on macOS, and whenever a commit fails with `op-agent-sign:` or `failed to write commit object`. Covers the preflight check, the commit command, verification, exit codes 64/69/70/72/75/77 with the matching kanban action, and the secret-handling rules.
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [git, signing, 1password, security]
    related_skills: [official/security/1password]
---

# op-agent-sign: unattended signed commits

`op-agent-sign` is a `gpg.ssh.program` wrapper installed at `~/.local/bin/op-agent-sign`. When git asks
for a signature it reads the signing key with a 1Password service account (`op read`), pipes it into a
private `ssh-agent` (memory only, one-hour TTL) and lets `ssh-keygen` sign. No key file, no Keychain,
no unlocked 1Password app. Verification (`git verify-commit`, `git log --show-signature`) makes no
network call and uses no token.

Agents sign with their own **Agent signing key** (an Ed25519 key in the 1Password vault Agent, registered on
GitHub as a signing-only key), not with the user's personal key. Git gets it from the environment as
`user.signingkey=key::<agent public key>` (`GIT_CONFIG_COUNT=3`, section 2), so the global `user.signingkey`
is ignored for your commits. The personal key's fallback signer cannot sign with the agent key: if the service
account path fails, the commit fails closed.

## 1. When to use

- Before every `git commit` you run as a worker, cron job or delegate child.
- When a commit fails with `error: op-agent-sign: ...` followed by `fatal: failed to write commit object`.
- When `git log -1 --format=%G?` prints `N`, `B` or `E` for a commit you just made.

Commits must be signed. Do not turn signing off to get past an error: see section 6.

## 2. Preflight

```
op-agent-sign doctor --offline
```

Offline means no `op` call and no quota use. Read the `git_routing` line: `routed: true` means git already
uses the wrapper (the seven `GIT_CONFIG_*` lines, `GIT_CONFIG_COUNT=3`, in `~/.hermes/.env`: program,
allowed signers and `user.signingkey=key::<agent public key>`), `routed: false` means it does not. The
`signing_key` line shows the agent and the personal key fingerprints; `agent_key_distinct: true` is expected.
Add `--json` for one JSON object per line (`check`, `ok`, `detail`, optional `fix`). The exit code is 0 only
if every non-informational check passed. If a check other than `git_routing` is `false`, read its `fix`
text and use the error table in section 5. `runtime_dir` failing is fixed by `op-agent-sign setup` (creates
0700 directories only; safe to repeat). Do not repair token or config files yourself.

## 3. Commit

Routed: plain signed commit.

```
git commit -S -m "message"
```

Not routed: pass the program and the agent key for this one command (`<agent public key>` is the value of
`GIT_CONFIG_VALUE_2`, `key::ssh-ed25519 AAAA...`; read that one variable by name with
`printenv GIT_CONFIG_VALUE_2`, never the whole file or environment). The absolute form works even when
`~/.local/bin` is not on this process's `PATH`.

```
git -c gpg.ssh.program="$HOME/.local/bin/op-agent-sign" \
    -c gpg.ssh.allowedSignersFile="$HOME/.config/op-agent-sign/allowed_signers" \
    -c user.signingkey="key::<agent public key>" \
    commit -S -m "message"
```

Never `-c commit.gpgsign=false`, never `--no-gpg-sign`, never `git config commit.gpgsign false`. If the
commit cannot be signed, stop and use section 5. The first commit of an hour fetches the key (a few
seconds); later ones hit the cached agent.

## 4. Verify

```
git verify-commit HEAD
git log -1 --format=%G?
```

The second command must print `G`. Both commands need the allowed-signers file: it comes from the
environment when routed; otherwise put `-c gpg.ssh.allowedSignersFile="$HOME/.config/op-agent-sign/allowed_signers"`
before `verify-commit` and before `log`. Without it `%G?` prints `N` even for a good signature. Any other letter (`N` unsigned, `E` cannot check, `B` bad) means the commit is
not done: do not push, fix the cause, and re-commit with `git commit -S --amend --no-edit` only if the
commit is your own and unpushed.

## 5. Errors

Failures print `error: op-agent-sign: <reason> (exit NN)` and git then aborts with
`fatal: failed to write commit object` (git's own exit status is 128; the wrapper's code is the `NN` in
the message). The text never contains the token or key. Exit codes (sysexits):

| Exit | Meaning | Action |
|---|---|---|
| 64 | Usage: bad option or argument | You called the wrapper wrongly. Fix the command; do not block. |
| 69 | Unavailable: no token, or the token was rejected | Bootstrap is needed and only the user can do it. `kanban_block kind=capability` with reason "op-agent-sign needs `op-agent-sign bootstrap` (section 7)". |
| 70 | Internal error (agent could not start, socket path too long, unexpected `op` failure) | Run `op-agent-sign doctor --offline` once and `op-agent-sign flush`, retry once. Still failing: `kanban_block kind=needs_input` with the doctor line that failed. |
| 72 | Key mismatch: the agent has no key matching the signing public key (`user.signingkey` from the env: wrong item, passphrase-protected key, empty read) | Configuration problem. `kanban_block kind=needs_input`. Do not retry. |
| 75 | Temporary: deadline exceeded, rate limited (429) or network | Wait the delay the message prints (about 60 s for a 429, otherwise a minute), retry once. Fails again: `kanban_block kind=transient`. |
| 77 | Permission: config dir/file or token file is group/other-accessible | Configuration problem. `kanban_block kind=needs_input`; say which path `doctor` flagged. Do not run `chmod` on token files yourself. |

When the service account path fails with 69 or 75 the wrapper may fall back to the 1Password app's signer
and prints `warning: service-account path unavailable`. That signer only holds keys of the user's Private
vault, so it cannot sign with the agent key (`doctor` reports `fallback: unavailable for agent key`): expect
the commit to fail closed, and block per the table. Mention any such warning in your handoff.

## 6. Rules

- Never print, `cat`, `head`, `grep` or otherwise display `~/.hermes/.op.env`, `~/.hermes/.env`,
  `~/.config/op-agent-sign/token.env` or `~/.config/op-agent-sign/config`.
- Never run bare `env`, `printenv` or `set` into a transcript, a commit message, a comment or a file;
  the environment can hold a token. Test one variable by name if you must.
- Never copy, export or write a private key anywhere. Never put the SSH private key into the Hermes
  `secrets.onepassword.env` mapping: that exports it into every process environment and caches it in
  `~/.hermes/cache/op_cache.json`.
- Never set `OP_SERVICE_ACCOUNT_TOKEN` yourself or pass it on a command line.
- The service-account token lives in `~/.hermes/.op.env` (Hermes's documented bootstrap file, see
  https://hermes-agent.nousresearch.com/docs/user-guide/secrets/onepassword). Treat the whole vault the
  service account can read as the blast radius.
- Never `-c commit.gpgsign=false` and never `--no-gpg-sign`.
- Never push, and do not edit global git config, to work around a signing problem.

## 7. Rotation

Token or agent-key rotation, revocation and the full bootstrap command are in the module README
(`~/src/dotfiles/modules/op-agent-sign/README.md`, sections "Agent signing key" and "Rotation and
revocation"). Key rotation is: new item in the vault Agent, new signing-only key on GitHub, append (never
delete) a line in `allowed_signers`, re-bootstrap, keep the old lines. The user rotates
the token with `op-agent-sign bootstrap`; `hermes secrets onepassword token` also works but writes to
`~/.hermes/.env`. Workers never run `bootstrap`: it needs a terminal and the 1Password app.
