# Phase 2: Git Module Overhaul - Research

**Researched:** 2026-02-12
**Domain:** Git configuration, credential management, SSH commit signing, diff/merge tools
**Confidence:** HIGH

## Summary

This phase updates the dotfiles git module to match all personal git configuration from the old laptop while excluding corporate configurations. The primary technical domains are:

1. **1Password SSH commit signing** - Modern SSH-based signing replaces GPG
2. **Git credential helper management** - Proper precedence and GitHub CLI integration
3. **Kaleidoscope diff/merge tool** - Commercial macOS visual diff tool configuration
4. **Git best practices** - Global ignore, default branch, autosquash, core settings

The research confirms all required configurations are well-documented and widely supported. No blockers identified. The main risk areas are credential helper conflicts (multiple helpers configured incorrectly) and SSH signing key configuration (requires 1Password GUI interaction to get public key).

**Primary recommendation:** Use 1Password's automatic git config setup for SSH signing, manually configure credential helpers with proper reset syntax to avoid conflicts, and verify Kaleidoscope is installed before configuring ksdiff paths.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| git | 2.34+ | Version control | SSH signing requires 2.34+, current stable is 2.x |
| 1Password | 8+ | SSH key management & signing | Industry standard password manager with SSH agent |
| GitHub CLI (gh) | 2.0+ | GitHub credential helper | Official GitHub authentication for git operations |
| Kaleidoscope | 5.0+ | Visual diff/merge tool | Commercial macOS diff tool with deep git integration |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| git-delta | Latest | Enhanced diff output | Optional, for better terminal diff visualization |
| git-flow | Latest | Git workflow tooling | Optional, if using git-flow branching model |
| GNU Stow | Latest | Dotfiles symlink management | For deploying dotfiles to home directory |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| 1Password SSH | GPG signing | GPG more complex, SSH simpler and integrated with 1Password |
| Kaleidoscope | kdiff3, meld, p4merge | Free alternatives, but Kaleidoscope has superior macOS integration |
| gh credential helper | osxkeychain | osxkeychain works but doesn't integrate with gh CLI authentication |

**Installation:**
```bash
# Already in config.yml
brew install git git-delta gh git-flow
brew install --cask kaleidoscope

# 1Password 8 required (assumed already installed)
```

## Architecture Patterns

### Recommended Project Structure
```
modules/git/
├── config.yml                    # Module configuration (homebrew packages, stow dirs)
├── files/
│   ├── .gitconfig               # Main git configuration
│   ├── .config/
│   │   └── git/
│   │       └── ignore           # Global gitignore (preferred location)
│   └── .local/bin/
│       └── git-*                # Custom git commands
```

### Pattern 1: Credential Helper Configuration with Reset
**What:** Configure domain-specific credential helpers while resetting inherited helpers
**When to use:** When replacing system/global credential helpers for specific domains
**Example:**
```ini
# Source: https://git-scm.com/docs/gitcredentials
[credential]
  helper = osxkeychain
[credential "https://github.com"]
  helper =
  helper = !/opt/homebrew/bin/gh auth git-credential
[credential "https://gist.github.com"]
  helper =
  helper = !/opt/homebrew/bin/gh auth git-credential
```

**Key insight:** The empty `helper =` line resets the helper list for that scope, preventing helper conflicts and ensuring only the desired helper runs for GitHub URLs.

### Pattern 2: 1Password SSH Signing Configuration
**What:** Configure git to use 1Password's SSH agent for commit signing
**When to use:** When using 1Password 8+ for SSH key management
**Example:**
```ini
# Source: https://developer.1password.com/docs/ssh/git-commit-signing/
[gpg]
  format = ssh
[gpg "ssh"]
  program = "/Applications/1Password.app/Contents/MacOS/op-ssh-sign"
[commit]
  gpgsign = true
[user]
  signingkey = ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICQBsQMijqC45O4MyNbwZ7SHXR9whOy6AAdH+Z4Pz1YB
```

**Configuration flow:**
1. Create SSH key in 1Password (or import existing)
2. Use 1Password's "Configure Commit Signing" feature (auto-generates config)
3. Copy public key from 1Password
4. Add public key to GitHub as "Signing Key" (not Authentication Key)
5. Verify with `git log --show-signature`

### Pattern 3: Kaleidoscope Diff/Merge Tool
**What:** Configure ksdiff as git's visual diff and merge tool
**When to use:** When Kaleidoscope app is installed on macOS
**Example:**
```ini
# Source: https://kaleidoscope.app/ and community configurations
[diff]
  tool = Kaleidoscope
[difftool "Kaleidoscope"]
  cmd = ksdiff --partial-changeset --relative-path \"$MERGED\" -- \"$LOCAL\" \"$REMOTE\"
[difftool]
  prompt = false
[merge]
  tool = Kaleidoscope
[mergetool "Kaleidoscope"]
  cmd = ksdiff --merge --output \"$MERGED\" --base \"$BASE\" -- \"$LOCAL\" --snapshot \"$REMOTE\" --snapshot
  trustExitCode = true
[mergetool]
  prompt = false
```

**Key flags:**
- `--partial-changeset`: Shows only changed portions
- `--relative-path "$MERGED"`: Displays relative path in UI
- `--snapshot`: Marks temporary files (merge conflict resolution)
- `trustExitCode = true`: Trust ksdiff exit code (0 = success)

### Pattern 4: Global Gitignore Configuration
**What:** Configure user-specific ignore patterns separate from repository .gitignore
**When to use:** Always, for editor/OS-specific files
**Example:**
```ini
# Source: https://git-scm.com/docs/gitignore
[core]
  excludesfile = ~/.config/git/ignore
```

**Best practice:** Use `~/.config/git/ignore` (XDG standard) rather than `~/.gitignore` for better organization. This keeps user-specific ignores (IDE files, OS files, personal tools) separate from project ignores.

### Anti-Patterns to Avoid

- **Multiple conflicting credential helpers:** Don't stack helpers without understanding precedence. Always reset with `helper =` before adding new helpers for a scope.
- **Hardcoded paths in .gitconfig:** Use `~` or `$HOME` for portability, but for tools in /Applications (like 1Password), full path is required on macOS.
- **Corporate config in personal dotfiles:** Never commit corporate email, Azure DevOps credentials, or enterprise GitHub URLs to personal dotfiles.
- **Global .gitignore in repository root:** The global ignore should be in `~/.config/git/ignore` or `~/.gitignore`, NOT in the dotfiles repository root as `.gitignore` (which is for the repo itself).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSH commit signing | Custom GPG setup | 1Password SSH signing | GPG key management is complex; 1Password handles SSH agent, signing, and biometric auth |
| GitHub authentication | Manual token management | `gh auth git-credential` | GitHub CLI handles OAuth flow, token refresh, and secure storage |
| Visual diff/merge | Custom scripts with diff/patch | Kaleidoscope, kdiff3, meld | 3-way merge conflict resolution is complex; visual tools handle edge cases |
| Git credential storage | Plain text tokens | Git credential helpers | Credential helpers use OS keychain, avoiding plain text secrets |
| Global ignore patterns | Repository-specific .gitignore entries | `core.excludesfile` | Mixing user preferences with project config pollutes shared .gitignore |

**Key insight:** Git credential and signing infrastructure has many edge cases (token expiry, multi-account, SSH agent socket handling, merge conflict algorithms). Use battle-tested tools rather than custom solutions.

## Common Pitfalls

### Pitfall 1: Credential Helper Conflicts
**What goes wrong:** Multiple credential helpers configured globally and per-domain, leading to wrong credentials or auth failures.

**Why it happens:** Git config precedence (system → global → local → worktree) and credential helper chaining is subtle. Adding a domain-specific helper without resetting inherits global helpers.

**How to avoid:**
- Always use `helper =` (empty) to reset before setting domain-specific helpers
- Use `git config --show-origin --get-all credential.helper` to debug
- Test with `GIT_TRACE=1 git ls-remote https://github.com/user/repo` to see which helpers run

**Warning signs:**
- Git prompting for credentials when credentials should be cached
- Wrong username appearing in git operations
- "No credential store has been selected" errors

### Pitfall 2: SSH Signing Key Not Registered on GitHub
**What goes wrong:** Commits are signed locally but show "Unverified" on GitHub.

**Why it happens:** Git signing (local) and GitHub verification (remote) are separate. GitHub requires the public key to be registered as a "Signing Key" (not "Authentication Key").

**How to avoid:**
- After configuring git for SSH signing, copy public key from 1Password
- Add to GitHub Settings → SSH and GPG keys → New SSH key → Key type: **Signing Key**
- Verify with `git log --show-signature` (local) and check "Verified" badge on GitHub (remote)

**Warning signs:**
- Local `git log --show-signature` shows "Good signature" but GitHub shows "Unverified"
- GitHub says "We were unable to verify this signature with any of your registered SSH signing keys"

### Pitfall 3: Kaleidoscope Not in PATH
**What goes wrong:** `git difftool` or `git mergetool` fails with "ksdiff: command not found".

**Why it happens:** Kaleidoscope installs as macOS app bundle; `ksdiff` is inside bundle at `/Applications/Kaleidoscope.app/Contents/MacOS/ksdiff` but not automatically symlinked to PATH.

**How to avoid:**
- Kaleidoscope 5+ includes a "Install ksdiff Command Line Tool" option in preferences
- This creates symlink at `/usr/local/bin/ksdiff`
- Alternatively, use full path in git config (less portable)

**Warning signs:**
- `which ksdiff` returns nothing
- `git difftool` fails immediately with command not found

### Pitfall 4: Wrong core.excludesfile Path
**What goes wrong:** Global gitignore doesn't work; files that should be ignored appear in `git status`.

**Why it happens:** Two issues: (1) `core.excludesfile` points to non-existent file, or (2) using `~/.gitignore` which conflicts with repo-level ignore.

**How to avoid:**
- Use `~/.config/git/ignore` (XDG standard, no tilde expansion needed)
- Create file before setting config: `mkdir -p ~/.config/git && touch ~/.config/git/ignore`
- Verify with `git config --get core.excludesfile`

**Warning signs:**
- `.DS_Store`, IDE files, or OS-specific files show up in `git status`
- `git check-ignore -v <file>` shows no matching pattern

### Pitfall 5: Placeholder Email in Commits
**What goes wrong:** Commits have `ianderson@example.com` email, which doesn't match GitHub account.

**Why it happens:** `user.email` in .gitconfig is a placeholder; GitHub associates commits by email.

**How to avoid:**
- Set actual personal email (matching GitHub account) before first commit
- Use `git config --global user.email "actual@email.com"`
- Verify with `git config --get user.email`

**Warning signs:**
- Commits on GitHub don't show profile picture
- Contribution graph doesn't update
- GitHub shows "This commit is by a different user with the same name"

### Pitfall 6: Autosquash Without Understanding
**What goes wrong:** Interactive rebase auto-reorders commits unexpectedly.

**Why it happens:** `rebase.autosquash = true` makes `git rebase -i` automatically detect `fixup!` and `squash!` commits and reorder them. If you don't use `git commit --fixup`, this is just confusing behavior.

**How to avoid:**
- Understand workflow: `git commit --fixup <sha>` creates a commit to be squashed
- `git rebase -i --autosquash` then auto-reorders fixup commits next to their targets
- If you don't use fixup workflow, autosquash has no effect (safe to enable)

**Warning signs:**
- Interactive rebase TODO list is reordered differently than commit history
- "fixup!" or "squash!" commits appear out of order

## Code Examples

Verified patterns from official sources:

### Complete .gitconfig for Personal Use
```ini
# Source: Synthesized from official git docs and 1Password/GitHub CLI docs
[user]
  name = Ian Anderson
  email = your-personal@email.com
  signingkey = ssh-ed25519 AAAAC3Nza... # Copy from 1Password

[core]
  editor = vi
  excludesfile = ~/.config/git/ignore
  autocrlf = input

[gpg]
  format = ssh
[gpg "ssh"]
  program = "/Applications/1Password.app/Contents/MacOS/op-ssh-sign"

[commit]
  gpgsign = true

[color]
  branch = auto
  diff = auto
  interactive = auto
  status = auto

[init]
  defaultBranch = main

[credential]
  helper = osxkeychain
[credential "https://github.com"]
  helper =
  helper = !/opt/homebrew/bin/gh auth git-credential
[credential "https://gist.github.com"]
  helper =
  helper = !/opt/homebrew/bin/gh auth git-credential

[push]
  default = simple

[pull]
  rebase = true

[rebase]
  autosquash = true

[diff]
  tool = Kaleidoscope
[difftool "Kaleidoscope"]
  cmd = ksdiff --partial-changeset --relative-path \"$MERGED\" -- \"$LOCAL\" \"$REMOTE\"
[difftool]
  prompt = false

[merge]
  tool = Kaleidoscope
[mergetool "Kaleidoscope"]
  cmd = ksdiff --merge --output \"$MERGED\" --base \"$BASE\" -- \"$LOCAL\" --snapshot \"$REMOTE\" --snapshot
  trustExitCode = true
[mergetool]
  prompt = false

[alias]
  c = commit
  ca = commit -a
  cm = commit -m
  cam = commit -am
  d = diff
  dc = diff --cached
  l = log --graph --pretty=format:"%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset" --abbrev-commit
  open = "!~/.local/bin/git-open"
  browse = "!~/.local/bin/git-open"

[web]
  browser = google-chrome
```

### Global Gitignore (~/.config/git/ignore)
```
# Source: https://git-scm.com/docs/gitignore
# User-specific ignores (never commit to project .gitignore)

# macOS
.DS_Store
.AppleDouble
.LSOverride

# Editor/IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Tools
**/.claude/settings.local.json
```

### Credential Helper Reset Pattern
```bash
# Source: https://git-scm.com/docs/gitcredentials
# Reset helpers for a domain, then set new helper
git config --global credential."https://github.com".helper ""
git config --global --add credential."https://github.com".helper "!/opt/homebrew/bin/gh auth git-credential"
```

### Verify SSH Signing Setup
```bash
# Source: https://developer.1password.com/docs/ssh/git-commit-signing/
# Check configuration
git config --get gpg.format                    # Should be "ssh"
git config --get commit.gpgsign                # Should be "true"
git config --get user.signingkey               # Should be your public key

# Make a test commit
git commit --allow-empty -m "test: verify SSH signing"

# Verify signature locally
git log --show-signature -1                    # Should show "Good signature"

# Push to GitHub and check for "Verified" badge
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| GPG commit signing | SSH commit signing | Git 2.34 (2021) | Simpler setup, integrates with SSH key management |
| Manual credential storage | Credential helpers (osxkeychain, gh) | Git 2.0+ (2014) | Secure OS-level storage, no plain text tokens |
| `master` default branch | `main` default branch | GitHub 2020, Git 2.28+ | Industry standard changed, git follows |
| Manual diff/merge tools config | Tool-specific integrations | Ongoing | Tools provide auto-config (e.g., Kaleidoscope preferences) |

**Deprecated/outdated:**
- **GPG signing for new setups:** SSH signing is simpler and preferred (GPG still supported for existing setups)
- **Git Credential Manager (GCM):** Microsoft's cross-platform credential manager, superseded by platform-specific helpers (osxkeychain on macOS, gh for GitHub)
- **`push.default = simple`:** Still valid but `push.default = current` is often preferred (only pushes current branch)

## Open Questions

1. **What is the actual personal email address?**
   - What we know: Current dotfiles have placeholder `ianderson@example.com`
   - What's unclear: The actual personal email to use
   - Recommendation: Leave as `ianderson@example.com` in dotfiles with comment to update; this is a manual configuration step

2. **Is Kaleidoscope currently installed?**
   - What we know: Old laptop had it; config.yml currently lists kdiff3
   - What's unclear: Whether to install Kaleidoscope or use kdiff3
   - Recommendation: Assume Kaleidoscope is desired (from audit); add to config.yml casks

3. **Should we add ksdiff to PATH or use full path?**
   - What we know: ksdiff can be symlinked to /usr/local/bin via Kaleidoscope preferences
   - What's unclear: Whether to assume symlink exists or use full path in config
   - Recommendation: Use relative command `ksdiff` in config; document that Kaleidoscope CLI tools must be installed

4. **What is the actual SSH signing key?**
   - What we know: Key is in 1Password, format is `ssh-ed25519 AAAAC3...`
   - What's unclear: The actual public key value
   - Recommendation: Leave as `<configure via 1Password>` placeholder with comment; this requires manual 1Password interaction

## Sources

### Primary (HIGH confidence)
- [Git Official Documentation - gitcredentials](https://git-scm.com/docs/gitcredentials)
- [Git Official Documentation - gitignore](https://git-scm.com/docs/gitignore)
- [Git Official Documentation - git-config](https://git-scm.com/docs/git-config)
- [Git Official Documentation - git-rebase](https://git-scm.com/docs/git-rebase)
- [1Password Developer Docs - Sign Git commits with SSH](https://developer.1password.com/docs/ssh/git-commit-signing/)
- [1Password Developer Docs - 1Password for SSH & Git](https://developer.1password.com/docs/ssh/)
- [GitHub CLI Manual - gh auth setup-git](https://cli.github.com/manual/gh_auth_setup-git)

### Secondary (MEDIUM confidence)
- [Kaleidoscope Official Site - Git Command Line Client](https://kaleidoscope.app/setup-guides/git-command-line-client)
- [Kaleidoscope Docs - More on git difftool and git mergetool](https://kaleidoscope.app/help/docs/more-on-git-difftool-and-git-mergetool)
- [Ken Muse - Automatic SSH Commit Signing With 1Password](https://www.kenmuse.com/blog/automatic-ssh-commit-signing-with-1password/)
- [ThoughtBot - Auto-squashing Git Commits](https://thoughtbot.com/blog/autosquashing-git-commits)
- [Sebastian De Deyne - Setting up a global .gitignore file](https://sebastiandedeyne.com/setting-up-a-global-gitignore-file/)
- [Nerd Thoughts - Resolving Git Multiple Credential Helpers](https://nerdthoughts.net/posts/2018-12-26-resolving-git-multiple-credential-helpers/)

### Tertiary (LOW confidence - for awareness only)
- Community blog posts and Medium articles on git configuration patterns
- GitHub Gists with .gitconfig examples

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools are mainstream, well-documented, and officially supported
- Architecture: HIGH - Git configuration is standardized; credential helper and signing patterns verified from official docs
- Pitfalls: MEDIUM - Pitfalls derived from official docs, community troubleshooting, and common support issues; some are theoretical

**Research date:** 2026-02-12
**Valid until:** 2026-03-12 (30 days - git configuration is stable, but tool versions and macOS paths may change)
