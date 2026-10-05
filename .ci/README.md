# dotm verification v1

Implemented locally; no workflow has been pushed or run on GitHub. No branch protection was changed.

## Contract and scope

`contract.json` is the reviewed repo manifest and policy version. All models use the same commands. `verify.py run PROFILE` executes fixed argv with timeouts and records exit codes, log hashes, dependency environment, commit, input-tree hash (including untracked/nonignored changes and executable bits), and manifest hash. `verify.py accept` rejects absent/duplicate profiles, skipped/failed/cancelled jobs, changed inputs, stale commit/contract, expired receipts, different workflow run/attempt, missing command evidence and altered logs. Model prose cannot satisfy these checks.

The stable check is **dotm-acceptance**. It runs even when a dependency fails and requires all three profiles. No path-filter skips or continue-on-error are used. New content invalidates earlier receipts. Results live in ignored `.ci/results/`, uploaded for seven days. Logs come only from synthetic fixtures/tests; never place credentials in test fixtures.

| Profile | Required coverage | Explicit exclusions |
| --- | --- | --- |
| fast / Ubuntu x64 | Python syntax, YAML/module configuration, full dotm tests and negative gate tests | No production apply |
| macos-fixture / macos-14 ARM | Pinned dotmodules role applies a synthetic root-level dotfile to temporary HOME; link/content checks; second apply must report changed=0 | No Homebrew/MAS/package installs, preferences, services, credentials, production deploy.yml or full Mac qualification |
| linux-arm-fixture / Ubuntu 24.04 ARM | Native ARM platform/role-selection unit tests and the same pinned-role state/idempotence fixture | No APT package installs, Pi hardware, boot/device/service validation |

Platform fixtures refuse ordinary local invocation, use disposable hosted runners and a unique temporary HOME, and never select real user modules. This guard prevents accidental use; it is not a security sandbox against someone who can change the workflow or environment. Production apply remains separately authorized and must have affected-module `dotm verify` plus relevant behavior checks on the actual target.

## Baseline reconciliation

Before this change: 73 pass, 2 fail in the full dotm suite. The two failing tests populated the obsolete deploy.yml `dotmodules.install` field, while `get_deploy_modules()` deliberately reads profiles.yml `base_modules`. The fixtures now use the documented production source, retain their original membership assertions, and add a test proving that a contradictory legacy playbook does not override profiles. No tests were skipped and no production behavior changed. The separate `requires: null` patch remains unapplied.

## Local commands

Use Python 3.13.12 and an isolated venv. Install `.ci/requirements.lock` using pip `--require-hashes` or uv's equivalent, then:

```sh
python .ci/verify.py run fast
python .ci/verify.py accept
```

The second command must fail locally when the two hosted-platform receipts are missing. Do not manufacture them. Hosted runners install the role SHA from `.ci/ansible-requirements.yml` and CI-only exact collection versions; production requirements.yml remains unchanged. Python dependencies include transitive hashes. Regenerate the lock deliberately with `uv pip compile .ci/requirements.in --python-version 3.13 --generate-hashes --output-file .ci/requirements.lock` and review updates. Action release tags were resolved through GitHub to immutable commits; runner OS labels and exact Python versions are explicit but hosted image contents can still change.

## Enforcement boundary and activation proposal

Receipts are not cryptographic attestations. Anyone allowed to modify the workflow/verifier can weaken it; publishing these files alone does not prevent merging. Independently review `.github/workflows/verify.yml`, `.ci/**`, tests and exceptions. A later separately approved repository rule should require `dotm-acceptance` and independent review of policy changes. Do not let an implementation agent approve its own acceptance changes. Hermes PR completion contracts can then consume repository-required CI checks for the actual PR head. Local-only Kanban completion and target deployment remain separate boundaries.

Proposed triggers, effective only after authorized publication: every pull request, pushes to main, and manual workflow_dispatch. No pull_request_target, secrets, OIDC, deployments, self-hosted runners, or schedules. Token permissions: contents:read; checkout credentials are not persisted. The three jobs time out at 15 minutes; aggregate at 5; superseded runs cancel. These are job bounds, not an account spending cap.

## Initial budget for review

GitHub identified getfatday/dotfiles as public. GitHub currently documents standard hosted runners as free for public repos, but activation should still confirm account/billing policy, repo visibility and selected runner labels; no guaranteed-free claim is made here. No paid or larger runners are selected.

Using published fallback rates if minutes become billable: Linux x64 $0.006/min, ARM $0.005/min, macOS $0.062/min. Planning assumptions per matrix: fast 5 min ($0.030), Mac 8 ($0.496), ARM 6 ($0.030), acceptance 2 ($0.012): **$0.568/run**, about **$5.68 for ten runs**, excluding artifact storage. At configured job timeouts the compute estimate is **$1.125/run** (15/15/15/5 minutes). Rounding, retries and repeated pushes add usage; storage has its own policy. These runtime assumptions are not measured hosted durations. Start with one approved run, inspect timing and logs, then decide the recurring trigger/required-check policy.

Sources checked 2026-10-04: [runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing), [standard runner labels and public-repository billing](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

## Repair rules

Failure stays failed. Preserve evidence, diagnose, draft a bounded repair, rerun the same contract, then independent review. Do not remove gates, suppress failures or auto-apply. A known-baseline exception requires explicit owner approval and expiry; v1 has none. New repos remain inspection/proposal-only until their manifest and permissions are reviewed. This implementation is a small dotm pilot, not a deployed general-purpose verification service.
