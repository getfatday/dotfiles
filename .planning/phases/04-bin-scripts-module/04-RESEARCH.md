# Phase 4: ~/bin Scripts Module - Research

**Researched:** 2026-02-12
**Domain:** Shell script management, dotfile security, script migration, GNU Stow deployment
**Confidence:** HIGH

## Summary

This phase migrates personal utility scripts from an old laptop to the dotfiles repo's bin module while filtering out corporate scripts, secrets, and hardcoded paths. The primary technical domains are:

1. **GNU Stow symlink management** - How file permissions and executable bits are preserved through symlinks
2. **Shell script security** - Preventing secret leakage in public repos (email addresses, API keys, hardcoded credentials)
3. **Shebang best practices** - Portable script headers for cross-platform compatibility
4. **Script sanitization** - Detecting and removing hardcoded paths, secrets, and corporate references

The research confirms that GNU Stow preserves file permissions through symlinks, so scripts MUST be committed with executable mode (100755) to work after stowing. The main risk areas are accidentally committing secrets (73.6% of public dotfiles repos leak sensitive data) and missing hardcoded corporate references that would leak private information.

**Primary recommendation:** Use git ls-files mode 100755 for all scripts, apply #!/usr/bin/env bash shebangs for portability, and use grep-based detection patterns to find secrets/corporate references before migration.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| GNU Stow | 2.3+ | Dotfile symlink deployment | De facto standard for dotfile management, used by project |
| Bash | 4.0+ | Script interpreter | macOS ships with bash, most scripts use bash |
| grep/ripgrep | Latest | Pattern detection for secrets | Standard text search tools for filtering |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| detect-secrets | Latest | Secret scanning | Optional, more thorough than grep for secret detection |
| shellcheck | Latest | Shell script linting | Optional, for validating script quality |
| git ls-files | Part of git | Query git file modes | For verifying executable permissions are set |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| GNU Stow | Manual copying | Stow provides atomic updates and conflict detection |
| Bash scripts | Zsh scripts | Bash more portable, zsh requires zsh installed |
| grep patterns | detect-secrets tool | grep simpler for one-time migration, detect-secrets better for CI/CD |

**Installation:**
```bash
# Already available
brew install stow  # Already required by dotfiles project
# grep is built-in to macOS
# git is already installed (required by phase 2)

# Optional tools
brew install shellcheck  # For script quality checking
pip install detect-secrets  # For advanced secret scanning
```

## Architecture Patterns

### Recommended Project Structure
```
modules/bin/
├── config.yml                       # Module configuration (stow_dirs only)
└── files/
    └── .local/bin/                  # User scripts directory
        ├── git-*                    # Git utility scripts
        ├── slack-*                  # Slack API scripts
        ├── emacs-*                  # Emacs utility scripts
        └── [other-scripts]          # Standalone utilities
```

**Key insight:** Git scripts belong in `modules/git/files/.local/bin/`, not `modules/bin/`. The bin module is for non-git-specific utilities.

### Pattern 1: Script Organization by Domain
**What:** Group related scripts by their primary purpose/domain
**When to use:** When organizing utility scripts in a dotfiles repo
**Example:**
```
modules/git/files/.local/bin/    # Git-specific commands (git-*)
modules/bin/files/.local/bin/    # General utilities (slack-*, jsonl2tsv, etc.)
modules/editor/                   # Editor-specific scripts could go here
```

**Why:** Domain-specific modules can be installed/updated independently. Git scripts should travel with git configuration.

### Pattern 2: GNU Stow Preserves Permissions via Symlinks
**What:** Stow creates symlinks; file permissions remain in source files
**When to use:** Always - this is how Stow works
**Example:**
```bash
# Source file with executable bit
$ git ls-files -s modules/bin/files/.local/bin/slack-api
100755 abc123... 0	modules/bin/files/.local/bin/slack-api

# After stowing, symlink inherits source permissions
$ ls -l ~/.local/bin/slack-api
lrwxr-xr-x ... .local/bin/slack-api -> ../../.dotmodules/modules/bin/files/.local/bin/slack-api

# Symlink points to executable file, so it's executable
$ ~/.local/bin/slack-api --help
# Works because source file is 755
```

**Key insight:** Files MUST be committed to git with executable mode (100755) or they won't be executable after stowing. Set with `git add --chmod=+x <file>` or `git update-index --chmod=+x <file>`.

### Pattern 3: Portable Shebang with /usr/bin/env
**What:** Use `#!/usr/bin/env bash` instead of `#!/bin/bash`
**When to use:** For scripts intended to run on multiple systems (Linux, macOS, BSD)
**Example:**
```bash
#!/usr/bin/env bash
# Portable - finds bash from PATH

# NOT:
#!/bin/bash
# Hardcoded - fails if bash is in /usr/local/bin or /opt/homebrew/bin
```

**Why:** Avoids hardcoding paths. FreeBSD/OpenBSD don't have bash in `/bin` by default. Homebrew bash on macOS may be in `/opt/homebrew/bin/bash`.

**Source:** [GitHub - RfidResearchGroup/proxmark3 Issue #560](https://github.com/RfidResearchGroup/proxmark3/issues/560), [Tech Edu Byte - Bash Shebang](https://www.techedubyte.com/bash-shebang-bin-bash-vs-usr-bin-env-bash/)

### Pattern 4: Shebang Must Be First Line
**What:** The shebang MUST be the very first line, no blank lines or whitespace before it
**When to use:** Always - kernel requirement
**Example:**
```bash
#!/usr/bin/env bash
# Correct - shebang is first line

# NOT:

#!/usr/bin/env bash
# Wrong - blank line before shebang causes kernel to ignore it
```

**Source:** [Linuxize - Bash Shebang](https://linuxize.com/post/bash-shebang/), [Medium - Shebang Best Practices](https://medium.com/@redswitches/shebang-in-bash-and-python-scripts-best-practices-8c0a0b42c176)

### Anti-Patterns to Avoid
- **644 permissions on scripts:** Files won't be executable after stowing (Stow preserves source permissions via symlinks)
- **Hardcoded bash path:** `/bin/bash` fails on systems with bash in different locations
- **No shebang:** Script runs with default shell, may not support bash-specific syntax
- **Blank line before shebang:** Kernel ignores shebang, script may fail

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Secret detection | Manual grep patterns | detect-secrets, git-secrets, trufflehog | Handles entropy detection, regex patterns, base64 encoding, many secret formats |
| Shell script validation | Custom linting | shellcheck | Catches syntax errors, bad practices, portability issues |
| Git file mode management | Manual chmod + git add | git add --chmod=+x or git update-index --chmod=+x | Atomic operation, records mode in git index |
| Dotfile deployment | Custom copy scripts | GNU Stow | Handles conflicts, atomic updates, easy rollback via unstow |

**Key insight:** Secret detection is deceptively complex. Tools like detect-secrets handle entropy analysis, base64 detection, and context-aware filtering that grep patterns miss.

## Common Pitfalls

### Pitfall 1: Committing Scripts as 644 (Non-Executable)
**What goes wrong:** Scripts work fine on source machine but fail after stowing because symlink points to non-executable file
**Why it happens:** File was added to git without executable bit, or copied from system that doesn't preserve permissions
**How to avoid:** Always use `git add --chmod=+x` when adding scripts, verify with `git ls-files -s` (should show 100755)
**Warning signs:**
- `git ls-files -s` shows `100644` instead of `100755`
- `ls -l` shows `-rw-r--r--` instead of `-rwxr-xr-x`
- Script works directly but fails when run from stowed symlink

**Detection:**
```bash
# Find non-executable scripts in bin directory
git ls-files -s modules/bin/files/.local/bin/ | grep '^100644'

# Fix non-executable scripts
git ls-files modules/bin/files/.local/bin/ | xargs git update-index --chmod=+x
```

### Pitfall 2: Leaking Secrets in Public Repos
**What goes wrong:** Public dotfiles repos commonly leak API keys, email addresses, SSH keys, hardcoded credentials
**Why it happens:** Scripts developed privately contain secrets; users don't audit before committing
**How to avoid:** Use grep patterns to detect secrets before committing, consider using detect-secrets tool
**Warning signs:**
- Email addresses in scripts (especially corporate domains)
- Long alphanumeric strings in quotes
- Patterns like `token=`, `password=`, `api_key=`
- Hardcoded URLs to internal services

**Detection patterns:**
```bash
# Find common secret patterns
grep -REi "(auth|authentication|authorization|bearer|secret|token|pass|password|username)" modules/bin/files/.local/bin/

# Find email addresses
grep -REi "[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}" modules/bin/files/.local/bin/

# Find corporate references
grep -REi "(expedia|corporate-domain)" modules/bin/files/.local/bin/

# Find quoted strings that might be secrets (24+ chars)
grep -REi "('|\")[a-zA-Z0-9]{24,}('|\")" modules/bin/files/.local/bin/
```

**Source:** [InstaTunnel - Dotfiles Security](https://instatunnel.my/blog/why-your-public-dotfiles-are-a-security-minefield), [Medium - Dotfiles Security Minefield](https://medium.com/@instatunnel/why-your-public-dotfiles-are-a-security-minefield-fc9bdff62403), [Cycode - Hardcoded Secrets](https://cycode.com/blog/dont-let-hardcoded-secrets-compromise-your-security-4-effective-remediation-techniques/)

**Statistics:** Research found 73.6% of dotfiles repos leak sensitive information. Most common: email addresses (1.2M found), RSA private keys, API keys, browsing history.

### Pitfall 3: Hardcoded Paths That Don't Transfer
**What goes wrong:** Scripts reference paths specific to old laptop, fail on new machine
**Why it happens:** Development machine has specific directory structure, user forgets paths are hardcoded
**How to avoid:** Use `$HOME` or `~` for user directories, environment variables for tool paths, or find utilities to locate files
**Warning signs:**
- Paths starting with `/Users/specificusername/`
- Hardcoded paths to tools in `/usr/local/bin/` or `/opt/homebrew/bin/`
- References to project directories that may not exist on other machines

**Detection:**
```bash
# Find hardcoded user paths
grep -RE "/Users/[^/]+/" modules/bin/files/.local/bin/

# Find hardcoded tool paths
grep -RE "/(usr/local|opt/homebrew)/bin/" modules/bin/files/.local/bin/

# Find absolute paths that might be machine-specific
grep -RE "^[^#]*(/Volumes/|/Users/)" modules/bin/files/.local/bin/
```

**Fix:** Replace with environment variables or detection logic:
```bash
# Instead of:
/Users/ianderson/src/project/tool

# Use:
$HOME/src/project/tool
# or
~/src/project/tool
# or if project might not exist:
if [ -d ~/src/project ]; then ~/src/project/tool; fi
```

### Pitfall 4: Missing Script Dependencies
**What goes wrong:** Script depends on utilities not installed on new machine
**Why it happens:** Old laptop had tools installed over time; dependencies not documented
**How to avoid:** Add dependencies to module's config.yml, document in script header comments
**Warning signs:**
- Script calls commands like `jq`, `curl`, `fzf` without checking if they exist
- Script assumes specific versions of tools
- Script depends on other custom scripts

**Detection:**
```bash
# Find common utility dependencies in scripts
grep -RhE "^[^#]*(jq|curl|fzf|rg|bat|fd|exa)" modules/bin/files/.local/bin/ | sort -u
```

**Fix:** Document in config.yml:
```yaml
# modules/bin/config.yml
homebrew_packages:
  - jq      # Required by slack-api script
  - curl    # Required by slack-api script
```

### Pitfall 5: Corporate/Private References in "Generic" Scripts
**What goes wrong:** Script appears generic but contains one line with corporate domain or internal reference
**Why it happens:** Script was developed at work, adapted for personal use, one reference missed during cleanup
**How to avoid:** Grep for corporate domains, internal URLs, company-specific email patterns
**Warning signs:**
- Corporate email domain in fallback/default values
- URLs to internal services
- References to internal project names or team names

**Example from audit:** `git-report` script has `expediagroup.com` email fallback on line 174. Remove or parameterize that line to make it reusable.

**Detection:**
```bash
# Find corporate domain references
grep -RnE "(company|expedia|corporate-domain)\.(com|biz|io)" modules/bin/files/.local/bin/

# Find internal URLs
grep -RnE "https?://[^/]*\.(internal|corp|local)" modules/bin/files/.local/bin/
```

## Code Examples

Verified patterns from existing scripts and official sources:

### Setting Executable Permissions in Git
```bash
# When adding new scripts
git add --chmod=+x modules/bin/files/.local/bin/new-script

# To fix existing scripts already in staging
git update-index --chmod=+x modules/bin/files/.local/bin/existing-script

# Verify permissions are correct (should show 100755)
git ls-files -s modules/bin/files/.local/bin/

# Example output (correct):
# 100755 abc123... 0	modules/bin/files/.local/bin/slack-api
```

### Portable Shebang
```bash
#!/usr/bin/env bash
# Correct - finds bash from PATH, works on macOS, Linux, BSD

# Example from git-recent script (already in repo):
#!/usr/bin/env bash

# Source: https://gist.github.com/jordan-brough/48e2803c0ffa6dc2e0bd
```
Source: modules/git/files/.local/bin/git-recent

### Script with Dependency Check
```bash
#!/usr/bin/env bash

# Check for required dependencies
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed" >&2
    echo "Install with: brew install jq" >&2
    exit 1
fi

# Rest of script...
```

### Detecting Secrets Before Commit
```bash
# Comprehensive secret scan before migrating scripts
cd modules/bin/files/.local/bin/

# Find potential secrets
grep -RnEi "(auth|bearer|secret|token|password|api[_-]?key)" .

# Find email addresses
grep -RnE "[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}" .

# Find corporate references
grep -RnEi "(expedia|company-name)" .

# Find long quoted strings (potential tokens)
grep -RnE "('|\")[a-zA-Z0-9]{24,}('|\")" .

# Find hardcoded user paths
grep -RnE "/Users/[^/]+/" .
```

### Script Header Template
```bash
#!/usr/bin/env bash
#
# script-name - Brief description
#
# Usage: script-name [options] args
#
# Dependencies:
#   - jq (brew install jq)
#   - curl (built-in)
#
# Example:
#   script-name --flag value

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script implementation...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded `/bin/bash` | `#!/usr/bin/env bash` | Ongoing best practice | Better cross-platform compatibility, works with Homebrew bash |
| GPG commit signing | SSH commit signing | 2021-2022 (Git 2.34+) | Simpler setup, integrates with 1Password/SSH agents |
| Manual chmod + git add | `git add --chmod=+x` | Git 2.9+ (2016) | Single command to add with executable bit |
| Secrets in dotfiles | Encrypted secrets or env vars | Ongoing security practice | Prevents leakage in public repos |

**Deprecated/outdated:**
- Hardcoded interpreter paths in shebangs - Use `/usr/bin/env <interpreter>` instead
- 644 permissions for scripts - Must be 755 for execution
- Secrets in configuration files - Use environment variables, password managers, or encrypted storage

## Open Questions

1. **Are there symlinks in the old laptop's ~/bin/?**
   - What we know: Audit mentions `jump-window` is a symlink to iCloud tmux config
   - What's unclear: Should symlinks be preserved, or should we copy their targets?
   - Recommendation: Document symlinks in migration notes, decide case-by-case (external symlinks probably skip, internal ones copy target)

2. **What about scripts that depend on other scripts?**
   - What we know: `slack-api` calls `slack-token` utility
   - What's unclear: Should dependencies be enforced in config.yml or documented only?
   - Recommendation: Document in script header comments, don't enforce in config.yml (scripts are optional utilities)

3. **Should scripts be validated with shellcheck?**
   - What we know: shellcheck is industry standard for bash linting
   - What's unclear: Is it worth adding to verification criteria?
   - Recommendation: Optional - run manually during migration but don't enforce in CI

## Sources

### Primary (HIGH confidence)
- [GNU Stow Manual](https://www.gnu.org/software/stow/manual/stow.html) - Official documentation on symlink behavior
- Git documentation - File permission handling via git ls-files and update-index
- Existing module structure (modules/git/files/.local/bin/) - Observed pattern of 100755 permissions

### Secondary (MEDIUM confidence)
- [Tech Edu Byte - Bash Shebang](https://www.techedubyte.com/bash-shebang-bin-bash-vs-usr-bin-env-bash/) - Portable shebang best practices
- [Linuxize - Bash Shebang](https://linuxize.com/post/bash-shebang/) - Shebang must be first line
- [Medium - Shebang Best Practices](https://medium.com/@redswitches/shebang-in-bash-and-python-scripts-best-practices-8c0a0b42c176) - When to use different shebangs
- [GitHub - proxmark3 Issue #560](https://github.com/RfidResearchGroup/proxmark3/issues/560) - Remove hardcoded paths in scripts
- [InstaTunnel - Dotfiles Security](https://instatunnel.my/blog/why-your-public-dotfiles-are-a-security-minefield) - 73.6% of dotfiles leak secrets
- [Medium - Dotfiles Security Minefield](https://medium.com/@instatunnel/why-your-public-dotfiles-are-a-security-minefield-fc9bdff62403) - Common dotfile security issues
- [Cycode - Hardcoded Secrets](https://cycode.com/blog/dont-let-hardcoded-secrets-compromise-your-security-4-effective-remediation-techniques/) - Remediation techniques
- [Smallstep - Command Line Secrets](https://smallstep.com/blog/command-line-secrets/) - Handling secrets securely
- [Nick Janetakis - Find/Remove Hardcoded Passwords](https://nickjanetakis.com/blog/help-find-and-remove-hard-coded-passwords-and-secrets-in-a-project) - Detection patterns

### Tertiary (LOW confidence)
- Various GitHub secret scanning tools (detect-secrets, git-secrets, trufflehog) - Mentioned in searches but not verified for this use case

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - GNU Stow behavior verified via official docs and existing module observation (git module has 100755 scripts)
- Architecture: HIGH - Patterns observed in existing modules (git/, bin/) and verified via git ls-files
- Pitfalls: HIGH - 644 vs 755 verified via Stow symlink behavior, secret leakage statistics from multiple sources, shebang requirements from official docs

**Research date:** 2026-02-12
**Valid until:** 60 days (stable domain - shell scripting and GNU Stow practices change slowly)
