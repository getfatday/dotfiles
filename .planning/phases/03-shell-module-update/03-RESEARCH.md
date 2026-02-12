# Phase 03: Shell Module Update - Research

**Researched:** 2026-02-12
**Domain:** Zsh shell configuration, Prezto framework, modular dotfile management
**Confidence:** HIGH

## Summary

Phase 3 requires updating the zsh module to capture all missing shell configuration from the old laptop while maintaining cross-platform compatibility (Intel vs ARM Mac) and modular architecture. The audit reveals three critical gaps: (1) missing Prezto initialization in .zshrc, (2) no .zshenv file in the repo (required by multiple modules for PATH management), and (3) missing configurations that should live in other modules (docker, editor, node, claude).

The ansible-role-dotmodules system uses a file merging strategy where modules contribute partial .zshrc and .zshenv files that are merged at deployment time with clear attribution headers. This means the fix is distributed across multiple modules, not centralized in the zsh module alone.

**Primary recommendation:** Add Prezto init to zsh module's .zshrc, create .zshenv files in each module that needs PATH/env setup (following the node/editor pattern), enable Prezto git aliases, and use architecture detection for Homebrew path handling.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Zsh | Latest from Homebrew | Shell | Default shell on macOS since Catalina |
| Prezto | Latest from GitHub | Zsh framework | Lighter than Oh My Zsh, modular, mature |
| GNU Stow | Latest from Homebrew | Symlink manager | ansible-role-dotmodules dependency |
| ansible-role-dotmodules | Custom (getfatday) | Dotfile orchestration | Handles file merging and module installation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asdf | Latest from Homebrew | Version manager | For Node.js, Ruby, Python version management |
| z/autojump | Latest from Homebrew | Directory navigation | Quick directory jumping (already in productivity module) |
| zsh-history-substring-search | Latest from Homebrew | History search | Already in zsh module config.yml |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Prezto | Oh My Zsh | Oh My Zsh is slower, more features but heavier; Prezto is faster and modular |
| Prezto | Zim Framework | Zim is faster but less mature; Prezto already in use |
| asdf | nvm/rbenv | asdf is polyglot (one tool for all languages); already committed to asdf in node module |

**Installation:**
```bash
# Already in modules/zsh/config.yml
homebrew_packages:
  - zsh
  - zsh-history-substring-search

# Prezto installed via setup-prezto.sh script (modules/zsh/files/.local/bin/setup-prezto.sh)
```

## Architecture Patterns

### Recommended Project Structure
```
modules/
├── zsh/                    # Core zsh + Prezto
│   ├── config.yml         # Declares mergeable_files: .zshrc, .zpreztorc
│   └── files/
│       ├── .zshrc         # Prezto init + zsh module contributions
│       ├── .zpreztorc     # Prezto module configuration
│       └── .local/bin/setup-prezto.sh
├── editor/                 # Emacs/editor config
│   ├── config.yml         # Declares mergeable_files: .zshrc, .zshenv
│   └── files/
│       ├── .zshrc         # Editor aliases and functions
│       └── .zshenv        # EDITOR/VISUAL env vars
├── node/                   # Node.js tooling
│   ├── config.yml         # Declares mergeable_files: .zshrc, .zshenv
│   └── files/
│       ├── .zshrc         # PNPM, asdf integration
│       └── .zshenv        # Node PATH entries
├── docker/                 # Docker tooling
│   └── files/
│       └── .zshrc         # Docker aliases and completions
└── merged/                 # Auto-generated at deploy time
    ├── .zshrc             # Merged from all modules
    └── .zshenv            # Merged from all modules
```

### Pattern 1: Shell File Load Order

**What:** Zsh loads files in this order: `.zshenv` → `.zprofile` → `.zshrc` → `.zlogin` → `.zlogout`

**When to use:**
- `.zshenv`: Environment variables and PATH (sourced in ALL shells, even non-interactive)
- `.zprofile`: Login shell setup (rarely needed on macOS)
- `.zshrc`: Interactive shell configuration (aliases, functions, completions, prompts)
- `.zlogin`: Commands to run after `.zshrc` (rarely needed)

**Example:**
```bash
# modules/node/files/.zshenv
# Node module contribution to Zsh environment
# This file will be merged with the main .zshenv file

# Node.js and npm PATH additions
export PATH=$HOME/.npm-packages/bin:$HOME/.node/bin:$HOME/.asdf/shims:$PATH
```

**Source:** [ZSH configuration files load order](https://zsh.sourceforge.io/Intro/intro_3.html), [How Do Zsh Configuration Files Work?](https://www.freecodecamp.org/news/how-do-zsh-configuration-files-work/)

### Pattern 2: Prezto Initialization

**What:** Prezto is loaded by sourcing its init script in `.zshrc`, typically at the end

**When to use:** Always, in the zsh module's .zshrc file (currently MISSING from repo)

**Example:**
```bash
# Source Prezto framework
if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
  source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
fi
```

**Source:** [GitHub - sorin-ionescu/prezto](https://github.com/sorin-ionescu/prezto), [Better zsh with Prezto](https://wikimatze.de/better-zsh-with-prezto/)

### Pattern 3: Cross-Architecture Homebrew Path

**What:** Homebrew uses different paths for ARM64 (`/opt/homebrew`) vs Intel (`/usr/local`)

**When to use:** Any module that references Homebrew paths directly (node, productivity)

**Example:**
```bash
# Detect architecture and use appropriate Homebrew path
if command -v brew >/dev/null 2>&1; then
  BREW_PREFIX="$(brew --prefix)"
else
  # Fallback based on architecture
  if [[ "$(uname -m)" == "arm64" ]]; then
    BREW_PREFIX="/opt/homebrew"
  else
    BREW_PREFIX="/usr/local"
  fi
fi

# Use BREW_PREFIX in path references
if [[ -f "$BREW_PREFIX/etc/profile.d/z.sh" ]]; then
  . "$BREW_PREFIX/etc/profile.d/z.sh"
fi
```

**Source:** [Homebrew Setup for Apple/Intel Compatibility](https://www.metasimple.org/2025/01/11/dual-brew-setup.html), [Migrate from Intel (Rosetta2) to ARM brew on M1](https://github.com/orgs/Homebrew/discussions/417)

### Pattern 4: Module File Merging

**What:** ansible-role-dotmodules merges files declared in `mergeable_files` with attribution headers

**When to use:** For files like `.zshrc`, `.zshenv`, `.bashrc` that multiple modules need to contribute to

**Example:**
```yaml
# modules/node/config.yml
mergeable_files:
  - ".zshrc"      # Node.js environment and asdf integration
  - ".zshenv"     # Node.js PATH configuration
```

**Result at deployment:**
```bash
# =============================================================================
# ZSH MODULE CONTRIBUTION
# =============================================================================
if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
  source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
fi

# =============================================================================
# NODE MODULE CONTRIBUTION
# =============================================================================
export PNPM_HOME="/Users/ianderson/Library/pnpm"
if [ -f /opt/homebrew/opt/asdf/libexec/asdf.sh ]; then
  . /opt/homebrew/opt/asdf/libexec/asdf.sh
fi
```

**Source:** [ansible-role-dotmodules README.md](file:///Users/ianderson/.ansible/roles/ansible-role-dotmodules/README.md)

### Pattern 5: asdf Global vs Project Configuration

**What:** asdf reads `.tool-versions` from `$HOME` (global) and project directories (local), with local overriding global

**When to use:**
- Global `~/.tool-versions`: Fallback default versions for tools
- Project `.tool-versions`: Project-specific versions (committed to version control)

**Example:**
```bash
# Global ~/.tool-versions (in node module)
nodejs 25.2.1
jq 1.7.1

# Project myapp/.tool-versions (in project repo)
nodejs 20.10.0  # Overrides global for this project
```

**Source:** [Versions | asdf](https://asdf-vm.com/manage/versions.html), [Managing Multiple Tool Versions with asdf](https://schoenwald.aero/posts/2025-02-20_managing-multiple-tool-versions/)

### Anti-Patterns to Avoid

- **Hardcoding Homebrew paths:** Use `brew --prefix` or architecture detection instead of `/opt/homebrew` or `/usr/local`
- **Centralizing all shell config in zsh module:** Respect module boundaries (docker aliases in docker module, editor vars in editor module)
- **Skipping .zshenv:** PATH and environment variables belong in .zshenv (sourced by all shells), not .zshrc (interactive only)
- **Putting project-specific versions in global .tool-versions:** Global should be fallback defaults, not pinned versions
- **Duplicating Prezto module config:** Don't re-implement git aliases when Prezto provides them (set `skip 'no'` in .zpreztorc)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Zsh framework | Custom prompt, completion, plugin system | Prezto (already in use) | Prompt themes, module system, git integration, syntax highlighting battle-tested |
| File merging across modules | Manual shell scripts to concatenate files | ansible-role-dotmodules mergeable_files | Handles attribution, conflict detection, idempotent deployment |
| Version management | Custom version switching scripts | asdf (already in use) | Handles shims, PATH manipulation, .tool-versions parsing, polyglot |
| Directory jumping | Manual directory history tracker | z or autojump (already in productivity module) | Frecency algorithm, mature, fast |
| Homebrew path detection | Hardcoded paths with if/else | `brew --prefix` | Handles both architectures, relocatable installs, future-proof |

**Key insight:** Shell configuration is deceptively complex. Load order matters, PATH order matters, quoting matters, subshell behavior differs. Use established tools (Prezto, asdf) rather than custom solutions. The ansible-role-dotmodules merging system handles the hard parts (order, deduplication, attribution).

## Common Pitfalls

### Pitfall 1: Missing Prezto Initialization

**What goes wrong:** Prezto modules (git, syntax-highlighting, prompt) don't load; shell looks vanilla despite .zpreztorc configuration

**Why it happens:** The init line is missing from .zshrc (currently the case in this repo)

**How to avoid:** Add Prezto init to zsh module's .zshrc:
```bash
if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
  source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
fi
```

**Warning signs:** No git prompt, no syntax highlighting, `which gws` returns "command not found" despite .zpreztorc loading git module

### Pitfall 2: PATH Set in .zshrc Instead of .zshenv

**What goes wrong:** PATH additions don't propagate to non-interactive shells (scripts, cron, Emacs subprocesses)

**Why it happens:** Misunderstanding of when each file is sourced (.zshenv = all shells, .zshrc = interactive only)

**How to avoid:** Put PATH and environment variables in .zshenv, put aliases/functions/prompts in .zshrc

**Warning signs:** Commands work in terminal but fail in scripts, Emacs can't find executables in custom PATH

### Pitfall 3: Hardcoded Homebrew Paths

**What goes wrong:** Configuration breaks when moving between Intel and ARM Macs

**Why it happens:** Copy-pasting `/opt/homebrew` paths without architecture detection

**How to avoid:** Use `brew --prefix` or architecture detection pattern (see Pattern 3)

**Warning signs:** "command not found" errors on Intel Mac, or incorrect binaries loaded from Rosetta install

### Pitfall 4: Module Boundary Violations

**What goes wrong:** Docker aliases end up in zsh module, editor vars end up in zsh module, creating one giant monolithic config

**Why it happens:** Not understanding the ansible-role-dotmodules merging system

**How to avoid:** Each module contributes its own .zshrc/.zshenv fragment. Docker module owns docker aliases, editor module owns EDITOR var, node module owns asdf integration.

**Warning signs:** Modules can't be independently installed/removed, everything is coupled to zsh module

### Pitfall 5: Corporate Config Leakage

**What goes wrong:** Corporate paths, Android NDK, AWS tooling, Expedia-specific configs end up in public repo

**Why it happens:** Blindly copying old laptop's merged config without filtering

**How to avoid:** Cross-reference FILTERED.md, exclude anything mentioning: expedia, ewegian, zscaler, jamf, corporate VPNs, AWS/Azure (unless personal)

**Warning signs:** Paths like `/Applications/Zscaler`, Android NDK, corporate proxy settings

### Pitfall 6: Global .tool-versions Pinning

**What goes wrong:** All projects forced to use the same Node.js version, can't test against multiple versions

**Why it happens:** Treating global .tool-versions like a project lock file

**How to avoid:** Global versions should be "current stable" as a fallback; projects override with their own .tool-versions

**Warning signs:** Multiple projects break when global version changes, version conflicts between projects

### Pitfall 7: Prezto Git Alias Conflict

**What goes wrong:** Prezto's built-in git aliases (gws, gwd, etc.) are disabled, but user expects them

**Why it happens:** git module's .zpreztorc sets `skip 'yes'` but old laptop had `skip 'no'`

**How to avoid:** Check old laptop's behavior (audit shows `skip 'no'`), update .zpreztorc accordingly

**Warning signs:** `gws` (git status) doesn't work despite Prezto git module being loaded

## Code Examples

Verified patterns from official sources and current repo:

### Prezto Init in .zshrc
```bash
# modules/zsh/files/.zshrc
# Prezto init (CURRENTLY MISSING - NEEDS TO BE ADDED)

if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
  source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
fi
```
Source: [Prezto README](https://github.com/sorin-ionescu/prezto)

### Environment Variables in .zshenv
```bash
# modules/editor/files/.zshenv (CURRENT IMPLEMENTATION)
# Editor module contribution to Zsh environment
# This file will be merged with the main .zshenv file

# Default Editor
export EDITOR="emacsclient -t"
export VISUAL="emacsclient -t"
```
Source: Current repo (modules/editor/files/.zshenv)

### Cross-Platform Homebrew Integration
```bash
# modules/productivity/files/.zshrc (CURRENT IMPLEMENTATION - NEEDS UPDATE)
# Z directory navigation
if command -v brew >/dev/null 2>&1 && (( $+commands[brew] )) ; then
    if [[ -f `brew --prefix`/etc/profile.d/z.sh ]]; then
        . `brew --prefix`/etc/profile.d/z.sh
    fi
fi
```
Source: Current repo (modules/productivity/files/.zshrc) - already uses `brew --prefix`

### Module config.yml with Mergeable Files
```yaml
# modules/node/config.yml (CURRENT IMPLEMENTATION)
---
# Node.js development module
homebrew_packages:
  - asdf
  - node
  - pnpm

stow_dirs:
  - node

mergeable_files:
  - ".zshrc"      # Node.js environment and asdf integration
  - ".zshenv"     # Node.js PATH configuration
```
Source: Current repo (modules/node/config.yml)

### Conditional File Sourcing Pattern
```bash
# modules/node/files/.zshrc (CURRENT IMPLEMENTATION)
# ASDF integration
if [ -f /opt/homebrew/opt/asdf/libexec/asdf.sh ]; then
  . /opt/homebrew/opt/asdf/libexec/asdf.sh
fi

# ASDF direnv integration
if [ -f "${XDG_CONFIG_HOME:-$HOME/.config}/asdf-direnv/zshrc" ]; then
  source "${XDG_CONFIG_HOME:-$HOME/.config}/asdf-direnv/zshrc"
fi
```
Source: Current repo (modules/node/files/.zshrc)

### Prezto Module Configuration
```bash
# modules/zsh/files/.zpreztorc (CURRENT - NEEDS GIT ALIAS UPDATE)
# Git module configuration
zstyle ':prezto:module:git:status:ignore' submodules 'all'
# ADD THIS LINE to enable Prezto git aliases (currently missing):
# zstyle ':prezto:module:git:alias' skip 'no'
```
Source: Old laptop audit (had `skip 'no'`), [Prezto git module docs](https://github.com/sorin-ionescu/prezto/tree/master/modules/git)

### Global .tool-versions
```bash
# modules/node/files/.tool-versions (NEEDS TO BE CREATED)
nodejs 25.2.1
jq 1.7.1
```
Source: Old laptop audit (SHELL.md)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Monolithic .zshrc | Modular .zshrc fragments merged by ansible | ansible-role-dotmodules adoption | Better module isolation, reusability |
| Oh My Zsh | Prezto | ~2019 | Faster shell startup, lighter framework |
| nvm/rbenv/pyenv | asdf | ~2021 | Single tool for all languages, consistent interface |
| Hardcoded Intel paths | `brew --prefix` | Apple Silicon transition (2020-2021) | Cross-architecture compatibility |
| Manual file concatenation | ansible-role-dotmodules merge_files.yml | 2025 | Automated, attributed, conflict-detected merging |

**Deprecated/outdated:**
- `.zprofile`: Rarely needed on modern macOS; .zshenv and .zshrc handle most cases
- Hardcoded `/usr/local/bin` in PATH: Use `brew --prefix` or architecture detection
- prezto alias skip 'yes' in old git modules: Modern approach enables Prezto's curated aliases

## Open Questions

1. **Should OpenClaw completions be conditional or in a dedicated module?**
   - What we know: Audit shows `source "$HOME/.openclaw/completions/openclaw.zsh"` in old laptop
   - What's unclear: Should this be in a new `openclaw` module, or conditional in zsh module?
   - Recommendation: Create minimal `openclaw` module with .zshrc fragment containing conditional sourcing (file may not exist on fresh install)

2. **Should Rust/Cargo env be in a rust module or merged into existing module?**
   - What we know: Audit shows `. "$HOME/.cargo/env"` in old .zshenv
   - What's unclear: Is there enough Rust config to warrant a module, or should it be inline?
   - Recommendation: If there's a Cargo config file or Rust-specific settings, create rust module; otherwise add conditional sourcing to a utilities/speckit module

3. **What about the 'yolo' Claude alias?**
   - What we know: `alias yolo='claude --dangerously-skip-permissions'` on old laptop
   - What's unclear: Should this live in claude module (no .zshrc currently) or productivity?
   - Recommendation: Add .zshrc to claude module with this alias (follows module boundary principle)

4. **Should .inputrc be mergeable?**
   - What we know: .inputrc exists in zsh module (not declared mergeable)
   - What's unclear: Do other modules need to contribute to .inputrc?
   - Recommendation: Keep as stow-only unless another module needs readline config

## Sources

### Primary (HIGH confidence)
- [ansible-role-dotmodules README.md](file:///Users/ianderson/.ansible/roles/ansible-role-dotmodules/README.md) - File merging strategy, module structure
- [ansible-role-dotmodules merge_files.yml](file:///Users/ianderson/.ansible/roles/ansible-role-dotmodules/tasks/merge_files.yml) - Implementation details
- Current repo modules (zsh, node, editor, docker, productivity) - Existing patterns
- [ZSH Startup Files Introduction](https://zsh.sourceforge.io/Intro/intro_3.html) - Official Zsh documentation on file load order
- [asdf Versions Documentation](https://asdf-vm.com/manage/versions.html) - Official asdf version management
- [Prezto GitHub Repository](https://github.com/sorin-ionescu/prezto) - Official Prezto documentation

### Secondary (MEDIUM confidence)
- [How Do Zsh Configuration Files Work? - FreeCodeCamp](https://www.freecodecamp.org/news/how-do-zsh-configuration-files-work/) - Verified with official docs
- [Homebrew Setup for Apple/Intel Compatibility](https://www.metasimple.org/2025/01/11/dual-brew-setup.html) - Recent (2025) dual-arch guide
- [Migrate from Intel to ARM brew on M1 - GitHub Discussion](https://github.com/orgs/Homebrew/discussions/417) - Official Homebrew guidance
- [Better zsh with Prezto](https://wikimatze.de/better-zsh-with-prezto/) - Community best practices
- [How to Modularise Your Shell Config - Medium](https://medium.com/@DahlitzF/how-to-modularise-your-shell-config-81581ca8da) - Modular pattern verification

### Tertiary (LOW confidence)
- Various WebSearch results on Zsh configuration patterns - Used for discovery, verified against primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Prezto, asdf, zsh all documented in current repo and official sources
- Architecture: HIGH - ansible-role-dotmodules patterns confirmed in codebase, shell load order from official docs
- Pitfalls: HIGH - Based on specific gaps identified in audit (missing Prezto init, hardcoded paths observed)

**Research date:** 2026-02-12
**Valid until:** 2026-03-12 (30 days - stable technologies)
