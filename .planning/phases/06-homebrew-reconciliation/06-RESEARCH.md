# Phase 6: Homebrew Reconciliation - Research

**Researched:** 2026-02-12
**Domain:** Homebrew package management and declarative configuration
**Confidence:** HIGH

## Summary

This phase focuses on ensuring all personal Homebrew packages are declared in module `config.yml` files while excluding corporate packages and understanding dependency management. The dotfiles system uses `ansible-role-dotmodules` which installs packages directly from module configurations rather than generating Brewfiles. However, the phase should generate a canonical Brewfile for reference and future migration scenarios.

The current system has 122 installed formulas but only declares ~20 top-level packages across modules. Analysis shows 101 packages are missing from module declarations, but most are dependencies (auto-installed by Homebrew). Using `brew leaves` reveals only 37 top-level packages, of which 18 are undeclared and need evaluation for inclusion.

**Primary recommendation:** Focus on `brew leaves` output to identify explicitly installed packages, categorize as personal vs corporate vs dependencies, then add personal packages to appropriate module `config.yml` files. Generate a reference Brewfile but don't change the ansible-role-dotmodules workflow.

## Standard Stack

### Core Tools
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Homebrew | 5.0.0+ | Package manager for macOS | De facto standard for macOS development |
| brew bundle | built-in | Brewfile management | Official Homebrew tool for declarative config |
| ansible-role-dotmodules | current | Module-based dotfile management | Project's chosen architecture |

### Supporting Tools
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| brew leaves | built-in | List top-level packages | Identifying explicitly installed packages |
| brew deps --tree | built-in | Show dependency graph | Understanding package relationships |
| brew bundle dump | built-in | Generate Brewfile from installed | Creating backup/reference Brewfiles |
| brew uses --installed | built-in | Show what depends on package | Determining if package is dependency |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Module config.yml | Brewfile only | Loses module organization, can't merge configs |
| ansible-role-dotmodules | Direct Brewfile + stow | Simpler but less flexible, no conflict resolution |

**Current Installation Method:**
```yaml
# modules/[name]/config.yml
homebrew_packages:
  - package-name
  - another-package

homebrew_casks:
  - cask-name

homebrew_taps:
  - tap/name
```

## Architecture Patterns

### Recommended Module Organization

Packages should be declared in the module that most logically owns them:

```
modules/
├── git/          # Git-related: git, git-delta, gh, git-flow
├── editor/       # Editors: vim, neovim, emacs
├── node/         # Node ecosystem: node, pnpm, asdf
├── docker/       # Container tools: docker, docker-compose, docker-machine
├── productivity/ # CLI utilities: fzf, autojump, z, jq, wget
├── rust/         # Rust toolchain: rustup-init
├── zsh/          # Shell: zsh, zsh-history-substring-search
└── macos/        # System tools: mas (Mac App Store CLI)
```

### Pattern 1: Top-Level Packages Only

**What:** Only declare packages you explicitly want (top-level), let Homebrew handle dependencies

**When to use:** Always - this is Homebrew's design

**Example:**
```yaml
# modules/editor/config.yml
homebrew_packages:
  - emacs          # Explicitly wanted
  # NOT: gmp, gnutls, tree-sitter (these are emacs dependencies)
```

**Rationale:** Homebrew automatically installs and manages dependencies. Declaring dependencies in config.yml is redundant and creates maintenance burden.

### Pattern 2: Taps for Third-Party Packages

**What:** Declare taps when using packages from non-core repositories

**When to use:** When package requires a custom tap

**Example:**
```yaml
# modules/obsidian/config.yml
homebrew_taps:
  - yakitrak/yakitrak

homebrew_packages:
  - yakitrak/yakitrak/obsidian-cli
```

### Pattern 3: Formula vs Cask Distinction

**What:** Use `homebrew_packages` for CLI tools/libraries, `homebrew_casks` for GUI apps

**When to use:** Always - matches Homebrew's architecture

**Example:**
```yaml
# modules/git/config.yml
homebrew_packages:
  - git              # CLI tool (formula)
  - git-delta        # CLI tool (formula)

homebrew_casks:
  - kaleidoscope     # GUI app (cask)
```

### Pattern 4: Module Specificity

**What:** Create focused modules rather than dumping everything in one place

**When to use:** When packages serve distinct purposes

**Example - GOOD:**
```yaml
# modules/productivity/config.yml - Navigation and CLI utilities
homebrew_packages:
  - fzf
  - autojump
  - z
  - jq
  - wget
  - rsync

# modules/media/config.yml - Media processing tools
homebrew_packages:
  - ffmpeg
  - imagemagick
  - streamlink
```

**Example - BAD:**
```yaml
# modules/misc/config.yml - Too broad
homebrew_packages:
  - fzf
  - ffmpeg
  - git
  - docker
  # Everything dumped together - hard to reason about
```

### Anti-Patterns to Avoid

- **Declaring dependencies:** Don't list packages that are only dependencies of other packages
- **Duplicate declarations:** Don't declare same package in multiple modules
- **Overly broad modules:** Avoid "utilities" or "misc" modules that lack clear purpose
- **Missing taps:** Don't forget to declare taps for third-party formulas
- **Mixing concerns:** Don't mix media tools with shell tools in same module

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Package comparison | Shell script to diff packages | `brew leaves`, `brew bundle check` | Built-in, handles edge cases (taps, casks, mas) |
| Brewfile generation | YAML-to-Brewfile converter | `brew bundle dump --describe` | Official tool, handles all package types |
| Dependency detection | Parse `brew list` output | `brew deps --tree`, `brew uses` | Accurate dependency graph |
| Corporate package filtering | Regex on package names | Manual audit + documented exclusion list | Prevents false positives (e.g., "go" is not corporate) |
| Module assignment | Automatic categorization | Human judgment with consistent patterns | Package purpose requires context |

**Key insight:** Homebrew provides comprehensive introspection tools. Use them rather than parsing text output or reverse-engineering package relationships.

## Common Pitfalls

### Pitfall 1: Declaring Dependencies as Top-Level Packages

**What goes wrong:** Module configs fill up with dozens of lib* packages, making it unclear what was explicitly wanted vs auto-installed

**Why it happens:** Running `brew list` shows all packages equally, both top-level and dependencies

**How to avoid:** Always use `brew leaves` to identify top-level packages, then cross-reference with `brew deps` to confirm dependency relationships

**Warning signs:**
- Modules listing many `lib*` packages (libpng, libjpeg, etc.)
- Packages you've never heard of in module configs
- Module configs growing faster than you're installing tools

### Pitfall 2: Missing Taps

**What goes wrong:** Package declaration fails during `ansible-playbook` run because tap wasn't declared

**Why it happens:** Tap is already installed on current machine, so you forget it needs to be declared

**How to avoid:** When adding a non-core package, always check `brew info [package]` to see which tap provides it, then add tap to module config

**Warning signs:**
- Ansible errors like "No available formula with the name 'package'"
- Package installs fine manually but fails in playbook
- Full package name includes slash (e.g., `yakitrak/yakitrak/obsidian-cli`)

**Example:**
```yaml
# WRONG - Will fail on fresh install
homebrew_packages:
  - obsidian-cli

# RIGHT - Declares tap first
homebrew_taps:
  - yakitrak/yakitrak
homebrew_packages:
  - yakitrak/yakitrak/obsidian-cli  # or just obsidian-cli after tap added
```

### Pitfall 3: Corporate Package Inclusion

**What goes wrong:** Corporate-specific tools (Zscaler, Jamf, AWS CLI, Terraform) get committed to public repo

**Why it happens:** Hard to distinguish personal vs corporate CLI tools (both are just packages)

**How to avoid:**
1. Maintain explicit exclusion list (documented in audit)
2. Question any package you only used at previous employer
3. Prefer install-on-demand for specialized tools
4. Document rationale for including infrastructure tools (e.g., "personal projects" vs "only used at work")

**Warning signs:**
- Package names containing company names (expedia, zscaler, jamf)
- SAML/SSO-related tools (saml2aws)
- Enterprise infrastructure tools (teleport, vault, consul) unless you use them personally
- Cloud provider CLIs (awscli, azure-cli) unless you have personal accounts

### Pitfall 4: Formula vs Cask Confusion

**What goes wrong:** Declaring cask in `homebrew_packages` or vice versa, causing install failures

**Why it happens:** Some tools have both versions (e.g., docker has formula and Docker Desktop cask)

**How to avoid:** Use `brew info [name]` to check type - it will show "==> Cask" or "==> Formula" header

**Warning signs:**
- Ansible errors about "not a cask" or "not a formula"
- Installing GUI app but declaring in `homebrew_packages`
- Package has capitalized name (usually indicates cask)

**Example:**
```bash
$ brew info docker
==> docker: 28.0.1 (formula)  # CLI tool - use homebrew_packages

$ brew info --cask docker
==> docker: 4.38.0 (cask)     # Docker Desktop GUI - use homebrew_casks
```

### Pitfall 5: Stale Package Declarations

**What goes wrong:** Declaring packages that are deprecated, renamed, or no longer needed

**Why it happens:** Packages evolve, get renamed, or become unnecessary as tools improve

**How to avoid:**
- Check `brew info` for deprecation warnings
- Review modules periodically for packages you no longer use
- Note when Homebrew suggests alternatives during upgrades

**Warning signs:**
- Brew warnings about "deprecated" or "disabled" formulas
- Multiple packages doing same thing (e.g., `wget` and `curl`)
- Packages you haven't used in 6+ months

**Example from research:**
```
==> memo: 1.0.3
Deprecated because it is not maintained upstream!
# This should NOT be added to modules
```

## Code Examples

Verified patterns from official sources and project:

### Identifying Top-Level Packages
```bash
# List explicitly installed packages (not dependencies)
brew leaves

# Example output:
# ansible
# asdf
# docker
# emacs
# ffmpeg
# ...

# Check if package is top-level or dependency
brew uses --installed [package]
# If output is empty, it's top-level
# If output lists packages, it's a dependency
```

### Checking Package Type and Tap
```bash
# Get package information
brew info [package]

# Example for third-party package:
# ==> yakitrak/yakitrak/obsidian-cli: stable 0.2.3
# https://github.com/Yakitrak/obsidian-cli
# From: https://github.com/yakitrak/homebrew-yakitrak/...
# → Need to add tap: yakitrak/yakitrak

# Example for core package:
# ==> git: stable 2.44.0
# From: https://github.com/Homebrew/homebrew-core/...
# → No tap needed (core)
```

### Module Config Pattern
```yaml
# modules/[category]/config.yml
---
# [Category] module
# [Brief description of purpose]

# [Category] dependencies
homebrew_packages:
  - package-one    # Comment explaining why/what
  - package-two

# Optional: if third-party packages
homebrew_taps:
  - owner/repo

# Optional: GUI applications
homebrew_casks:
  - app-name

# Stow directories
stow_dirs:
  - [category]

# Optional: files that merge with other modules
mergeable_files:
  - ".zshrc"
  - ".zshenv"
```

### Generating Reference Brewfile
```bash
# Generate Brewfile with descriptions
brew bundle dump --describe --force

# Output format:
# # Comment describing package
# brew "package-name"
# cask "app-name"
# tap "owner/repo"
# mas "App Name", id: 123456789
```

### Comparing Installed vs Declared
```bash
# Extract declared packages from all modules
grep -h "^  - " modules/*/config.yml | \
  sed 's/^  - //' | \
  sed 's/ *#.*//' | \
  sort -u > declared.txt

# Get top-level installed packages
brew leaves | sort > installed.txt

# Find installed but not declared
comm -23 installed.txt declared.txt

# Find declared but not installed
comm -13 installed.txt declared.txt
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual package install | Brewfile declarative config | Homebrew Bundle v1.0 (2016) | Reproducible environments |
| Single global Brewfile | Module-based config.yml | ansible-role-dotmodules | Better organization, modularity |
| `brew bundle --global` defaults to `~/.Brewfile` | Defaults to XDG config directory | Homebrew 5.0.0 (2024-11) | Follows XDG standards |
| `homebrew/cask` tap required | Automatically available | Homebrew 4.x (2023) | One less tap to declare |

**Current state (February 2026):**
- Homebrew 5.0.0 is latest major version (released Nov 2024)
- Download concurrency enabled by default
- `brew bundle` paths follow XDG conventions
- No breaking changes expected for this phase

**Deprecated/outdated:**
- Explicit `homebrew/cask` tap declaration (now automatic)
- `homebrew/core` tap declaration (never needed, always available)
- `--global` flag for Brewfile location (use `$HOMEBREW_BUNDLE_FILE` env var instead)

## Project-Specific Context

### Current System Architecture

The dotfiles repository uses `ansible-role-dotmodules` which:
1. Aggregates `config.yml` from all modules in playbook's `install` list
2. Installs packages directly via Ansible's `homebrew` modules
3. Does NOT generate or use Brewfiles (packages come from YAML configs)
4. Handles taps, formulas, casks, and Mac App Store apps

### Existing Module Structure

22 modules currently exist with varying levels of package declarations:
- **With packages:** git, zsh, node, editor, productivity, docker, macos, rust, speckit
- **Casks only:** 1password, alfred, chatgpt, chrome, claude, cursor, grammarly, handbrake, iterm, obsidian, spotify
- **No packages:** bin, finances (these are config-only modules)

### Current vs Installed Gap

**Declared packages:** ~45 unique (20 formulas + 13 casks)
**Installed formulas:** 122 total (37 top-level via `brew leaves`)
**Gap:** 18 top-level packages undeclared (see audit HOMEBREW.md)

### Audit Findings (from .planning/audit/HOMEBREW.md)

**Personal packages worth adding (from audit):**
- ansible, ffmpeg, go, imagemagick, jq, nginx, postgresql@14, stow, tmux, wget
- gnupg/pinentry-mac, sops, streamlink, rename, rsync, dos2unix
- git-filter-repo, git-quick-stats, things.sh, ical-buddy, obsidian-cli
- reattach-to-user-namespace, gnu-sed

**Corporate packages to exclude (from audit):**
- aws-sam-cli, awscli, azure-cli, cfn-lint, egctl
- helm, teleport, vault, saml2aws, terraform-docs
- mongocli, mongosh, android-* tools

**Tap patterns discovered (from current system):**
```
antoniorodr/memo       → memo (deprecated, skip)
steipete/tap           → gogcli, imsg, peekaboo, remindctl, summarize
yakitrak/yakitrak      → obsidian-cli
```

### Package Classification Strategy

Based on audit and installed packages:

1. **Keep in modules:** Top-level personal tools used regularly
2. **Exclude from modules:** Corporate tools, one-time tools, deprecated packages
3. **Document as dependencies:** Anything that's not a leaf package
4. **Create new modules if needed:** E.g., "media" for ffmpeg/imagemagick, "database" for postgresql

### Deliverables for This Phase

1. **Audit reconciliation:** Review `.planning/audit/HOMEBREW.md` findings
2. **Module updates:** Add missing packages to appropriate `config.yml` files
3. **New modules (if needed):** Create modules for logical groupings
4. **Reference Brewfile:** Generate canonical Brewfile for documentation/backup
5. **Documentation:** Update module READMEs with package rationale
6. **Validation:** Compare `brew leaves` with aggregated module declarations

### Why Not Switch to Pure Brewfile?

The project could switch to Brewfile-only approach, but **should not** because:
- Loses module organization (all packages in one flat file)
- Can't co-locate packages with their configs
- ansible-role-dotmodules provides value beyond packages (stow, merging, conflicts)
- Module pattern enables selective installation (only install what you need)
- Breaking change would require playbook rewrites

However, **generating a Brewfile alongside modules** provides:
- Backup for disaster recovery
- Quick machine setup before Ansible available
- Easy comparison with other systems
- Documentation of full package set

## Open Questions

1. **Should third-party tap packages be in separate modules?**
   - What we know: yakitrak/obsidian-cli is in obsidian module, steipete/* packages scattered
   - What's unclear: Best practice for grouping tap-based utilities
   - Recommendation: Keep tap packages with their logical module (obsidian-cli with obsidian), but create "cli-tools" module for miscellaneous steipete/* utilities

2. **How to handle package version pinning?**
   - What we know: Homebrew formulas can specify versions (e.g., postgresql@14, python@3.13)
   - What's unclear: Whether modules should pin versions or use latest
   - Recommendation: Pin when needed for compatibility (e.g., postgresql major versions), use latest otherwise

3. **Should dependencies ever be declared?**
   - What we know: Homebrew handles dependencies automatically
   - What's unclear: Are there cases where explicitly declaring helps?
   - Recommendation: Never declare dependencies UNLESS package has multiple providers and you need specific one (rare)

4. **How to handle Formula vs Cask name conflicts?**
   - What we know: Some packages have both (docker formula + Docker Desktop cask)
   - What's unclear: Naming convention in modules when both exist
   - Recommendation: Use different module names (docker for CLI, docker-desktop for GUI) or document in comments

5. **What's the threshold for creating a new module?**
   - What we know: Project has 22 modules ranging from single-tool to multi-tool
   - What's unclear: When does "productivity" become too broad?
   - Recommendation: Create new module when >5 related packages OR single complex tool with extensive config

## Sources

### Primary (HIGH confidence)
- [Homebrew Bundle Documentation](https://docs.brew.sh/Brew-Bundle-and-Brewfile) - Official Brewfile format and commands
- [ansible-role-dotmodules GitHub](https://github.com/getfatday/ansible-role-dotmodules) - Role architecture and task implementation
- Project audit files (.planning/audit/HOMEBREW.md) - Current vs old laptop comparison
- Current module configs (modules/*/config.yml) - Existing declaration patterns

### Secondary (MEDIUM confidence)
- [Brew Bundle Brewfile Tips (Gist)](https://gist.github.com/ChristopherA/a579274536aab36ea9966f301ff14f3f) - Community best practices
- [Homebrew 5.0.0 Release Notes](https://brew.sh/2025/11/12/homebrew-5.0.0/) - Recent changes and features
- [MacStadium: Advanced Homebrew Options](https://macstadium.com/blog/advanced-homebrew-options-to-level-up-your-infrastructure) - Enterprise patterns

### Tertiary (LOW confidence)
- [Jamf and Zscaler Integration](https://www.jamf.com/blog/jamf-zscaler-threat-detection-identification/) - Corporate package context (helps identify exclusions)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Homebrew and brew bundle are well-documented, stable tools
- Architecture: HIGH - Module patterns evident from existing codebase, Homebrew design is clear
- Pitfalls: HIGH - Discovered through actual gap analysis and package inspection
- Corporate filtering: MEDIUM - Based on audit but requires human judgment per package

**Research date:** 2026-02-12
**Valid until:** 90 days (Homebrew is stable; module pattern is established)
**Revalidate if:** Homebrew 6.x releases OR ansible-role-dotmodules changes package handling OR project switches to pure Brewfile approach
