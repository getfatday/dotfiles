# Feature Research

**Domain:** Dotfiles Audit & Migration (Laptop → Ansible-based Repository)
**Researched:** 2026-02-11
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Must Have or Migration Fails)

Features required for successful dotfiles audit and migration. Missing these = broken or incomplete migration.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| File Discovery & Inventory | Can't migrate what you can't find | Low | Scan mounted volume for all dotfiles, config directories, and user customizations |
| Git Config Extraction | Git settings contain identity, signing, credentials | Low | Extract .gitconfig, includeIf directives, global hooks, credential helpers |
| Secret Detection & Separation | Public repo cannot contain credentials | Medium | Pattern matching for API keys, passwords, tokens; must be 1Password-bound |
| Corporate Artifact Filtering | Expedia-specific configs must be excluded | Medium | Pattern-based exclusion rules to prevent corporate IP in public repo |
| Idempotent Ansible Playbooks | Must be safe to run multiple times | Medium | All tasks check before change; second run = no changes |
| ~/bin Script Migration | Custom utilities are critical workflows | Low | Inventory all scripts, preserve permissions, document dependencies |
| Module-Based Organization | Monolithic configs are unmaintainable | Medium | Each concern (git, shell, editor) = separate module with config.yml |
| Diff Visibility | Need to see what's changing before applying | Low | Preview mode showing before/after states for all changes |
| Backup & Rollback | Migration mistakes must be recoverable | Medium | Snapshot existing configs before modification; rollback mechanism |
| SSH Config Migration | SSH settings control access to services | Low | Extract .ssh/config (not keys), known_hosts patterns, includes |

### Differentiators (Makes Migration Robust/Maintainable)

Features that separate fragile migrations from production-quality dotfiles systems.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Automated Testing in Containers | Prove idempotency before deploying to host | High | Docker/Podman containers test full playbook execution; catch errors early |
| Configuration Diff Reports | Visual comparison of old vs new configs | Medium | Side-by-side diff showing what was captured vs what already exists |
| Missing App Module Detection | Discover apps with config but no dotfiles module | Medium | Compare installed apps against existing modules; generate scaffolding |
| Multi-Machine Config Variants | Same repo, different configs per machine | Medium | Ansible host_vars or conditional includes based on hostname/tags |
| Credential Helper Validation | Verify git credential helpers work post-migration | Low | Test 1Password git integration, SSH signing with actual operations |
| Dependency Graph Visualization | Show which modules depend on which packages | Medium | Document Homebrew dependencies per module; detect conflicts |
| Audit Trail Documentation | Record what was found, what was excluded, why | Low | Migration report with decisions, exclusions, transformations |
| Shell Config Gap Analysis | Compare old shell setup against migrated config | Medium | Identify missing aliases, functions, PATH entries not yet captured |
| Pre-commit Hook Integration | Prevent secrets from entering git history | Low | Gitleaks or similar scanning before commits; fail on detected secrets |
| Configuration Merge Strategies | Handle conflicts between modules intelligently | High | When multiple modules provide same config, define precedence rules |

### Anti-Features (Deliberately NOT Building)

Features that seem useful but create problems in dotfiles audit context.

| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| Full System State Capture | "Capture everything for perfect reproduction" | Creates massive, brittle configs full of system-generated cruft | Capture only user-authored configs; let Ansible/Homebrew handle system state |
| Automatic Secret Encryption in Repo | "Keep secrets in git with encryption" | Encrypted secrets still leak metadata; rotation nightmare | Use 1Password references; secrets never touch repo even encrypted |
| Binary File Migration | "Preserve app state files, caches, databases" | Bloats repo with non-portable, version-specific binaries | Document how to regenerate state; only track human-readable configs |
| Corporate Config Preservation | "Keep Expedia stuff for reference" | Legal/IP risk in public repo; stale after leaving company | Document patterns learned; exclude all corporate artifacts |
| Universal Playbook (All Platforms) | "One playbook works everywhere" | Complexity explosion; platform-specific quirks everywhere | macOS-first with documented extension points for Linux later |
| Automated Module Creation | "Auto-generate modules from discovered configs" | Creates low-quality modules with unclear ownership | Manual module creation with intentional design; discovery informs but doesn't automate |
| Live Sync to Repo | "Automatically commit config changes" | Unreviewed commits; secrets slip through; noise | Manual review and commit; changes are intentional |
| Complete Package History | "Track every version of every package ever installed" | Irrelevant for fresh setup; creates maintenance burden | Track current versions only; Homebrew handles updates |

## Feature Dependencies

```
File Discovery & Inventory
    └──requires──> Mounted Volume Access
                        └──enables──> Git Config Extraction
                        └──enables──> ~/bin Script Migration
                        └──enables──> SSH Config Migration

Secret Detection & Separation
    └──requires──> Pattern Matching Engine
                        └──requires──> 1Password Integration (for storage)

Corporate Artifact Filtering
    └──requires──> Pattern Definition
                        └──conflicts──> Corporate Config Preservation (anti-feature)

Module-Based Organization
    └──requires──> Ansible Role Structure
                        └──enables──> Configuration Merge Strategies
                        └──enables──> Multi-Machine Config Variants

Idempotent Ansible Playbooks
    └──requires──> State Checking Before Changes
                        └──enables──> Automated Testing in Containers
                        └──enables──> Backup & Rollback

Automated Testing in Containers
    └──requires──> Idempotent Ansible Playbooks
    └──requires──> Docker/Podman
                        └──enhances──> Configuration Diff Reports

Pre-commit Hook Integration
    └──enhances──> Secret Detection & Separation
                        └──prevents──> Live Sync to Repo (anti-feature)

Audit Trail Documentation
    └──requires──> File Discovery & Inventory
    └──requires──> Corporate Artifact Filtering
                        └──enables──> Configuration Diff Reports
```

### Dependency Notes

- **File Discovery requires Mounted Volume Access:** Cannot audit old laptop without read access to /Volumes/Macintosh HD-1/Users/ianderson/
- **Secret Detection requires 1Password Integration:** Detected secrets must have a storage destination; 1Password is the chosen vault
- **Module Organization enables Merge Strategies:** Without modules, configuration merging is undefined; modules provide boundaries
- **Idempotency enables Container Testing:** Cannot safely test in containers if playbooks aren't idempotent (risk of corrupting test environment)
- **Pre-commit hooks enhance Secret Detection:** Defense-in-depth; catch secrets both during audit and before commit
- **Corporate filtering conflicts with preservation:** Mutually exclusive; must choose public-safe over corporate reference

## MVP Recommendation

### Launch With (Audit Phase Complete)

Minimum viable audit — what's needed to safely capture personal configs from old laptop.

- [x] File Discovery & Inventory — Cannot migrate without knowing what exists
- [x] Git Config Extraction — Identity, signing, diff tools are critical workflows
- [x] Secret Detection & Separation — Blockers for public repo; must identify before committing
- [x] Corporate Artifact Filtering — Legal requirement; Expedia patterns must be excluded
- [x] ~/bin Script Migration — Custom scripts are high-value, low-volume
- [x] SSH Config Migration — Access patterns needed (without private keys)
- [x] Module-Based Organization — Foundation for maintainability
- [x] Audit Trail Documentation — Record decisions for future reference

### Add After Validation (Ansible Migration Phase)

Features to add once core inventory is complete and being translated to Ansible.

- [ ] Idempotent Ansible Playbooks — Implement after manual inventory review
- [ ] Diff Visibility — Add when testing playbooks against existing configs
- [ ] Backup & Rollback — Critical before first destructive run
- [ ] Configuration Diff Reports — Useful during iterative refinement
- [ ] Missing App Module Detection — Once base modules are established
- [ ] Shell Config Gap Analysis — After initial shell module migration
- [ ] Credential Helper Validation — After git module is ansible-ified
- [ ] Pre-commit Hook Integration — Once repo structure is stable

### Future Consideration (Enhancement Phase)

Features to defer until base system is working and proven.

- [ ] Automated Testing in Containers — High value but requires stable playbooks first
- [ ] Multi-Machine Config Variants — Not needed for single-machine initial migration
- [ ] Dependency Graph Visualization — Nice-to-have; manual documentation sufficient initially
- [ ] Configuration Merge Strategies — Address when conflicts actually arise

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| File Discovery & Inventory | HIGH | LOW | P1 |
| Git Config Extraction | HIGH | LOW | P1 |
| Secret Detection & Separation | HIGH | MEDIUM | P1 |
| Corporate Artifact Filtering | HIGH | MEDIUM | P1 |
| ~/bin Script Migration | HIGH | LOW | P1 |
| SSH Config Migration | HIGH | LOW | P1 |
| Module-Based Organization | HIGH | MEDIUM | P1 |
| Audit Trail Documentation | MEDIUM | LOW | P1 |
| Idempotent Ansible Playbooks | HIGH | MEDIUM | P2 |
| Diff Visibility | MEDIUM | LOW | P2 |
| Backup & Rollback | HIGH | MEDIUM | P2 |
| Configuration Diff Reports | MEDIUM | MEDIUM | P2 |
| Missing App Module Detection | MEDIUM | MEDIUM | P2 |
| Shell Config Gap Analysis | MEDIUM | MEDIUM | P2 |
| Credential Helper Validation | MEDIUM | LOW | P2 |
| Pre-commit Hook Integration | MEDIUM | LOW | P2 |
| Automated Testing in Containers | MEDIUM | HIGH | P3 |
| Multi-Machine Config Variants | LOW | MEDIUM | P3 |
| Dependency Graph Visualization | LOW | MEDIUM | P3 |
| Configuration Merge Strategies | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for audit phase completion (discovering and documenting what exists)
- P2: Should have for migration phase (translating to Ansible, validating correctness)
- P3: Nice to have for enhancement phase (long-term maintainability, multi-machine)

## Audit vs Migration Feature Split

### Audit Phase (Discovery & Documentation)
**Goal:** Safely capture what exists on old laptop without modifying anything.

**Features:**
- File Discovery & Inventory
- Git Config Extraction
- Secret Detection & Separation
- Corporate Artifact Filtering
- ~/bin Script Migration
- SSH Config Migration
- Audit Trail Documentation

**Output:** Documented inventory of configs, scripts, and patterns ready for Ansible translation.

### Migration Phase (Ansible Translation & Validation)
**Goal:** Convert inventory into idempotent Ansible modules and validate correctness.

**Features:**
- Module-Based Organization
- Idempotent Ansible Playbooks
- Diff Visibility
- Backup & Rollback
- Configuration Diff Reports
- Missing App Module Detection
- Shell Config Gap Analysis
- Credential Helper Validation
- Pre-commit Hook Integration

**Output:** Working Ansible-based dotfiles repo that reproduces personal configs.

### Enhancement Phase (Robustness & Scale)
**Goal:** Add testing, multi-machine support, and long-term maintainability features.

**Features:**
- Automated Testing in Containers
- Multi-Machine Config Variants
- Dependency Graph Visualization
- Configuration Merge Strategies

**Output:** Production-quality dotfiles system ready for multiple machines and years of use.

## Domain-Specific Patterns

### Git Configuration Audit Patterns
Based on [Git configurations in a code audit](https://some-natalie.dev/blog/git-config-audits/):

**Critical Git Config Areas:**
- Identity (user.name, user.email, user.signingkey)
- Signing (commit.gpgsign, gpg.program, gpg.ssh.allowedSignersFile)
- Credential helpers (credential.helper, includeIf for context-specific credentials)
- Diff tools (diff.tool, merge.tool, difftool/mergetool configs)
- Aliases (custom workflows encoded as git aliases)
- Hooks directory (core.hooksPath if using shared hooks)
- SSH configuration (core.sshCommand for custom SSH behavior)

**Audit Considerations:**
- Cannot rely on system configuration to meet audit controls
- Git config can reference executable hooks (security concern)
- includeIf directives may reference corporate repos (exclude these)

### Secret Detection Patterns
Based on [Connecting the .dotfiles: Checked-In Secret](https://pure.mpg.de/rest/items/item_3505626/component/file_3505627/content) research showing 124,230 dotfiles repos with leaked secrets:

**Detection Strategies:**
- Pre-commit hooks with Gitleaks or similar scanning
- Pattern matching for: API keys, tokens, passwords, private keys
- Git smudge/clean filters for transparent encryption (use cautiously)
- .gitignore for sensitive directories (.ssh/, .gnupg/)
- Password manager integration (1Password) for runtime secret injection

**Storage Patterns:**
- Secrets never in repo (even encrypted)
- 1Password references in configs
- Environment variables sourced from 1Password at shell init
- SSH keys stay local (never migrate, regenerate)

### Ansible Idempotency Testing Patterns
Based on [Automated and Tested Dotfile Deployment Using Ansible and Docker](https://bananamafia.dev/post/dotfile-deployment/):

**Testing Approach:**
- Run playbook in container twice
- Second run should show 0 changes (all "ok", no "changed")
- Use Podman/Docker for isolated test environment
- Test with minimal base image (simulates fresh machine)

**Idempotency Requirements:**
- Use Ansible modules (not raw shell commands) for state checking
- Check file existence before copying
- Check package installation before installing
- Use `creates:` parameter for command tasks
- Template tasks should be truly idempotent

### Module Organization Patterns
Based on existing dotfiles repo and [ansible-role-dotmodules](https://github.com/geerlingguy/ansible-role-dotfiles):

**Module Structure:**
```
module-name/
├── config.yml          # Homebrew packages, stow dirs, dependencies
└── files/              # Actual dotfiles
    ├── .config/        # XDG config directory files
    ├── .local/bin/     # User scripts
    └── .*              # Traditional dotfiles
```

**Configuration Aggregation:**
- Each module declares dependencies (Homebrew packages, taps, casks)
- Role aggregates across all enabled modules
- Single Homebrew install with deduplicated package list
- GNU Stow deploys all files/ directories

**Conflict Resolution:**
- Later modules override earlier modules (order matters)
- Use includeIf in git config for module-specific overrides
- Document conflicts in module config.yml

## Sources

**Dotfiles Management Best Practices:**
- [How to Store Dotfiles - Atlassian Git Tutorial](https://www.atlassian.com/git/tutorials/dotfiles)
- [GitHub does dotfiles - dotfiles.github.io](https://dotfiles.github.io/)
- [Exploring Tools For Managing Your Dotfiles](https://gbergatto.github.io/posts/tools-managing-dotfiles/)
- [The Ultimate Guide to Mastering Dotfiles](https://www.daytona.io/dotfiles/ultimate-guide-to-dotfiles)

**Ansible for Dotfiles:**
- [Ansible for dotfiles: the introduction I wish I've had](https://phelipetls.github.io/posts/introduction-to-ansible/)
- [GitHub - geerlingguy/ansible-role-dotfiles](https://github.com/geerlingguy/ansible-role-dotfiles)
- [Automated and Tested Dotfile Deployment Using Ansible and Docker](https://bananamafia.dev/post/dotfile-deployment/)
- [Managing Dotfiles with Ansible | The Broken Link](https://thebroken.link/managing-dotfiles-with-ansible/)

**Dotfiles Audit Tools:**
- [chezmoi](https://www.chezmoi.io/) - 17,876 stars, secret management, templating
- [yadm](https://yadm.io/) - 6,145 stars, encryption, system-specific alternates
- [Dotbot](https://github.com/anishathalye/dotbot) - 7,789 stars, lightweight bootstrapping

**Security & Secrets Management:**
- [Organizing your dotfiles — managing secrets](https://medium.com/@htoopyaelwin/organizing-your-dotfiles-managing-secrets-8fd33f06f9bf)
- [Connecting the .dotfiles: Checked-In Secret](https://pure.mpg.de/rest/items/item_3505626/component/file_3505627/content) - Research on 124,230 repos
- [dotfiles/docs/explanations/security.md](https://github.com/RickCogley/dotfiles/blob/main/docs/explanations/security.md)
- [Why Your Public Dotfiles are a Security Minefield](https://medium.com/@instatunnel/why-your-public-dotfiles-are-a-security-minefield-fc9bdff62403)

**Git Configuration Auditing:**
- [Git configurations in a code audit](https://some-natalie.dev/blog/git-config-audits/)
- [Git - git-config Documentation](https://git-scm.com/docs/git-config)

**Idempotency & Testing:**
- [GitHub - shricodev/dotfiles - Fully automated with Docker testing](https://github.com/shricodev/dotfiles)
- [Writing Idempotent Tasks in Ansible](https://reintech.io/blog/writing-idempotent-tasks-in-ansible)
- [GitHub - rudenkornk/dotfiles - Ansible idempotent playbooks](https://github.com/rudenkornk/dotfiles)

---
*Feature research for: Dotfiles Audit & Ansible Migration*
*Researched: 2026-02-11*
*Confidence: MEDIUM - Based on WebSearch verified with multiple sources and official documentation; no Context7 or single-source official docs available for domain patterns*
