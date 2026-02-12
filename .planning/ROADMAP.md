# Implementation Roadmap

**Project:** Dotfiles Laptop Audit & Migration
**Created:** 2026-02-11
**Strategy:** Phased migration — audit first, then implement modules, then validate

## Phase 1: Audit & Discovery (read-only)

**Goal:** Inventory everything on the old laptop worth capturing. No writes to repo yet.

### Tasks
1. **Homebrew audit** — Run `brew bundle dump` equivalent against old laptop's Homebrew to generate a complete package list. Compare with existing module declarations.
2. **Git config audit** — Diff old laptop's `.gitconfig` against repo's `modules/git/files/.gitconfig`. Identify SSH signing setup, credential helpers, diff/merge tool config (Kaleidoscope), aliases.
3. **Shell config audit** — Diff old `.zshrc`, `.zprofile`, `.zshenv` against repo's `modules/zsh/`. Identify missing aliases, functions, PATH entries, completions.
4. **~/bin scripts audit** — List all scripts in old laptop's `~/bin/`, categorize as personal vs corporate vs obsolete.
5. **SSH config audit** — Extract old `~/.ssh/config` (hosts, ProxyJump patterns). Filter corporate entries.
6. **App config audit** — Check for configs not yet in repo: Karabiner-Elements, Rust/cargo, Claude Code, OpenClaw, Rectangle, etc.
7. **Corporate artifact scan** — Flag anything matching: expedia, expediagroup, ewegian, hotels.com, vrbo, zscaler, jamf, corporate VPN.
8. **Secret scan** — Identify any API keys, tokens, passwords in configs that would need 1Password routing.

### Acceptance Criteria
- [ ] Audit report exists at `.planning/audit/` with findings per category
- [ ] Corporate artifacts are flagged and excluded
- [ ] No secrets identified in files destined for commit

### Output
- `.planning/audit/HOMEBREW.md` — package comparison
- `.planning/audit/GIT.md` — git config diff
- `.planning/audit/SHELL.md` — shell config gaps
- `.planning/audit/BIN.md` — ~/bin script inventory
- `.planning/audit/APPS.md` — missing app modules
- `.planning/audit/FILTERED.md` — corporate/secret items excluded

---

## Phase 2: Git Module Overhaul

**Goal:** Update `modules/git/` with all missing config from old laptop — SSH signing, Kaleidoscope, credential helpers, global gitignore, and best practices.

**Plans:** 1 plan

Plans:
- [ ] 02-01-PLAN.md — Update .gitconfig, create global gitignore, update config.yml

### Acceptance Criteria
- [ ] `modules/git/files/.gitconfig` reflects all personal git config
- [ ] No corporate git config included
- [ ] SSH signing configured (key reference, not actual key)

---

## Phase 3: Shell Module Update

**Goal:** Capture all missing shell config from old laptop.

### Tasks
1. Add missing aliases to zsh module
2. Add missing shell functions
3. Update PATH entries (respecting Intel→ARM Homebrew path differences)
4. Add missing completions or plugins
5. Ensure corporate PATH entries are excluded

### Acceptance Criteria
- [ ] `modules/zsh/` has all personal shell config
- [ ] PATH handles both `/opt/homebrew` (ARM) and `/usr/local` (Intel) gracefully
- [ ] No corporate shell config included

---

## Phase 4: ~/bin Scripts Module

**Goal:** Capture personal utility scripts.

### Tasks
1. Copy personal scripts from old laptop's `~/bin/` to `modules/bin/files/bin/`
2. Filter out corporate/Expedia scripts
3. Filter out scripts that reference hardcoded paths or secrets
4. Ensure scripts are executable and have proper shebangs
5. Update `modules/bin/config.yml` if needed

### Acceptance Criteria
- [ ] All personal utility scripts captured
- [ ] No corporate scripts included
- [ ] Scripts are functional on Apple Silicon

---

## Phase 5: New Modules

**Goal:** Add modules for apps/tools found on old laptop but missing from repo.

### Tasks
1. **Karabiner module** — Create `modules/karabiner/` with config.yml and karabiner.json
2. **Rust module** — Create `modules/rust/` if cargo/rustup config exists
3. **SSH module** — Create `modules/ssh/` with config template (no private keys)
4. **Any other missing modules** identified in Phase 1 audit

### Acceptance Criteria
- [ ] Each new module follows existing pattern (config.yml + files/)
- [ ] No secrets in any module files
- [ ] Modules are listed in appropriate ansible playbooks

---

## Phase 6: Homebrew Reconciliation

**Goal:** Ensure Brewfile captures all packages from old laptop worth keeping.

### Tasks
1. Compare old laptop's installed packages with module-declared packages
2. Add missing packages to appropriate modules' config.yml
3. Remove any corporate-only packages (Zscaler, Jamf, etc.)
4. Ensure cask vs formula distinction is correct

### Acceptance Criteria
- [ ] All personal Homebrew packages are declared in module configs
- [ ] No corporate packages included

---

## Phase 7: Validation & Deploy

**Goal:** Verify everything works on Mac Mini.

### Tasks
1. Run pre-commit secret scan on entire repo
2. `ansible-playbook --check` (dry run) on Mac Mini
3. Review dry-run output for unexpected changes
4. `ansible-playbook` real run on Mac Mini
5. Verify git config works (signing, diff tools)
6. Verify shell config works (aliases, functions, PATH)
7. Verify ~/bin scripts work
8. Verify new modules deployed correctly

### Acceptance Criteria
- [ ] Dry run passes clean
- [ ] Real run succeeds
- [ ] All migrated configs are functional
- [ ] Old laptop is confirmed wipeable

---

## Execution Notes

- **Phases 1 must complete before 2-6** (need audit data)
- **Phases 2-6 can run in parallel** (independent modules)
- **Phase 7 requires all prior phases** (integration test)
- **Public repo constraint is non-negotiable** — when in doubt, exclude and route to 1Password
