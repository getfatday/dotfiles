---
name: op-agent-sign
description: Sign git commits unattended via the op-agent-sign wrapper (1Password service account); use before committing or when signing fails
allowed-tools: Bash(git *) Bash(op-agent-sign *)
user-invocable: true
---

# op-agent-sign: unattended signed commits (Claude Code)

`op-agent-sign` is a `gpg.ssh.program` wrapper at `~/.local/bin/op-agent-sign`. When git asks for a
signature it reads the signing key with a 1Password service account (`op read`), pipes it into a private
in-memory `ssh-agent` (one-hour TTL) and lets `ssh-keygen` sign. No key file, no Keychain, no unlocked
1Password app. Verification makes no network call and uses no token.

Invoked as `/op-agent-sign`, run the preflight in section 2 and report the result. Otherwise follow the
sections in order whenever you are about to commit or a commit fails to sign.

## 1. When to use

- Before any `git commit` you run with the Bash tool.
- When a commit fails with `error: op-agent-sign: ...` followed by `fatal: failed to write commit object`.
- When `git log -1 --format=%G?` prints anything but `G` for a commit you just made.

Commits must be signed. Never switch signing off to get past an error (section 6).

## 2. Preflight

Run with the Bash tool:

```
op-agent-sign doctor --offline
```

No `op` call, no quota use. Read the `git_routing` line: `routed: true` means git already uses the wrapper
(the `env` block in `~/.claude/settings.json` sets `GIT_CONFIG_COUNT=2` with `gpg.ssh.program=op-agent-sign`
and `gpg.ssh.allowedSignersFile=~/.config/op-agent-sign/allowed_signers`); `routed: false` means it does
not (older session, `~/.local/bin` not on `PATH`, or settings not applied: tell the user to restart Claude
Code). The exit code is 0 only if every non-informational check passed; for another failing check, quote its
`fix` text to the user and use section 5. `runtime_dir` failing is fixed by `op-agent-sign setup` (creates 0700
directories only; safe to repeat). Do not repair token or config files yourself.

## 3. Commit

Routed:

```
git commit -S -m "message"
```

Not routed (one command only; the absolute path works even when `~/.local/bin` is not on `PATH`):

```
git -c gpg.ssh.program="$HOME/.local/bin/op-agent-sign" \
    -c gpg.ssh.allowedSignersFile="$HOME/.config/op-agent-sign/allowed_signers" \
    commit -S -m "message"
```

Never `-c commit.gpgsign=false`, never `--no-gpg-sign`, never `git config commit.gpgsign false`. The first
commit in an hour fetches the key (a few seconds); later ones use the cached agent.

## 4. Verify

```
git verify-commit HEAD
git log -1 --format=%G?
```

The second command must print `G`. When not routed, put
`-c gpg.ssh.allowedSignersFile="$HOME/.config/op-agent-sign/allowed_signers"` before `verify-commit` and
before `log`; without it `%G?` prints `N` even for a good signature. Any other letter (`N` unsigned, `E` cannot check, `B` bad) means the commit is not done: do not push; tell
the user, fix the cause, then re-sign your own unpushed commit with `git commit -S --amend --no-edit`.

## 5. Errors

Failures print `error: op-agent-sign: <reason> (exit NN)` and git then aborts with
`fatal: failed to write commit object` (git's own status is 128; the wrapper's code is the `NN` in the
message). The text never contains the token or key.

| Exit | Meaning | What to do and tell the user |
|---|---|---|
| 64 | Usage: bad option | You called the wrapper wrongly. Fix the command. |
| 69 | No token, or token rejected | Stop. Tell the user: "the signing service account is not set up on this machine or its token was rejected; run `op-agent-sign bootstrap` in a terminal (see the module README), then `op-agent-sign doctor`." You cannot do this yourself. |
| 70 | Internal error (agent did not start, socket path too long, unexpected `op` failure) | Run `op-agent-sign flush`, retry once. Still failing: show the user the failing `doctor --offline` line. |
| 72 | Key mismatch: no key matching `user.signingkey` (wrong item, passphrase-protected key, empty read) | Configuration problem; do not retry. Tell the user which `doctor` check failed. |
| 75 | Temporary: deadline, rate limit (429), network | Wait the delay printed (about 60 s for a 429, otherwise a minute), retry once. Still failing: stop and tell the user it is temporary. |
| 77 | Permissions: config dir/file or token file is group/other-accessible | Stop. Tell the user the path `doctor` flagged and that it needs mode 0600 (directories 0700). Do not `chmod` token files yourself. |

When the service-account path fails with 69 or 75 the wrapper may fall back to the 1Password app's signer
and print `warning: service-account path unavailable`; mention that warning in your summary.

## 6. Rules

- Never print, `cat`, `head` or `grep` `~/.hermes/.op.env`, `~/.hermes/.env`,
  `~/.config/op-agent-sign/token.env` or `~/.config/op-agent-sign/config`. Do not read them with the Read tool.
- Never run bare `env`, `printenv` or `set` into the conversation, a commit message or a file; the
  environment can hold a token. Test one variable by name if you must.
- Never copy, export or write a private key anywhere. Never put the SSH private key into the Hermes
  `secrets.onepassword.env` mapping: that exports it into every Hermes process and caches it in
  `~/.hermes/cache/op_cache.json`.
- Never set `OP_SERVICE_ACCOUNT_TOKEN` or pass it on a command line.
- The token lives in `~/.hermes/.op.env` (Hermes's documented bootstrap file, see
  https://hermes-agent.nousresearch.com/docs/user-guide/secrets/onepassword). The whole vault the service
  account can read is the blast radius.
- Never `-c commit.gpgsign=false`, never `--no-gpg-sign`. Do not edit global git config or push to work
  around a signing problem.

## 7. Rotation

Token and key rotation, revocation and the full bootstrap command are in the module README
(`~/src/dotfiles/modules/op-agent-sign/README.md`, "Rotation and revocation"). The user rotates the token
with `op-agent-sign bootstrap` (`hermes secrets onepassword token` also works but writes to
`~/.hermes/.env`). Never run `bootstrap` yourself: it needs a terminal and the 1Password app.
