# hermes-platform

The Hermes Agent install, restorable from this repo. Sibling of `modules/hermes` (the Claude Code <->
Hermes bridge), which stays bridge-only.

Today the install, its pin, the local patch branch and the gateway LaunchAgent are artefacts of "ran the
official installer once": no repo restores them. This module owns them.

## What it owns

| Thing | Where | Owner |
|---|---|---|
| upstream commit the install is built on | `pin.txt` | this module |
| local patches (one commit each, on `local/hermes-patches`) | the patch ledger `ledger/local-patches.jsonl` in the lab repo (hyp-hermes), patch files next to it | the ledger; this module applies them |
| dependency environment | official installer, `scripts/install.sh --stage ...` | upstream; this module runs it |
| gateway LaunchAgent plist | `files/Library/LaunchAgents/ai.hermes.gateway.plist`, stowed by dotm | this module |

Not owned: `~/.hermes/config.yaml`, `~/.hermes/.env`, profiles, cron jobs, credentials, launchd load state,
the running gateway. None of the scripts here touch them.

## Use

    dotm sync                                        # stows the plist (capability hermes-host)
    modules/hermes-platform/setup.sh --dry-run       # what setup would do, changes nothing
    modules/hermes-platform/setup.sh                 # clone, branch, patches, bootstrap
    modules/hermes-platform/check.sh                 # read-only verdict; exit 1 on any FAIL
    modules/hermes-platform/check.sh --dry-run       # module structure only (no install needed)

`setup.sh` is idempotent: a second run finds the branch, every patch and the bootstrap marker in place and
changes nothing. Exit 3 means a patch no longer applies (see the rebase rule).

Environment (machine-local, never committed): `HERMES_PLATFORM_HOME` (default `~/.hermes`; not `HERMES_HOME`,
which names a profile dir inside agent sessions), `HERMES_PLATFORM_DIR` (default
`$HERMES_PLATFORM_HOME/hermes-agent`), `HERMES_REPO_URL` (default upstream on GitHub),
`HERMES_PLATFORM_LEDGER` (default `~/src/hyp-hermes/ledger/local-patches.jsonl`),
`HERMES_PLATFORM_PATCH_ROOT` (default: the ledger's repo root; ledger `patch_file` is relative to it).
A machine with neither the lab repo nor the module's `vendor/` copy cannot set up or check the patches: setup fails with
exit 2 and says so rather than installing an unpatched Hermes under a patched pin.

## What setup does, in order

1. Clone `NousResearch/hermes-agent` (treeless, `--no-checkout`) to the install dir if absent.
2. `git switch -c local/hermes-patches <pin>` (or switch to it). Refuses on tracked local changes and when
   the branch is not based on the pin.
3. For each ledger row whose status is not `retired`: `git apply -p1` the patch file and commit it as
   `local(<id>): <narrow_description>`. A patch whose reverse already applies is skipped. Commits are
   unsigned (setup must not need a key agent) and use `hermes-platform@localhost` only when git has no
   identity; the ledger's `commit` sha is informational and differs per machine.
4. Run the official installer's non-interactive stages (`install.sh --manifest` lists them) except
   `repository`, which fast-forwards or resets the checkout and would drop the patch branch. Skipped when
   `.hermes-bootstrap-complete` already records HEAD. `--skip-bootstrap` skips it.

## What check verifies

install dir is a git checkout; HEAD is on `local/hermes-patches`; the pin is an ancestor of HEAD;
`git log <pin>..HEAD` and `git log origin/main..HEAD` each hold exactly as many commits as the ledger has
live patches, touching exactly the files the patches touch; each patch is fully present in the tree; no
uncommitted tracked changes; the gateway plist matches the module's file; `hermes doctor` exits 0.

The plist comparison has three outcomes: a symlink into this module (stowed: ok); a regular file identical
to the module's (the installer-made state before the first sync: ok, reported as unmanaged); anything else
(FAIL).

`hermes doctor` is strict by design: it exits 1 whenever it lists any issue (for example npm advisories in
the browser tools or missing optional API keys), and the check then fails with doctor's own
"Found N issue(s)" line. That is a finding about the install, not about this module; fix it with
`hermes doctor --fix` / `hermes setup`, or relax the check in a follow-up card.

## Rebase rule (on `hermes update`)

`hermes update` pulls upstream onto the working branch. With a patch branch that must never be a silent
stash/pop; it is a rebase:

1. `git -C ~/.hermes/hermes-agent rebase <new upstream sha> local/hermes-patches`
2. A conflict is a loud failure: stop, resolve it by hand, or, if upstream now carries the fix, set the
   patch's ledger row to `retired` and drop it from the branch (`git rebase -i`).
3. Put the new sha in `pin.txt`, commit, `dotm sync`, rerun `setup.sh`, then `check.sh`.

Until step 3, `check.sh` fails on purpose: `<pin>..HEAD` then lists upstream commits that are not ledgered
patches. Never `git stash` in the install and never `hermes update` on this branch without the rebase.

## Stowing the plist

`dotm sync` links `files/Library/LaunchAgents/ai.hermes.gateway.plist` into `~/Library/LaunchAgents`.
The installer left a regular file there, byte-identical to this one when the module was created. If stow
reports a conflict, move the regular file aside first (rename it to `ai.hermes.gateway.plist.bak` in the same directory), then
`dotm sync`. Loading it (`launchctl bootstrap`) and restarting the gateway are not done
by this module; the running job keeps the definition it was loaded with until the operator reloads it.

Known limits of the stowed plist, all inherited from the installer's own file:
- It holds absolute, per-account paths (the home directory and the tool store). The module is therefore
  correct on the machine it was captured from; a machine with another account needs its own capture
  (`hermes gateway install` writes one) before this file is trustworthy there. (dotfiles-ops: plists need
  absolute paths, normally generated per `$HOME`; this module follows the card and stows the captured file.)
- Its `PATH` names a dependency-environment directory by hash. A dependency re-resolve changes that hash;
  the gateway starts through `.hermes/bin/hermes`, which does not depend on it, but the plist then
  drifts from reality until it is recaptured. Today the hash in the file
  (`environments/0a7fda8e...`) is already not the one on disk (`ab693e6d...`).

## Vendored patches (no lab repo needed)

`vendor/` is a faithful copy of the lab's `ledger/local-patches.jsonl` and of every non-retired patch file it names,
under the same relative paths (`vendor/ledger/local-patches.jsonl`, `vendor/experiments/<id>/<name>.patch`), so the
ledger's `patch_file` values resolve against `vendor/` unchanged. When `HERMES_PLATFORM_LEDGER` is unset and the
lab's ledger is not on the machine, the scripts fall back to it; CI sets it explicitly.

Sync rule: whenever the lab's ledger changes (a patch added, retired, or rebased onto a new pin), run
`modules/hermes-platform/vendor-sync.sh` (copies lab to vendor, removes vendored patches no live row names) and commit
`vendor/` together with the `pin.txt` bump if there is one. `vendor-sync.sh --check` is read-only and exits 1 on any
difference; run it before pushing a pin bump. A stale copy fails CI (the restored install no longer matches the
patches the lab says it carries), it does not install quietly unpatched.

## CI restore proof

`.github/workflows/verify.yml` job `macos-hermes` (profile `macos-hermes` in `.ci/contract.json`, driver
`.ci/hermes_fixture.py`) runs on a clean hosted Mac, which is the clean machine: it declares `hermes-host`, checks that
exactly `hermes` and `hermes-platform` are selected because of it, then in a throwaway HOME runs `setup.sh` (clone at
`pin.txt`, patch branch from `vendor/`, official installer stages), a second `setup.sh` (must change nothing),
`hermes doctor` (its exit code is printed as `--- hermes doctor: exit N`), and `check.sh --credentialless`. The child
environment is an allow-list: no token, key or secret reaches it. `--credentialless` reports `skip doctor:
skipped-credential ...` when `hermes doctor` exits non-zero only over issues that need credentials or the interactive
first-run setup; any other issue is still FAIL. The gateway plist is stood in for by a symlink (dotm's stow is covered
by `macos-fixture`); loading it into launchd is not exercised.

## Tests

`tests/run.sh` builds a fixture upstream repo and a scratch `HERMES_PLATFORM_HOME`, then exercises dry-run, clone,
branch, patch apply, idempotent rerun, a conflicting patch (exit 3), and the check verdicts. Offline, no
network, never touches the real install.
