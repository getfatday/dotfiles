# Project Research Summary

**Project:** Ansible-based macOS Dotfiles Management & Migration
**Domain:** Personal infrastructure automation and configuration migration
**Researched:** 2026-02-11
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project transforms an existing macOS laptop's configuration into a version-controlled, Ansible-based dotfiles repository that can safely migrate personal configurations while excluding corporate artifacts. The domain is well-established with clear patterns: modular organization using GNU Stow for symlink management, Ansible for orchestration, and separation of audit (read-only discovery) from migration (write operations) to prevent data loss.

The recommended approach follows a phased migration: first audit the old laptop to inventory configurations and packages, then extract and filter content to remove corporate/sensitive data, implement module-based Ansible playbooks that deploy via GNU Stow, and finally test thoroughly before production deployment. The architecture centers on self-contained modules (git, zsh, node, etc.) that declare their Homebrew dependencies and contribute configuration files, orchestrated by ansible-role-dotmodules which handles package installation and config deployment.

Critical risks include accidental secret commits (9.5% of dotfiles repos leak credentials), corporate artifact contamination (VPN configs, internal hostnames), and Homebrew architecture mismatches when migrating Intel → Apple Silicon. All are mitigated through pre-commit hooks with secret scanning, explicit corporate filtering checklists during audit, and clean Homebrew reinstallation from Brewfile rather than wholesale directory copying. The research provides HIGH confidence on stack choices and architecture patterns, MEDIUM confidence on features and pitfall prevention strategies.

## Key Findings

### Recommended Stack

The stack is proven and stable: ansible-core 2.20.2 (requires Python 3.12+) provides the automation foundation, with community.general and geerlingguy.mac collections for macOS-specific tasks. Homebrew handles package management, mas-cli automates Mac App Store installations, and 1Password CLI manages secrets without committing them to the repository.

**Core technologies:**
- **ansible-core 2.20.2**: Infrastructure automation engine — latest stable with Python 3.12+ support, actively maintained
- **Homebrew + mas-cli 4.0+**: macOS package management — de facto standard, required for automated installs, mas-cli is only CLI tool for App Store automation
- **GNU Stow**: Dotfile symlink management — built into module pattern, preserves repo structure while deploying to $HOME
- **1Password CLI 2.18.0+**: Secret management — service account support prevents committing credentials to public repo
- **rsync**: File/directory comparison — preserves macOS extended attributes critical for Mac-to-Mac migrations

**Version considerations:**
- ansible-core 2.20.2 requires Python 3.12+ (use 2.19.6 if stuck on Python 3.11)
- Apple Silicon uses `/opt/homebrew` prefix vs `/usr/local` on Intel (auto-detected by Ansible)
- mas-cli 4.0+ requires root for all operations after Apple CVE-2025-43411 fix

### Expected Features

Dotfiles audit and migration breaks into three clear phases: audit (discovery), migration (Ansible translation), and enhancement (testing/multi-machine). The research identified distinct feature sets for each phase.

**Must have (table stakes):**
- File discovery and inventory — cannot migrate without knowing what exists
- Git config extraction — identity, signing keys, credential helpers are critical workflows
- Secret detection and separation — blockers for public repo, must identify before committing
- Corporate artifact filtering — legal requirement to exclude Expedia-specific configs
- ~/bin script migration — custom utilities are high-value, low-volume wins
- SSH config migration — access patterns needed (keys stay local, regenerate per machine)
- Module-based organization — foundation for maintainability and selective deployment
- Idempotent Ansible playbooks — safe to run multiple times without breaking system

**Should have (competitive):**
- Configuration diff reports — visual comparison of old vs new configs to verify completeness
- Backup and rollback mechanisms — migration mistakes must be recoverable
- Shell config gap analysis — identify missing aliases, functions, PATH entries
- Pre-commit hook integration — defense-in-depth against secret leakage
- Credential helper validation — verify 1Password git integration works post-migration

**Defer (v2+):**
- Automated testing in containers — high value but requires stable playbooks first
- Multi-machine config variants — not needed for single-machine initial migration
- Dependency graph visualization — manual documentation sufficient initially
- Configuration merge strategies — address when conflicts actually arise

### Architecture Approach

The architecture follows a layered model: audit scripts discover and extract configurations from the old machine into a gitignored temp/ directory, migration scripts filter corporate/sensitive content into a staging area, and ansible-role-dotmodules orchestrates deployment by discovering module config.yml declarations, aggregating Homebrew packages, and deploying files via GNU Stow or config merging.

**Major components:**
1. **Audit Layer** — Bash scripts using `brew bundle dump`, `find`, `diff` to inventory old machine (read-only, safe to run repeatedly)
2. **Module Directory** — Self-contained units with config.yml declaring dependencies and files/ containing actual dotfiles (each concern gets own module: git, zsh, node, bin)
3. **ansible-role-dotmodules** — Orchestration engine that discovers modules, aggregates package lists, resolves merge vs stow strategies, calls Homebrew modules and Stow
4. **Deployment Layer** — GNU Stow for single-owner files (symlinks .gitconfig → repo), merge strategy for multi-contributor files (.zshrc receives sections from git, zsh, node modules)

**Critical patterns:**
- **Separation of audit and migration**: Audit is read-only discovery, extraction copies to temp/, filtering cleans to staging/, only then manual review and commit to modules
- **Secrets in 1Password, not repo**: Use placeholders in committed configs, inject real values via `op` CLI during deployment
- **Homebrew Bundle for audit**: `brew bundle dump` generates comprehensive Brewfile from old machine, compare with module declarations to find gaps
- **Multi-strategy deployment**: Stow for files owned by single module, merge for shared files like .zshrc with section delimiters

### Critical Pitfalls

Research identified eight critical pitfalls with clear mitigation strategies:

1. **Accidental Secret Commits** — 9.5% of dotfiles repos leak credentials. Use gitleaks pre-commit hooks, add .ssh/, .gnupg/, *_history to .gitignore immediately, scan with `git filter-repo` before first commit.

2. **Corporate Artifact Contamination** — VPN configs, internal DNS, company domains slip into public repo. Create audit checklist for corporate indicators, grep old laptop for `expedia|corp|vpn|proxy`, manual review before any commits.

3. **Homebrew Architecture Mismatch** — Migration Assistant copies Intel Homebrew to Apple Silicon causing "Cannot install in ARM processor in Intel default prefix" errors. Never migrate Homebrew directories, export Brewfile from old machine, clean install native Homebrew at `/opt/homebrew`, bundle install from saved file.

4. **Shell Configuration PATH Reordering** — macOS `path_helper` re-orders $PATH to prioritize system paths over Homebrew/custom. Put PATH mods in .zshrc AFTER system init, call `brew shellenv` then append custom paths, use path arrays not string concat.

5. **Ansible Idempotency Failures** — Tasks report "changed" on every run. Use Ansible modules over shell commands, add `changed_when` with output parsing for unavoidable shell tasks like Stow, avoid `recurse: yes` on file permissions, test twice (second run should show zero changes).

6. **Overwriting Existing Configuration** — Playbook destroys local customizations without backup. Use `backup: yes` in file/copy/template tasks, manual backup before first run, test on VM/container before production, use `--diff` mode.

7. **Git History Contains Old Secrets** — Removing from working tree doesn't remove from history. Run `gitleaks detect` before first commit, use `git filter-repo` to clean history (not deprecated `git filter-branch`), revoke exposed credentials immediately even after cleaning.

8. **Architecture-Specific Hardcoding** — Hardcoded `/usr/local/bin` paths break on different architectures. Use `$(brew --prefix)` instead of hardcoded paths, detect architecture with `uname -m`, let `brew shellenv` handle paths, avoid architecture-specific packages.

## Implications for Roadmap

Based on research, a five-phase structure emerges naturally from dependency relationships and safety requirements:

### Phase 1: Audit Foundation
**Rationale:** Must establish safe practices (secret scanning, corporate filtering) BEFORE any file operations. Audit is read-only and reversible, making it the safest starting point.

**Delivers:**
- Pre-commit hooks with gitleaks for secret detection
- Corporate artifact identification checklist
- Audit scripts that discover packages (brew bundle dump), dotfiles (find), and diffs (comparison)
- temp/ directory structure with .gitignore

**Addresses:**
- Secret detection and separation (table stakes)
- Corporate artifact filtering (table stakes)
- File discovery and inventory (table stakes)

**Avoids:**
- Pitfall #1 (Accidental Secret Commits) — hooks block before any commits
- Pitfall #2 (Corporate Artifact Contamination) — checklist guides manual review
- Pitfall #7 (Git History Contains Secrets) — scanning happens before first commit

**Research flag:** Standard patterns, skip `/gsd:research-phase`

### Phase 2: Homebrew Migration
**Rationale:** Homebrew is foundational for all other tools. Clean migration prevents architecture mismatch issues that would break later phases. Must come before shell config (which references Homebrew paths) and Ansible implementation (which installs packages).

**Delivers:**
- Brewfile extracted from old machine
- Clean native Homebrew installation at `/opt/homebrew` (Apple Silicon) or `/usr/local` (Intel)
- Module config.yml structure defined for declaring package dependencies
- Verification that `brew doctor` passes and architecture detection works

**Addresses:**
- Homebrew architecture detection and clean installation
- Package inventory and dependency management

**Uses:**
- mas-cli for Mac App Store automation (from STACK.md)
- brew bundle for package export/import (from ARCHITECTURE.md Pattern 5)

**Avoids:**
- Pitfall #3 (Homebrew Architecture Mismatch) — explicit clean install prevents Intel → ARM issues
- Pitfall #8 (Architecture-Specific Hardcoding) — dynamic prefix detection established early

**Research flag:** Standard patterns, skip `/gsd:research-phase`

### Phase 3: Config Extraction & Filtering
**Rationale:** With safe practices established (Phase 1) and Homebrew foundation in place (Phase 2), can safely extract configs from old machine. Filtering MUST happen before committing to modules to prevent corporate contamination.

**Delivers:**
- Extraction scripts that copy configs to temp/old-machine/
- Filtering scripts that clean corporate content to temp/staging/
- Git config extracted with placeholders for personal email
- SSH config extracted without private keys
- ~/bin scripts migrated with permissions preserved

**Addresses:**
- Git config extraction (table stakes)
- SSH config migration (table stakes)
- ~/bin script migration (table stakes)
- Corporate artifact filtering execution

**Uses:**
- rsync for Mac-to-Mac file preservation (from STACK.md)
- 1Password CLI for secret placeholders (from ARCHITECTURE.md Pattern 4)

**Avoids:**
- Pitfall #2 (Corporate Artifact Contamination) — filtering scripts remove work-specific content
- Pitfall #6 (Direct Migration Without Audit) — temp/ staging prevents accidental overwrites

**Research flag:** Standard patterns, skip `/gsd:research-phase`

### Phase 4: Module Implementation
**Rationale:** With filtered configs in staging area, can now structure as Ansible modules. Module organization must be complete before deployment playbooks. This phase implements the core architecture pattern.

**Delivers:**
- Module directory structure (modules/git/, modules/zsh/, modules/bin/)
- config.yml for each module declaring Homebrew dependencies and stow dirs
- ansible-role-dotmodules installed and configured
- Idempotent playbooks that check state before changes

**Addresses:**
- Module-based organization (table stakes)
- Idempotent Ansible playbooks (table stakes)
- Configuration merge strategies (differentiator)

**Implements:**
- Module-Based Organization pattern (ARCHITECTURE.md Pattern 1)
- Multi-Strategy File Deployment (ARCHITECTURE.md Pattern 3)

**Uses:**
- ansible-core 2.20.2 with community.general collection (from STACK.md)
- GNU Stow for symlink management (from STACK.md)

**Avoids:**
- Pitfall #5 (Ansible Idempotency Failures) — write with `changed_when` from start
- Architecture Anti-Pattern #3 (Monolithic .zshrc) — modular approach prevents

**Research flag:** Standard patterns, skip `/gsd:research-phase`

### Phase 5: Testing & Deployment
**Rationale:** Must test deployment thoroughly before applying to production system. Container testing proves idempotency, backups enable rollback, verification confirms correctness.

**Delivers:**
- Backup strategy with restoration verification
- Container-based testing that proves idempotency (second run = zero changes)
- Shell config gap analysis comparing old vs new
- Credential helper validation (1Password git integration)
- Pre-deployment checklist and post-deployment verification

**Addresses:**
- Backup and rollback (should have)
- Diff visibility (table stakes)
- Shell config gap analysis (should have)
- Credential helper validation (should have)

**Uses:**
- Docker/Podman for automated testing (from FEATURES.md differentiators)
- Ansible --check and --diff modes for verification

**Avoids:**
- Pitfall #4 (Shell PATH Reordering) — verify PATH order in test environment
- Pitfall #6 (Overwriting Existing Configuration) — backups tested before production
- All "Looks Done But Isn't" checklist items verified

**Research flag:** Standard patterns for testing, skip `/gsd:research-phase`

### Phase Ordering Rationale

**Safety-first approach:**
- Phase 1 establishes guardrails (secret scanning, filtering checklists) before touching any files
- Each phase builds on previous: can't filter (P3) without audit tools (P1), can't deploy (P5) without modules (P4)
- Read-only operations (audit, inventory) come before write operations (extraction, deployment)

**Dependency-driven:**
- Homebrew (P2) must exist before shell configs (which reference brew paths)
- Modules (P4) must exist before deployment (P5)
- Extraction (P3) requires audit results (P1) to know what to copy

**Pitfall prevention:**
- Architecture mismatch (P3) addressed early by cleaning Homebrew in P2
- Secret leakage (P1, P7) blocked before first commit via hooks
- Idempotency failures (P5) caught in container testing before production

**Reversibility:**
- Audit (P1) is non-destructive and repeatable
- Extraction to temp/ (P3) is gitignored and disposable
- Container testing (P5) validates before production deployment
- Backups enable rollback if issues discovered

### Research Flags

**Phases with standard patterns (skip research-phase):**
- **Phase 1:** Secret scanning and audit scripts are well-documented, gitleaks patterns established
- **Phase 2:** Homebrew migration extensively documented in Homebrew GitHub discussions
- **Phase 3:** rsync and filtering are standard Unix operations with clear patterns
- **Phase 4:** ansible-role-dotmodules provides established module pattern, Ansible docs comprehensive
- **Phase 5:** Container testing patterns documented, idempotency verification standard practice

**No phases require `/gsd:research-phase`** — all patterns are well-established in the domain with multiple reference implementations and official documentation.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified with PyPI, Homebrew formulae, official Ansible docs; versions and compatibility confirmed |
| Features | MEDIUM | Based on community best practices and multiple dotfiles repos; patterns consistent across sources but no single authoritative feature list |
| Architecture | HIGH | ansible-role-dotmodules analyzed via WebFetch, GNU Stow patterns well-documented, multiple reference implementations |
| Pitfalls | MEDIUM-HIGH | Homebrew migration issues documented in GitHub discussions, secret leakage verified by research paper (124,230 repos studied), shell PATH issues confirmed in community posts |

**Overall confidence:** MEDIUM-HIGH

Research quality is strong for technical stack and architectural patterns (official sources, active projects), moderate for features and pitfalls (community consensus, empirical evidence but no authoritative standards). No major gaps that would block implementation.

### Gaps to Address

- **1Password CLI integration patterns**: Research shows it's used widely but specific Ansible integration patterns for service accounts need validation during Phase 4 implementation. Mitigation: Start with manual `op` CLI calls, formalize as Ansible lookup plugin if needed.

- **ansible-role-dotmodules conflict resolution**: Documentation describes merge strategy for shared files but conflict resolution logic not fully specified. Mitigation: Test multi-module .zshrc merging in Phase 4, document actual behavior vs expected.

- **mas-cli 4.0+ sudo requirements**: Recent CVE fix changed behavior but community experience limited. Mitigation: Test App Store installations with sudo in Phase 2, verify ansible tasks include become: yes.

- **Corporate artifact patterns**: Expedia-specific indicators need manual enumeration. Mitigation: Phase 1 includes explicit corporate discovery step with grep patterns for common corporate strings.

- **Shell config PATH testing**: Verification of PATH order across login/non-login shells needs explicit test cases. Mitigation: Phase 5 includes automated PATH verification script run in multiple shell contexts.

## Sources

### Primary (HIGH confidence)
- [ansible-core PyPI](https://pypi.org/project/ansible-core/) — Version 2.20.2 verified, Python 3.12+ requirement confirmed
- [Ansible GitHub Releases](https://github.com/ansible/ansible/releases) — Release dates (Jan 29, 2026) verified
- [community.general.homebrew module documentation](https://docs.ansible.com/projects/ansible/latest/collections/community/general/homebrew_module.html) — Official module parameters and usage
- [Homebrew Bundle Documentation](https://docs.brew.sh/Brew-Bundle-and-Brewfile) — Official guide to `brew bundle dump`
- [1Password Connect Ansible Collection docs](https://developer.1password.com/docs/connect/ansible-collection/) — Service account integration patterns
- [mas-cli GitHub](https://github.com/mas-cli/mas) — Version 4.0 requirements and CVE-2025-43411 fix details

### Secondary (MEDIUM confidence)
- [geerlingguy.mac collection GitHub](https://github.com/geerlingguy/ansible-collection-mac) — Roles and integration patterns verified
- [Homebrew migration discussions](https://github.com/orgs/Homebrew/discussions/4506) — Intel → Apple Silicon best practices from maintainers
- [Ansible for dotfiles introduction](https://phelipetls.github.io/posts/introduction-to-ansible/) — Community patterns and role organization
- [Managing Dotfiles with Ansible | The Broken Link](https://thebroken.link/managing-dotfiles-with-ansible/) — Module-based organization patterns
- [Automated and Tested Dotfile Deployment Using Ansible and Docker](https://bananamafia.dev/post/dotfile-deployment/) — Container testing strategies
- [ansible-role-dotmodules GitHub](https://github.com/getfatday/ansible-role-dotmodules) — Reference implementation (analyzed via WebFetch)
- [Connecting the .dotfiles: Checked-In Secret](https://pure.mpg.de/rest/items/item_3505626/component/file_3505627/content) — Academic research on 124,230 repos with leaked secrets
- [Git configurations in a code audit](https://some-natalie.dev/blog/git-config-audits/) — Critical git config areas and security concerns
- [Properly setting $PATH for zsh on macOS](https://gist.github.com/Linerre/f11ad4a6a934dcf01ee8415c9457e7b2) — path_helper interaction with custom PATH

### Tertiary (LOW confidence)
- Various GitHub dotfiles repos for pattern examples (consistency across many repos provides validation)
- DirEqual commercial GUI tool (not tested, mentioned as optional)
- mackup exclusion patterns (community contributions, no official validation)

---
*Research completed: 2026-02-11*
*Ready for roadmap: yes*
