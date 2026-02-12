# Technology Stack

**Project:** Ansible-based macOS Dotfiles Management & Migration
**Researched:** 2026-02-11
**Confidence:** MEDIUM-HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| ansible-core | 2.20.2 | Infrastructure automation engine | Latest stable release (Jan 2026), better Python 3.12+ support, actively maintained | HIGH |
| Python | 3.12+ | Runtime for Ansible | Required by ansible-core 2.20.2, stable on macOS via Homebrew | HIGH |
| Homebrew | Latest | macOS package manager | De facto standard for macOS package management, required for mas-cli and other tools | HIGH |
| mas-cli | 4.0+ | Mac App Store automation | Only CLI tool for App Store automation, required for scripting App Store installs | HIGH |
| 1Password CLI (op) | 2.18.0+ | Secret management | Service account support, integrates with Ansible via environment variables | MEDIUM |

### Ansible Collections

| Collection | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| community.general | 12.3.0+ | Homebrew module, 1Password lookups | Contains `homebrew` module and `onepassword_info` module for secret retrieval | HIGH |
| geerlingguy.mac | Latest (2.x) | macOS-specific automation roles | Provides homebrew, mas, and dock management roles; well-maintained by Jeff Geerling | MEDIUM |

**Note on geerlingguy.mac:** Requires separate installation of `elliotweiser.osx-command-line-tools` role (Ansible collections cannot depend on roles).

### Directory Auditing Tools

| Tool | Purpose | Why Recommended | Confidence |
|------|---------|-----------------|------------|
| rsync | File/directory comparison and sync | Built-in to macOS, preserves extended attributes and resource forks (critical for Mac-to-Mac), delta transfer algorithm | HIGH |
| diff | Basic directory comparison | Built-in Unix tool, simple output for quick comparisons | HIGH |
| brew bundle dump | Homebrew package audit | Official Homebrew feature, generates Brewfile with all installed packages (formulas, casks, mas, taps) | HIGH |

### Supporting Tools

| Tool | Version | Purpose | When to Use | Confidence |
|------|---------|---------|-------------|------------|
| mackup | Latest | Application config backup/restore | Optional: automated backup of app configs to dotfiles; use `.mackup.cfg` to exclude corporate files | MEDIUM |
| git | Latest | Version control | Required for dotfiles repository management | HIGH |
| DirEqual | Latest | GUI directory comparison | Optional: visual diff for complex directory audits; macOS-native app with snapshot feature | LOW |

## Installation

```bash
# Install Python 3.12+ via Homebrew
brew install python@3.12

# Install Ansible via pip (not Homebrew - better dependency isolation)
python3.12 -m pip install --user ansible-core==2.20.2

# Install required Ansible collections
ansible-galaxy collection install community.general
ansible-galaxy collection install geerlingguy.mac

# Install elliotweiser role (dependency for geerlingguy.mac)
ansible-galaxy role install elliotweiser.osx-command-line-tools

# Install mas-cli for Mac App Store automation
brew install mas

# Install 1Password CLI
brew install --cask 1password-cli

# Audit current system's Homebrew packages
brew bundle dump --file=./audit/Brewfile --describe --force
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative | Confidence |
|-------------|-------------|-------------------------|------------|
| ansible-core 2.20.2 | ansible-core 2.19.6 | If you need Python 3.11 support (2.20+ requires 3.12+); both released Jan 29, 2026 | HIGH |
| rsync | rclone | NEVER for Mac-to-Mac dotfiles - rclone cannot copy macOS extended attributes/resource forks | HIGH |
| Ansible + git | chezmoi | If managing single-user dotfiles across multiple platforms with templating; chezmoi has built-in templating and secret manager integration | MEDIUM |
| Ansible-only | Ansible + chezmoi hybrid | Use chezmoi for per-machine dotfile variations, Ansible for system-wide package/app installation | LOW |
| pip install ansible | brew install ansible | Historically problematic - Homebrew Ansible can't use pip module with Python 3.x properly; pip install gives better dependency control | MEDIUM |

## What NOT to Use

| Avoid | Why | Use Instead | Confidence |
|-------|-----|-------------|------------|
| rclone for Mac-to-Mac backup | Cannot copy macOS extended attributes, resource forks, or Finder metadata | rsync with `-a` flag for local/LAN transfers | HIGH |
| ansible package from Homebrew | Dependency conflicts with collections, pip module issues with Python 3.x | pip install --user ansible-core in virtual environment or user site-packages | MEDIUM |
| 1Password Connect Server | Overkill for single-user dotfiles; requires deployment infrastructure | 1Password CLI with service account or user authentication | MEDIUM |
| mas-cli < 4.0 | Older versions don't require sudo consistently; 4.0+ unified behavior after Apple CVE-2025-43411 fix | mas-cli 4.0+ (requires root for all install/update operations) | HIGH |
| DirEqual/GUI tools for automation | Not scriptable, manual workflow | rsync, diff, or brew bundle dump for automated auditing | MEDIUM |

## Stack Patterns by Use Case

### Pattern 1: Fresh macOS Setup (Greenfield)
**When:** Setting up a new Mac from dotfiles repo
**Stack:**
- Ansible playbook to install Homebrew
- `geerlingguy.mac.homebrew` role to install packages from Brewfile
- `geerlingguy.mac.mas` role to install App Store apps
- `community.general.onepassword_info` lookup for secrets
- Shell dotfiles (zsh) symlinked via Ansible `file` module

**Why:** Declarative, idempotent, repeatable. Ansible ensures system state matches desired state.

### Pattern 2: Audit Existing System (Migration)
**When:** Capturing config from old laptop to dotfiles repo
**Stack:**
- `brew bundle dump` to capture all Homebrew packages
- rsync to compare old laptop's home directory with current dotfiles
- Manual review of `.zshrc`, `.gitconfig`, etc.
- mackup to identify app configs to back up (with `.mackup.cfg` exclusions)
- 1Password CLI to export secrets to 1Password vault (NOT to git repo)

**Why:** Combination of automated discovery (brew bundle) and careful manual review prevents committing corporate secrets.

### Pattern 3: Sync Between Machines
**When:** Keeping multiple Macs in sync
**Stack:**
- Git to version control dotfiles repo
- Ansible playbook run periodically (`ansible-playbook --check --diff` for dry-run)
- 1Password CLI for secret retrieval
- Manual sync of sensitive files not suitable for git

**Why:** Git provides change tracking, Ansible ensures convergence, 1Password prevents secret leakage.

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| ansible-core 2.20.2 | Python 3.12, 3.13, 3.14 | Requires Python >= 3.12; dropped Python 3.11 support |
| ansible-core 2.19.6 | Python 3.11+ | If you need Python 3.11 support, use 2.19.x branch |
| community.general 12.3.0 | ansible-core 2.14+ | Works with both 2.19.x and 2.20.x |
| geerlingguy.mac 2.x | ansible-core 2.14+ | Requires elliotweiser.osx-command-line-tools role |
| mas-cli 4.0+ | macOS 13+ (Ventura or newer) | Older macOS versions (10.11-12) use mas-cli via Homebrew tap with older versions |
| 1Password CLI 2.18.0+ | macOS, service accounts | Service account support added in 2.18.0; caching added for macOS |

## macOS Apple Silicon Considerations

**Ansible Compatibility:** Fully supported on Apple Silicon (M1, M2, M3). Rosetta allows x86_64 software to run on ARM, but native ARM support is available for:
- Homebrew (native ARM bottles)
- Python 3.12+ (native ARM builds)
- ansible-core 2.20.2 (pure Python, architecture-agnostic)
- mas-cli (native ARM)

**Homebrew Prefix:** Apple Silicon uses `/opt/homebrew` instead of `/usr/local`. The `community.general.homebrew` module auto-detects this.

**Performance:** Native ARM performance is excellent. No known issues with Ansible on Apple Silicon as of 2026.

## Sources

### HIGH Confidence Sources
- [ansible-core PyPI](https://pypi.org/project/ansible-core/) - Official release information, version 2.20.2 verified
- [Ansible GitHub Releases](https://github.com/ansible/ansible/releases) - Official release dates (Jan 29, 2026)
- [community.general.homebrew module documentation](https://docs.ansible.com/projects/ansible/latest/collections/community/general/homebrew_module.html) - Official Ansible docs
- [1Password Connect Ansible Collection docs](https://developer.1password.com/docs/connect/ansible-collection/) - Official 1Password developer docs
- [mas-cli GitHub](https://github.com/mas-cli/mas) - Official source, version 4.0 requirements verified
- [Jeff Geerling blog: rclone vs rsync](https://www.jeffgeerling.com/blog/2025/4x-faster-network-file-sync-rclone-vs-rsync/) - Verified extended attributes limitation

### MEDIUM Confidence Sources
- [geerlingguy.mac collection GitHub](https://github.com/geerlingguy/ansible-collection-mac) - Verified roles, version less clear
- [Does It ARM - Ansible](https://doesitarm.com/formula/ansible) - Apple Silicon compatibility verified
- [Homebrew Formulae - ansible](https://formulae.brew.sh/formula/ansible) - Installation methods
- [Ansible for dotfiles introduction](https://phelipetls.github.io/posts/introduction-to-ansible/) - Community best practices
- [1Password CLI Release Notes](https://app-updates.agilebits.com/product_history/CLI2) - Service account features
- [community.general GitHub releases](https://github.com/ansible-collections/community.general/releases) - Version 12.3.0 referenced in docs

### LOW Confidence Sources (WebSearch-only, unverified with official docs)
- Various GitHub dotfiles repos for pattern examples
- DirEqual (commercial product, not verified with testing)
- mackup exclusion patterns (community contributions, not official docs)

---
*Stack research for: Ansible-based macOS Dotfiles Management*
*Researched: 2026-02-11*
*Next: FEATURES.md, ARCHITECTURE.md, PITFALLS.md*
