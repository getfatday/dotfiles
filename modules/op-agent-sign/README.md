# op-agent-sign

Unattended, SIGNED git commits for agents (Hermes workers, Claude Code) on macOS. The SSH signing key
stays in 1Password. When git asks for a signature, `op-agent-sign` (a `gpg.ssh.program` wrapper) fetches
the key with a 1Password service account (`op read`) and loads it into a private, in-memory `ssh-agent`
with a time-to-live. Nothing needs the 1Password desktop app to be unlocked.

No secrets live in this module: no token, no key, no vault or item IDs, no account URL. Those are
machine-local (see "Config keys" and "Token file").

## Install

```
dotm sync                         # stows the wrapper, allowed_signers, config.example
op-agent-sign setup               # 0700 dirs; links the Hermes skill when ~/.hermes exists
op-agent-sign bootstrap --token-ref op://<vault>/<token item>/credential --key-item "<key item>" \
    [--vault <vault name>] [--token-file PATH] [--yes] [--no-hermes-git-env]
op-agent-sign doctor              # all checks must pass; add --commit-test for an end-to-end signed commit
```

`bootstrap` is interactive (it needs a terminal and the 1Password app's CLI integration). It reads the
service-account token through the desktop app once, writes it to the token file (mode 0600, replaced
atomically), writes the key reference to `~/.config/op-agent-sign/config` (0600), checks that the service
account can read a key that matches `user.signingkey`, and, when `~/.hermes` exists, adds the five
`GIT_CONFIG_*` lines to `~/.hermes/.env` (absolute paths; foreign `GIT_CONFIG_*` lines there are never
merged, only reported). It never prints a value; vault and item IDs are masked to four characters.
It refuses to run when `OP_SERVICE_ACCOUNT_TOKEN` is already set in the environment.

## How the key reaches memory (and where it never is)

`op read "op://<vaultID>/<itemID>/private_key?ssh-format=openssh"` writes the key to a pipe, which goes
straight to `ssh-add -` on a private agent socket under `~/.cache/op-agent-sign/` (mode 0700). The key is
never in a file, argv, an environment variable, a log or a trace. The token is only ever in the
environment of the `op` child process. The agent forgets the key after the TTL (default one hour);
`op-agent-sign flush` stops it at once. Do not map the key into any secrets manager that exports it to
the environment or caches it on disk.

## Routing git to the wrapper

Nothing is changed in `~/.gitconfig`. Agents get, in their environment:

```
GIT_CONFIG_COUNT=2
GIT_CONFIG_KEY_0=gpg.ssh.program            GIT_CONFIG_VALUE_0=op-agent-sign   (or an absolute path)
GIT_CONFIG_KEY_1=gpg.ssh.allowedSignersFile GIT_CONFIG_VALUE_1=~/.config/op-agent-sign/allowed_signers
```

Claude Code gets this from the `claude` module's `settings.json` `env` block (the bare name needs
`~/.local/bin` on `PATH`). Hermes gets it from `~/.hermes/.env` (written by `bootstrap`; restart the
gateway afterwards). One-off: `git -c gpg.ssh.program=op-agent-sign commit -S ...`.

## Config keys

File `~/.config/op-agent-sign/config` (directory 0700, file 0600; otherwise exit 77), `KEY="VALUE"` lines.
An environment variable of the same name wins. See `~/.config/op-agent-sign/config.example`.

| Key | Default | Meaning |
|---|---|---|
| `OP_AGENT_SIGN_KEY_REF` | none (required) | `op://<vaultID>/<itemID>/private_key?ssh-format=openssh` |
| `OP_AGENT_SIGN_TOKEN_FILE` | first existing of `~/.hermes/.op.env`, `~/.hermes/.env`, `~/.config/op-agent-sign/token.env` | file holding `OP_SERVICE_ACCOUNT_TOKEN=...` |
| `OP_AGENT_SIGN_TTL` | `3600` | seconds the key stays cached; `0` = a throwaway agent per signature |
| `OP_AGENT_SIGN_DEADLINE` | `20` | seconds allowed for the whole sign path |
| `OP_AGENT_SIGN_RUNTIME_DIR` | `$HOME/.cache/op-agent-sign` | 0700 dir for the agent socket, pid and lock |
| `OP_AGENT_SIGN_FALLBACK` | the 1Password app's `op-ssh-sign` if present, else `none` | signer used when no token is obtainable or the service account fails; `none` disables |
| `OP_AGENT_SIGN_OP` | `op` | the op binary |
| `OP_AGENT_SIGN_DEBUG` | unset | file to append non-secret trace lines to |

## Token file

One line, `OP_SERVICE_ACCOUNT_TOKEN=...`, mode 0600. The wrapper reads it as a file at sign time and passes
it only to `op`. Options for where it lives (`bootstrap --token-file PATH` chooses; the default is
option a):

- a. `~/.hermes/.op.env` on a Hermes host (a dedicated one-line file, loaded by Hermes after `.env`
  and never overriding it), else `~/.config/op-agent-sign/token.env`. Replaced atomically on rotation.
- b. `~/.hermes/.env`: for a path ending in `/.env`, `bootstrap` replaces or appends the single
  `OP_SERVICE_ACCOUNT_TOKEN=` line and leaves every other line byte-for-byte unchanged. Hermes's own
  `hermes secrets onepassword setup/token` also write here; the wrapper reads either file.
- c. A path of your choosing (`OP_AGENT_SIGN_TOKEN_FILE`), for example on an encrypted volume.

A token held by Hermes is visible to its child processes; the blast radius is the vault scope granted to
the service account, so keep that to the one vault holding the signing key.

## Rotation and revocation

- Rotate the service-account token in 1Password (Developer > Service accounts > your account > Rotate;
  choose when the old token expires), update the stored token item, then on each machine run
  `op-agent-sign bootstrap --token-ref ...`, `op-agent-sign flush`, `op-agent-sign doctor`.
- Rotate the signing key: add the new key to 1Password, register its public half where commits are
  verified, append a second line to `allowed_signers` (never delete old lines: old commits must keep
  verifying), update `user.signingkey`, rerun `bootstrap --key-item`.
- Revoke: delete or disable the service account (immediate), then `op-agent-sign flush`. Signing falls
  back per `OP_AGENT_SIGN_FALLBACK`, or fails closed.

## Verbs

`bootstrap`, `setup [--check]`, `doctor [--offline] [--json] [--commit-test]`, `flush`, `selftest`,
`version`, `help`. `selftest` runs the offline suite (fake `op`, throwaway keys, no network). The same
suite runs from the repo with `sh modules/op-agent-sign/tests/run.sh`.

Exit codes: 0 ok, 64 usage, 69 unavailable (no token or token rejected), 70 internal, 72 key mismatch,
75 temporary (rate limit or deadline), 77 permissions.

## Uninstall

`dotm uninstall op-agent-sign` removes the symlinks and keeps your data. To finish: remove the five
`GIT_CONFIG_*` lines from `~/.hermes/.env` and the `env` entries from Claude's `settings.json`, run
`op-agent-sign flush`, then delete `~/.config/op-agent-sign/`, the token file, and the Hermes skill link
under `~/.hermes/skills/security/op-agent-sign`.
