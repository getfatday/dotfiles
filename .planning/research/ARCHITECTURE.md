# Architecture Research

**Domain:** Ansible-based macOS dotfiles management with audit & migration
**Researched:** 2026-02-11
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AUDIT LAYER                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                 │
│  │  Discovery │  │  Extraction│  │   Diff     │                 │
│  │   Scripts  │  │   Scripts  │  │  Analysis  │                 │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                 │
│        │                │                │                        │
│        └────────────────┴────────────────┘                        │
│                         │                                         │
├─────────────────────────┼─────────────────────────────────────────┤
│                   MODULE LAYER                                    │
│  ┌──────────────────────┴────────────────────────┐               │
│  │   Module Directory (modules/)                 │               │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐      │               │
│  │   │  git/   │  │  zsh/   │  │  node/  │      │               │
│  │   │config.yml│  │config.yml│  │config.yml│   │               │
│  │   │ files/  │  │ files/  │  │ files/  │      │               │
│  │   └─────────┘  └─────────┘  └─────────┘      │               │
│  └───────────────────┬───────────────────────────┘               │
│                      │                                            │
├──────────────────────┼────────────────────────────────────────────┤
│               ORCHESTRATION LAYER                                 │
│  ┌───────────────────┴───────────────────┐                       │
│  │  ansible-role-dotmodules              │                       │
│  │  • Module Discovery                   │                       │
│  │  • Config Aggregation                 │                       │
│  │  • Merge Strategy Resolution          │                       │
│  └───────────┬───────────────────────────┘                       │
│              │                                                    │
├──────────────┼────────────────────────────────────────────────────┤
│         DEPLOYMENT LAYER                                          │
│  ┌───────────┴────────────┬──────────────┬──────────────┐        │
│  │                        │              │              │        │
│  │   GNU Stow             │  Homebrew    │  File Merge  │        │
│  │   (Symlink mgmt)       │  (Packages)  │  (config.yml)│        │
│  │                        │              │              │        │
│  └────────────────────────┴──────────────┴──────────────┘        │
│                           │                                       │
├───────────────────────────┼───────────────────────────────────────┤
│                      TARGET SYSTEM                                │
│  ┌────────────────────────┴──────────────────────────┐           │
│  │   $HOME/                                           │           │
│  │   • .gitconfig (symlink → .dotmodules/git/.gitconfig)│        │
│  │   • .zshrc (merged from multiple modules)          │           │
│  │   • .local/bin/ (symlink → .dotmodules/*/files/.local/bin/)│  │
│  └────────────────────────────────────────────────────┘           │
└───────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Discovery Scripts** | Audit old machine, identify installed packages/configs | Bash scripts using `brew list`, `find`, `diff` |
| **Extraction Scripts** | Copy relevant files from old machine to staging area | `rsync`, `cp` with filtering for corporate/sensitive data |
| **Diff Analysis** | Compare old configs vs current repo, identify gaps | `git diff`, custom comparison scripts |
| **Module Directory** | Self-contained config units with dependencies | Directory with `config.yml` + `files/` subdirectory |
| **ansible-role-dotmodules** | Orchestrates module processing, resolves conflicts | Ansible role with tasks for discovery, aggregation, deployment |
| **GNU Stow** | Creates symlinks from dotfiles to home directory | Standard stow package manager |
| **Homebrew Integration** | Installs packages, casks, taps defined in modules | `community.general.homebrew` Ansible module |
| **File Merge** | Combines files from multiple modules (e.g., .zshrc) | Custom Ansible logic with section delimiters |

## Recommended Project Structure

```
dotfiles/
├── .planning/              # Research, roadmap, phase specs
│   ├── research/           # Domain research outputs
│   └── roadmap/            # Phase definitions
├── modules/                # Dotfile modules (managed by stow)
│   ├── git/
│   │   ├── config.yml      # Module dependencies & settings
│   │   └── files/
│   │       ├── .gitconfig
│   │       └── .local/bin/ # Git helper scripts
│   ├── zsh/
│   │   ├── config.yml
│   │   └── files/
│   │       ├── .zshrc
│   │       └── .zpreztorc
│   └── bin/                # Standalone scripts module
│       ├── config.yml
│       └── files/
│           └── .local/bin/
├── playbooks/
│   ├── deploy.yml          # Main deployment playbook
│   ├── audit.yml           # NEW: Audit old machine
│   └── migrate.yml         # NEW: Extract & update from audit
├── scripts/                # NEW: Audit & migration utilities
│   ├── audit/
│   │   ├── discover-packages.sh      # Generate Brewfile from old machine
│   │   ├── discover-dotfiles.sh      # Find all dotfiles
│   │   └── diff-configs.sh           # Compare old vs current
│   ├── migrate/
│   │   ├── extract-configs.sh        # Copy files from old machine
│   │   ├── filter-corporate.sh       # Remove work-specific content
│   │   └── update-modules.sh         # Update repo modules
│   └── lib/
│       └── helpers.sh                # Shared utility functions
├── temp/                   # NEW: Temporary extraction/staging
│   ├── old-machine/        # Mounted old laptop or extracted files
│   ├── audit-results/      # Discovery outputs
│   └── staging/            # Filtered configs ready for integration
├── requirements.yml        # Ansible role/collection dependencies
├── ansible.cfg             # Ansible configuration
└── README.md
```

### Structure Rationale

- **modules/:** Each module is self-contained with its own dependencies (Homebrew packages, casks) and files. This mirrors the modular philosophy of GNU Stow where each subdirectory is a "package."

- **playbooks/:** Separates audit (read-only discovery) from migration (write operations) from deploy (apply to new machine). This phase separation prevents accidental data loss.

- **scripts/:** External to Ansible for flexibility. Audit scripts can run without Ansible installed on old machine. Can be executed independently or called from playbooks.

- **temp/:** Explicitly gitignored staging area for messy extraction work. Keeps the repo clean while providing workspace for filtering corporate configs.

- **.planning/:** GSD-compatible project management structure for spec-driven development.

## Architectural Patterns

### Pattern 1: Module-Based Organization

**What:** Each concern (git, zsh, node, editor) is a separate module directory with `config.yml` declaring dependencies and `files/` containing actual dotfiles.

**When to use:** Always. This is the core organizational pattern.

**Trade-offs:**
- **Pros:** Highly modular, can selectively install/uninstall, clear dependency boundaries, easy to share modules across machines
- **Cons:** More directories than flat structure, requires understanding stow's directory mapping

**Example:**
```yaml
# modules/git/config.yml
homebrew_packages:
  - git
  - git-delta
  - gh

homebrew_casks:
  - kdiff3

stow_dirs:
  - git

mergeable_files:
  - ".zshrc"  # Git aliases contribute to shared .zshrc
```

### Pattern 2: Separation of Audit and Migration

**What:** Audit scripts (read-only) run on old machine to discover state. Migration scripts process audit results and update repo. Deploy playbook applies repo to new machine.

**When to use:** Any time migrating from existing machine to dotfiles repo.

**Trade-offs:**
- **Pros:** Safe (audit can't break old machine), repeatable (can re-run audit), clear phase boundaries
- **Cons:** Multi-step process, requires discipline to not skip audit phase

**Example workflow:**
```bash
# Phase 1: Audit old machine
./scripts/audit/discover-packages.sh /Volumes/Macintosh\ HD-1 > temp/audit-results/Brewfile.old
./scripts/audit/discover-dotfiles.sh /Volumes/Macintosh\ HD-1/Users/ianderson > temp/audit-results/dotfiles.list

# Phase 2: Migration (on new machine, with old mounted)
./scripts/migrate/extract-configs.sh /Volumes/Macintosh\ HD-1/Users/ianderson temp/old-machine/
./scripts/migrate/filter-corporate.sh temp/old-machine/ temp/staging/
./scripts/migrate/update-modules.sh temp/staging/ modules/

# Phase 3: Deploy to new machine
ansible-playbook playbooks/deploy.yml
```

### Pattern 3: Multi-Strategy File Deployment

**What:** ansible-role-dotmodules supports two deployment strategies that can be used together:
1. **Stow strategy:** Symlink entire directory trees (files/ → $HOME/)
2. **Merge strategy:** Combine same-named files from multiple modules with section delimiters

**When to use:**
- **Stow:** For files owned by single module (`.gitconfig`, `.vimrc`)
- **Merge:** For files contributed to by multiple modules (`.zshrc` receives git aliases, node paths, python venvs)

**Trade-offs:**
- **Pros:** Flexibility to share files (like .zshrc) across modules while keeping module separation
- **Cons:** Complexity in understanding which files are merged vs stowed; conflicts must be manually resolved

**Example:**
```yaml
# modules/git/config.yml
stow_dirs:
  - git
mergeable_files:
  - ".zshrc"  # Contribute git section to shared .zshrc

# modules/zsh/config.yml
stow_dirs:
  - zsh
mergeable_files:
  - ".zshrc"  # Contribute zsh section to shared .zshrc

# Result: $HOME/.zshrc is a merged file with:
# ===== Module: git =====
# [git aliases and functions]
# ===== Module: zsh =====
# [zsh configuration]
```

### Pattern 4: Secrets in 1Password, Not Repo

**What:** Private information (work email, API keys, etc.) stored in 1Password, referenced from configs but not committed to public repo.

**When to use:** Always for public repos; strongly recommended even for private repos.

**Trade-offs:**
- **Pros:** Safe to publish repo publicly, follows security best practices, centralized secret management
- **Cons:** Requires 1Password CLI setup, some manual steps for secret injection

**Example:**
```bash
# In .gitconfig template (committed to repo)
[user]
    name = Ian Anderson
    email = PLACEHOLDER_EMAIL  # Real email in 1Password

# In setup script or Ansible task (not committed)
op read "op://Personal/GitHub/email" | sed -i '' "s/PLACEHOLDER_EMAIL/$EMAIL/" ~/.gitconfig
```

### Pattern 5: Homebrew Bundle for Package Audit

**What:** Use `brew bundle dump` to generate Brewfile from installed packages on old machine, compare with modules' `homebrew_packages` declarations.

**When to use:** During audit phase to discover what was installed that might not be in the repo yet.

**Trade-offs:**
- **Pros:** Comprehensive package inventory, official Homebrew tool, includes casks and taps
- **Cons:** Includes dependencies (not just explicitly installed), may need filtering

**Example:**
```bash
# On old machine (or mounted old machine with homebrew intact)
brew bundle dump --file=temp/audit-results/Brewfile.old --describe --force

# Compare with current modules
cat modules/*/config.yml | grep -A 100 "homebrew_packages:" | sort | uniq > temp/current-packages.txt
cat temp/audit-results/Brewfile.old | grep "^brew " | sort > temp/old-packages.txt
diff temp/current-packages.txt temp/old-packages.txt
```

## Data Flow

### Audit → Migrate → Deploy Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         OLD MACHINE                              │
│  /Volumes/Macintosh HD-1/Users/ianderson/                        │
│    ├── .gitconfig                                                │
│    ├── .zshrc                                                    │
│    ├── .local/bin/custom-script                                 │
│    └── brew list output                                         │
└────────────────┬────────────────────────────────────────────────┘
                 │ (audit scripts - read-only)
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                   AUDIT RESULTS (temp/)                          │
│  temp/audit-results/                                             │
│    ├── Brewfile.old                                             │
│    ├── dotfiles.list                                            │
│    └── config-diffs.txt                                         │
└────────────────┬────────────────────────────────────────────────┘
                 │ (extract-configs.sh)
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                 EXTRACTED CONFIGS (temp/)                        │
│  temp/old-machine/                                               │
│    ├── .gitconfig (with work email)                             │
│    ├── .zshrc (with corporate paths)                            │
│    └── .local/bin/ (with proprietary scripts)                   │
└────────────────┬────────────────────────────────────────────────┘
                 │ (filter-corporate.sh)
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                FILTERED CONFIGS (temp/)                          │
│  temp/staging/                                                   │
│    ├── .gitconfig (PLACEHOLDER_EMAIL)                           │
│    ├── .zshrc (cleaned)                                         │
│    └── .local/bin/ (safe scripts only)                          │
└────────────────┬────────────────────────────────────────────────┘
                 │ (update-modules.sh - manual review + commit)
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MODULES (modules/)                            │
│  modules/git/files/.gitconfig                                    │
│  modules/zsh/files/.zshrc                                        │
│  modules/bin/files/.local/bin/                                  │
│  (version controlled, public repo safe)                         │
└────────────────┬────────────────────────────────────────────────┘
                 │ (ansible-playbook playbooks/deploy.yml)
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│            ANSIBLE ORCHESTRATION                                 │
│  1. ansible-role-dotmodules discovers modules                    │
│  2. Aggregates all config.yml declarations                       │
│  3. Resolves merge vs stow strategies                            │
│  4. Installs Homebrew packages (brew, mas)                       │
│  5. GNU Stow deploys files/ → $HOME/                             │
│  6. Merges .zshrc from multiple modules                          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                      NEW MACHINE                                 │
│  $HOME/                                                          │
│    ├── .gitconfig → .dotmodules/git/files/.gitconfig (symlink)  │
│    ├── .zshrc (merged file from git + zsh + node modules)       │
│    └── .local/bin/custom-script → .dotmodules/bin/files/... │   │
│  Applications installed via Homebrew                             │
└─────────────────────────────────────────────────────────────────┘
```

### Homebrew Package Flow

```
Module config.yml declarations
    ↓
homebrew_packages: [git, gh, ripgrep]
homebrew_casks: [iterm2, visual-studio-code]
homebrew_taps: [homebrew/cask-fonts]
mas_installed_apps: [497799835]  # Xcode
    ↓
ansible-role-dotmodules aggregates all modules
    ↓
community.general.homebrew module
community.general.homebrew_cask module
geerlingguy.mac.mas module (if available)
    ↓
Packages installed on target system
```

### GNU Stow Symlink Flow

```
modules/git/files/.gitconfig
    ↓
stow_dirs: [git] declared in config.yml
    ↓
ansible-role-dotmodules executes: stow -d $dest -t $HOME git
    ↓
$HOME/.gitconfig → $dest/git/files/.gitconfig (symlink created)
```

### Config Merge Flow

```
modules/git/files/.zshrc (git aliases)
modules/zsh/files/.zshrc (zsh config)
modules/node/files/.zshrc (node paths)
    ↓
mergeable_files: [".zshrc"] in each config.yml
    ↓
ansible-role-dotmodules detects shared file
    ↓
Combines with section markers:
===== Module: git =====
[git content]
===== Module: zsh =====
[zsh content]
===== Module: node =====
[node content]
    ↓
$HOME/.zshrc (merged file, not symlink)
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **Single machine (current state)** | Simple playbooks/deploy.yml, manual execution, all modules installed together |
| **Multiple personal machines (2-5)** | Add host-specific playbooks or group_vars, conditional module installation (desktop vs laptop), use tags for selective deployment |
| **Team sharing dotfiles (5-20 users)** | Abstract personal info to variables, provide example/template configs, document customization points, consider host-specific roles |
| **Organization-wide (20+ users)** | Split into base/optional modules, add role for organization defaults, use Ansible inventory/group_vars for user customization, consider Ansible Tower/AWX for orchestration |

### Scaling Priorities

1. **First bottleneck:** Manual execution on each machine. **Fix:** Add bootstrap script that installs Ansible and runs deploy playbook. Create `curl | bash` one-liner for fresh machine setup.

2. **Second bottleneck:** Conflicting preferences between machines (desktop has Docker, laptop doesn't). **Fix:** Use Ansible facts and conditionals in playbooks, or separate into machine-specific playbooks (playbooks/deploy-desktop.yml, playbooks/deploy-laptop.yml).

3. **Third bottleneck:** Secrets management across multiple machines/users. **Fix:** Standardize on secret provider (1Password, Bitwarden, Ansible Vault), create wrapper playbook that injects secrets after deployment.

## Anti-Patterns

### Anti-Pattern 1: Committing Secrets to Repo

**What people do:** Commit `.gitconfig` with real work email, API keys in `.zshrc`, SSH keys in repo

**Why it's wrong:**
- Exposes private information if repo becomes public
- Can't share repo safely with others
- Violates security best practices
- Corporate secrets may violate employment agreements

**Do this instead:**
- Use placeholders (PLACEHOLDER_EMAIL) in committed configs
- Store actual secrets in 1Password, inject during deployment
- Use `.gitignore` for any local-only configs (e.g., `.gitconfig.local` for machine-specific settings)
- Add `.env` files to `.gitignore` by default

### Anti-Pattern 2: Direct Migration Without Audit

**What people do:** `rsync -av /Volumes/old-machine/Users/me/ ~/` or manually copy configs directly into modules without review

**Why it's wrong:**
- Brings corporate/proprietary scripts into public repo
- Copies deprecated configs you no longer need
- Misses opportunity to clean up accumulated cruft
- May overwrite good new configs with old bad ones
- No record of what was changed

**Do this instead:**
- Run audit scripts first to inventory what exists
- Extract to temporary staging area
- Review and filter before committing to modules
- Use diff tools to compare old vs current configs
- Document decisions about what to keep/discard

### Anti-Pattern 3: Monolithic .zshrc/.bashrc

**What people do:** Put all shell config in single massive `.zshrc` file with git, node, python, docker, work-specific, etc. all mixed together

**Why it's wrong:**
- Can't selectively disable sections
- Hard to understand what depends on what
- Difficult to share modules (git config mixed with proprietary tools)
- Breaks modularity principle

**Do this instead:**
- Split into modules that contribute sections via `mergeable_files`
- Each module owns its domain (git module provides git aliases, node module provides node paths)
- ansible-role-dotmodules merges them with clear section delimiters
- Can disable entire module by removing from playbook install list

### Anti-Pattern 4: Homebrew Package Duplication

**What people do:** Declare `git` in multiple module config.yml files, or manually run `brew install` outside of playbook

**Why it's wrong:**
- Duplication makes it unclear which module owns the dependency
- Manual brew installs not tracked in repo, drift between machines
- Slows down playbook (Homebrew checks if already installed, but still overhead)

**Do this instead:**
- Each package declared in exactly one module's config.yml (DRY principle)
- Choose the most semantically appropriate module (git in git module, node in node module)
- For shared dependencies (e.g., jq used by multiple modules), create a utilities/common module
- Never run `brew install` manually; always add to module config.yml and re-run playbook

### Anti-Pattern 5: Conflicting Stow and Merge Strategies

**What people do:** Declare same file in both `stow_dirs` and `mergeable_files`, leading to conflicts where stow tries to symlink a file that merge wants to create

**Why it's wrong:**
- ansible-role-dotmodules will error on strategy conflicts
- Results in deployment failure
- Unclear which strategy should win

**Do this instead:**
- Decide per-file: single-owner files use stow, multi-contributor files use merge
- Document in module config.yml why a file is mergeable vs stowed
- If a file needs to be shared, explicitly mark as `mergeable_files` in all contributing modules
- Review ansible-role-dotmodules error messages for strategy conflicts and resolve intentionally

### Anti-Pattern 6: Skipping the Temp Directory

**What people do:** Edit modules directly from old machine files, committing without filtering

**Why it's wrong:**
- Risk of committing secrets/corporate content
- No staging area for review
- Can't easily revert if mistake discovered later
- Loses the safety net of temp/staging workflow

**Do this instead:**
- Always extract to `temp/old-machine/` first (gitignored)
- Run filtering scripts to clean corporate content → `temp/staging/`
- Manually review staging area before updating modules
- Only copy from staging to modules after verification
- Can nuke temp/ and start over if needed without affecting repo

## Integration Points

### External Dependencies

| Dependency | Integration Pattern | Notes |
|---------|---------------------|-------|
| **ansible-role-dotmodules** | Ansible Galaxy role installed via requirements.yml | Core orchestration engine, handles module discovery and deployment |
| **geerlingguy.mac collection** | Ansible Galaxy collection for macOS-specific tasks | Provides Homebrew and MAS integration |
| **GNU Stow** | System package, installed via Homebrew in playbook | Creates symlinks from dotfiles to $HOME |
| **Homebrew** | macOS package manager, assumed pre-installed or installed in bootstrap | Required for all package installations |
| **1Password CLI** | Optional, for secret injection | Needed if using 1Password pattern for secrets |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Audit scripts ↔ Ansible playbooks** | File-based (audit writes to temp/, playbooks read from temp/) | Audit can run standalone or be called from playbook |
| **Migration scripts ↔ Modules** | File copy from temp/staging/ to modules/*/files/ | Manual step with review, not automated to prevent accidents |
| **Modules ↔ ansible-role-dotmodules** | config.yml declarations read by role | Role discovers modules by scanning directories |
| **ansible-role-dotmodules ↔ Stow** | Shell commands executed by Ansible tasks | Role calls `stow -d <dest> -t $HOME <module>` |
| **ansible-role-dotmodules ↔ Homebrew** | Ansible modules (community.general.homebrew) | Role aggregates packages then installs in batch |
| **Deployed configs ↔ 1Password** | Secrets injected post-deployment via 1Password CLI or Ansible tasks | Separate step after initial stow/merge |

## Build Order for Audit → Migrate Workflow

### Phase 1: Audit (Read-Only)

**Goal:** Discover what exists on old machine without modifying anything

**Components to build:**
1. `scripts/audit/discover-packages.sh` - Generate Brewfile from `brew list`
2. `scripts/audit/discover-dotfiles.sh` - Find all dotfiles in old home directory
3. `scripts/audit/diff-configs.sh` - Compare old vs current repo configs
4. `playbooks/audit.yml` - Optional Ansible wrapper (can run scripts directly)

**Dependencies:** None (can run on old machine with just bash)

**Output:** Files in `temp/audit-results/` (Brewfile.old, dotfiles.list, diffs.txt)

### Phase 2: Extraction (Selective Copy)

**Goal:** Copy relevant files from old machine to temp staging

**Components to build:**
1. `scripts/migrate/extract-configs.sh` - rsync dotfiles from old machine to temp/old-machine/
2. `scripts/migrate/extract-bins.sh` - Copy ~/bin/ and ~/.local/bin/ scripts

**Dependencies:**
- Phase 1 audit results (dotfiles.list guides what to extract)
- Old machine mounted at known path

**Output:** Files in `temp/old-machine/` (raw copy, not filtered)

### Phase 3: Filtering (Corporate/Sensitive Removal)

**Goal:** Clean extracted configs for public repo safety

**Components to build:**
1. `scripts/migrate/filter-corporate.sh` - Remove work emails, corporate paths, proprietary tools
2. `scripts/migrate/filter-secrets.sh` - Replace API keys/passwords with placeholders
3. `scripts/lib/helpers.sh` - Shared filtering utilities (detect secrets, anonymize)

**Dependencies:**
- Phase 2 extraction results (temp/old-machine/)
- Filtering rules/patterns (hardcoded or config file)

**Output:** Files in `temp/staging/` (cleaned, ready for manual review)

### Phase 4: Module Update (Manual Integration)

**Goal:** Integrate staging area into modules after review

**Components to build:**
1. `scripts/migrate/update-modules.sh` - Helper to copy staging files to modules
2. Manual review checklist (document in .planning/research/PITFALLS.md)

**Dependencies:**
- Phase 3 filtered configs (temp/staging/)
- Existing module structure (modules/*/files/)
- Human review (cannot be fully automated)

**Output:** Updated modules/*/files/ directories, git commits

### Phase 5: Deployment (Apply to New Machine)

**Goal:** Deploy updated modules to current/new machine

**Components already exist:**
1. `playbooks/deploy.yml` - Main deployment playbook (already implemented)
2. `ansible-role-dotmodules` - Orchestration (already installed)

**Dependencies:**
- Phase 4 module updates committed to repo
- Ansible and requirements.yml roles installed
- Homebrew installed on target machine

**Output:** Configured $HOME with symlinks, merged configs, installed packages

### Recommended Build Order (Dependencies First)

```
1. scripts/lib/helpers.sh              # No dependencies, used by all others
2. scripts/audit/discover-packages.sh  # Independent, can run standalone
3. scripts/audit/discover-dotfiles.sh  # Independent
4. scripts/audit/diff-configs.sh       # Depends on existing repo
5. scripts/migrate/extract-configs.sh  # Depends on audit results
6. scripts/migrate/filter-corporate.sh # Depends on lib/helpers.sh
7. scripts/migrate/update-modules.sh   # Depends on filtered staging
8. Test audit → extract → filter flow  # Integration test
9. Manual review & module update       # Human-in-loop validation
10. Run playbooks/deploy.yml            # Already exists, final deployment
```

**Rationale for this order:**
- Helpers first (shared utilities)
- Audit scripts next (read-only, safe to run/test)
- Extraction after audit (needs audit results)
- Filtering after extraction (needs extracted files)
- Update scripts last (needs filtered files)
- Manual review before deployment (safety gate)

**Parallel work opportunities:**
- Audit scripts can be built in parallel (no dependencies on each other)
- While building scripts, can manually explore old machine to inform filtering rules
- Can update existing modules independently of migration work

## Sources

### Official Documentation
- [Homebrew Bundle and Brewfile Documentation](https://docs.brew.sh/Brew-Bundle-and-Brewfile) - Official guide to `brew bundle dump` and Brewfile management
- [Ansible Homebrew Module](https://docs.ansible.com/projects/ansible/latest/collections/community/general/homebrew_module.html) - Official Ansible module for Homebrew integration

### Architecture Patterns
- [Ansible for dotfiles: the introduction I wish I've had](https://phelipetls.github.io/posts/introduction-to-ansible/) - Comprehensive guide to Ansible dotfiles architecture
- [Managing Dotfiles with Ansible | The Broken Link](https://thebroken.link/managing-dotfiles-with-ansible/) - Best practices for role-based organization
- [Automated and Tested Dotfile Deployment Using Ansible and Docker](https://bananamafia.dev/post/dotfile-deployment/) - Testing strategies and deployment patterns

### GNU Stow Patterns
- [Using GNU Stow to manage your dotfiles](https://gist.github.com/andreibosco/cb8506780d0942a712fc) - Core Stow workflow and directory structure
- [Managing Dotfiles with GNU Stow](https://medium.com/quick-programming/managing-dotfiles-with-gnu-stow-9b04c155ebad) - Best practices for Stow-based management
- [How I manage my dotfiles using GNU Stow](https://tamerlan.dev/how-i-manage-my-dotfiles-using-gnu-stow/) - Real-world Stow workflow

### Migration & Backup
- [Dotfiles for Developers - Part 2: Backup/Restore macOS System Dotfiles](https://leeked.medium.com/dotfiles-for-developers-part-2-2c02029f771e) - Strategies for backing up before migration
- [Setting Up a New Mac with Dotfiles, Brew Bundle, and Mackup](https://respawn.io/posts/dotfiles-brew-bundle-and-mackup) - Using Mackup for app-specific backups
- [Automating macOS Setup and Backups with Homebrew, Dotfiles, and Bootstrap Scripts](https://zaclohrenz.com/posts/macos-setup/) - Comprehensive backup and bootstrap workflow

### Reference Implementations
- [ansible-role-dotmodules](https://github.com/getfatday/ansible-role-dotmodules) - The actual role used in this repo (architecture analyzed via WebFetch)
- [geerlingguy/ansible-role-dotfiles](https://github.com/geerlingguy/ansible-role-dotfiles) - Alternative simple clone-and-link approach
- [sloria/dotfiles](https://github.com/sloria/dotfiles) - Example of role-based Ansible dotfiles (analyzed via WebFetch)
- [frdmn/dotfiles](https://github.com/frdmn/dotfiles) - macOS-specific Ansible dotfiles implementation

---
*Architecture research for: Ansible-based macOS dotfiles management with audit & migration*
*Researched: 2026-02-11*
