---
phase: 05-new-modules
plan: 01
subsystem: modules
tags:
  - rust
  - gh-cli
  - module-creation
  - toolchain
dependency_graph:
  requires:
    - speckit-module-pattern
  provides:
    - rust-module
    - gh-cli-config
  affects:
    - modules/rust
    - modules/git
tech_stack:
  added:
    - rustup-init (homebrew)
  patterns:
    - mergeable zshenv files
    - stow configuration deployment
    - XDG config standard (.config/gh)
key_files:
  created:
    - modules/rust/config.yml
    - modules/rust/files/.zshenv
    - modules/git/files/.config/gh/config.yml
  modified: []
decisions:
  - decision: "Guard cargo env with file existence test"
    rationale: "Prevents errors if rustup not yet initialized"
    alternatives_considered: ["Unconditional source"]
  - decision: "Exclude hosts.yml from git module"
    rationale: "Contains OAuth tokens from gh auth login"
    alternatives_considered: ["None - security requirement"]
metrics:
  duration_seconds: 60
  tasks_completed: 2
  commits_created: 2
  deviations: 0
  completed_date: "2026-02-12T12:35:11Z"
---

# Phase 5 Plan 1: New Modules Summary

**One-liner:** Created Rust toolchain module with rustup-init and cargo env integration, plus gh CLI config in git module with HTTPS protocol and pr checkout alias.

## Objective

Create new modules for tools identified during audit: Rust toolchain module and gh CLI config in git module. Both tools are present on the current machine and can be captured now.

## Tasks Completed

### Task 1: Create Rust module
- **Status:** Complete
- **Commit:** 633b8d7
- **Files:**
  - `modules/rust/config.yml` - Module declaration with rustup-init homebrew package
  - `modules/rust/files/.zshenv` - Cargo environment integration with existence guard
- **Verification:** All files exist, rustup-init declared, cargo env sourced, security scans clean

### Task 2: Add gh CLI config to git module
- **Status:** Complete
- **Commit:** ff10894
- **Files:**
  - `modules/git/files/.config/gh/config.yml` - GitHub CLI configuration
- **Security:** hosts.yml excluded (contains OAuth tokens)
- **Verification:** git_protocol set to https, co alias configured, no tokens in committed files

## Deviations from Plan

None - plan executed exactly as written.

## Success Criteria Met

- [x] Rust module is self-contained with config.yml and mergeable .zshenv
- [x] gh CLI config is part of git module stow deployment
- [x] No secrets or auth tokens in any committed file
- [x] Karabiner documented as blocked (volume disconnected, not installed)

## Verification Results

```
PASS: modules/rust/config.yml exists
PASS: modules/rust/files/.zshenv exists
PASS: modules/git/files/.config/gh/config.yml exists
PASS: no hosts.yml committed
PASS: no secrets found in security scan
```

## Key Artifacts

### modules/rust/config.yml
Declares rustup-init as homebrew package, rust as stow directory, and .zshenv as mergeable file. Provides Rust toolchain management via rustup.

### modules/rust/files/.zshenv
Sources `$HOME/.cargo/env` with file existence guard to add Cargo bin directory to PATH. Will be merged with main .zshenv file during deployment.

### modules/git/files/.config/gh/config.yml
Configures GitHub CLI with HTTPS protocol, enables prompt, adds `co` alias for `pr checkout`. Deployed via git module's stow tree to `~/.config/gh/config.yml`.

## Security Notes

- **hosts.yml excluded:** This file contains OAuth tokens from `gh auth login` and must never be committed
- **No hardcoded paths:** All paths use $HOME variable or relative paths
- **No secrets:** Security scans confirmed no tokens, passwords, or keys in any committed file

## Next Phase Readiness

**Blockers:** None

**Dependencies satisfied:**
- Rust module ready for stow deployment
- gh CLI config ready for stow deployment
- Both modules follow speckit pattern

**Notes:**
- After deployment, run `rustup-init` to initialize Rust toolchain if not already present
- gh auth still requires manual `gh auth login` (OAuth flow not in dotfiles)
- Karabiner capture deferred - old laptop volume disconnected, tool not installed on current machine

## Self-Check: PASSED

**Files created:**
- modules/rust/config.yml - FOUND
- modules/rust/files/.zshenv - FOUND
- modules/git/files/.config/gh/config.yml - FOUND

**Commits created:**
- 633b8d7 - FOUND (feat(05-01): add rust toolchain module)
- ff10894 - FOUND (feat(05-01): add gh CLI config to git module)

**Must-have truths verified:**
- [x] modules/rust/ exists with config.yml and files/.zshenv
- [x] Rust module declares rustup-init homebrew formula
- [x] Rust module .zshenv sources $HOME/.cargo/env
- [x] gh config.yml is in git module stow tree at .config/gh/config.yml
- [x] gh config.yml has git_protocol: https and co alias
- [x] No secrets, tokens, or auth credentials in any committed file
- [x] hosts.yml is NOT committed (contains auth tokens)
