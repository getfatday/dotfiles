# Phase 05 Research: New Modules

**Researched:** 2026-02-12
**Confidence:** HIGH — all items verified against current machine state

## Scope Assessment

The Phase 1 audit (APPS.md) identified these candidates for new modules. With the old laptop volume disconnected, scope is limited to what's verifiable on the current Mac Mini.

### Feasible (current machine has the tools/config)

**1. Rust module** — READY
- Rust is installed on current machine via rustup (standard cargo binaries in `~/.cargo/bin/`)
- `~/.cargo/env` exists with standard PATH export
- No custom `~/.cargo/config.toml` — just the default toolchain
- Module needs: config.yml declaring `rust` formula, .zshenv fragment sourcing cargo/env
- Pattern: follows speckit module pattern (config.yml + mergeable .zshenv)

**2. gh (GitHub CLI) config** — READY
- `~/.config/gh/config.yml` exists on current machine with personal config
- Key settings: `git_protocol: https`, alias `co: pr checkout`
- `hosts.yml` has only `github.com` with user `getfatday` — clean, no corporate
- gh is already declared as a homebrew_package in `modules/git/config.yml`
- Best approach: add `~/.config/gh/config.yml` to git module's stow files (gh is a git tool)
- The hosts.yml should NOT be committed — it contains auth tokens managed by `gh auth login`

### Blocked (old laptop volume required)

**3. Karabiner module** — BLOCKED
- Karabiner-Elements is not installed on current machine
- 109KB karabiner.json with 6 complex modification rules was only on old laptop
- Cannot recreate from memory — complex key binding rules
- Can be revisited if old laptop drive is reconnected or if Karabiner is reinstalled and reconfigured

### Not needed

**4. SSH module** — SKIP (audit confirmed: no SSH config existed on old laptop, 1Password handles SSH agent)
**5. Rectangle** — SKIP (not found on old laptop)
**6. SOPS** — SKIP (not installed on current machine, old laptop config not accessible)
**7. .tool-versions** — SKIP (not on current machine; old laptop had nodejs 25.2.1 and jq 1.7.1 but asdf/node module already handles this)

## Implementation Plan

Two small tasks in a single wave:

1. **Create `modules/rust/`** — config.yml + files/.zshenv
2. **Add gh config to git module** — copy config.yml into git module's stow files at `.config/gh/config.yml`

Both are straightforward file creations following existing module patterns. No research phase needed.
