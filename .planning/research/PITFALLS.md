# Pitfalls Research

**Domain:** Dotfiles Audit & Ansible Migration (Corporate to Personal)
**Researched:** 2026-02-11
**Confidence:** MEDIUM-HIGH

## Critical Pitfalls

### Pitfall 1: Accidental Secret Commits

**What goes wrong:**
Authentication credentials (API keys, tokens, passwords, private keys) get accidentally committed into the dotfiles repository. Research shows 9.5% of dotfiles repos contain leaked API keys, with GitHub API keys being most common, followed by 9,452 private keys.

**Why it happens:**
- Environment variable resolution: Config systems replace `$VAR` syntax with actual values after maintenance commands
- Hidden secrets in unexpected files: `.zsh_history`, `.bash_history`, `.npmrc`, `.docker/config.json`
- Copy-paste from corporate configs that embed secrets directly
- Not using `.gitignore` for sensitive directories like `.ssh/`, `.gnupg/`

**How to avoid:**
1. Use pre-commit hooks with secret-scanning tools (gitleaks) to block commits containing credentials
2. Add `.ssh/`, `.gnupg/`, `.config/gh/`, `.aws/`, `.docker/config.json` to `.gitignore` immediately
3. Store all secrets in 1Password, reference them via environment variables or templates
4. Use `git filter-repo` (not `git filter-branch`) to scan existing history before first commit
5. After running Ansible or diagnostic commands, manually verify configs haven't resolved env vars

**Warning signs:**
- Files contain literal API keys, tokens, or password strings
- History files (`.zsh_history`, `.bash_history`) in staging area
- Config files show resolved values instead of `${VAR}` syntax
- SSH keys or GPG keys in the working tree

**Phase to address:**
**Phase 1 (Audit)** - Set up `.gitignore`, pre-commit hooks, and secret scanning BEFORE any commits. Run `gitleaks` on old laptop's home directory to identify what NOT to copy.

---

### Pitfall 2: Corporate Artifact Contamination

**What goes wrong:**
Corporate-specific configurations get copied into personal dotfiles: VPN configs, internal DNS settings, corporate CA certificates, company-specific environment variables (`HTTP_PROXY`, internal registry URLs), license keys for corporate software.

**Why it happens:**
- Wholesale copying without filtering
- Corporate configs mixed into standard files (`.zshrc` contains both personal aliases and corporate env vars)
- Not understanding which tools were corporate-managed vs. personal
- No explicit audit checklist for corporate artifacts

**How to avoid:**
1. Create audit checklist: VPN configs, internal hostnames, corporate email addresses, company domains, internal package registries
2. Grep old laptop for corporate indicators: `grep -r "expedia\|corp\|vpn\|proxy" ~/.config ~/.ssh`
3. Separate personal from corporate during audit phase - don't copy blindly
4. Review every config file for company-specific values before adding to repo
5. Use Ansible templates with personal values, not direct copies of corporate configs

**Warning signs:**
- Config files reference internal domains (`*.expedia.com`, `*.corp`)
- Environment variables point to corporate proxies or registries
- SSH config contains corporate VPN hostnames
- Git config has corporate email as default
- Homebrew taps or package sources point to internal mirrors

**Phase to address:**
**Phase 1 (Audit)** - Manual review with corporate artifact checklist. Create separate "DO NOT MIGRATE" list before any file copying begins.

---

### Pitfall 3: Homebrew Architecture Mismatch

**What goes wrong:**
Intel Homebrew at `/usr/local` gets migrated to Apple Silicon Mac, causing "Cannot install in Homebrew on ARM processor in Intel default prefix" errors. Intel binaries fail to run, dependencies break, and `brew bundle dump` crashes because Intel git doesn't work on Apple Silicon.

**Why it happens:**
- Migration Assistant copies Intel Homebrew wholesale
- Dotfiles reference `/usr/local/bin` paths that don't exist on Apple Silicon
- Dual installation complexity: leaving both Intel and ARM Homebrew creates unmaintainable conflicts
- Package lists include architecture-specific formulae that don't work cross-platform

**How to avoid:**
1. **DO NOT** use Migration Assistant for Homebrew - always reinstall from scratch
2. Export package list: `brew bundle dump` on OLD laptop (Intel), save `Brewfile` to dotfiles
3. Install native Apple Silicon Homebrew at `/opt/homebrew` on NEW machine
4. Use `brew bundle install` from saved `Brewfile` to reinstall packages natively
5. Update dotfiles to use `/opt/homebrew` paths, or use `eval "$(/opt/homebrew/bin/brew shellenv)"`
6. Remove architecture-specific packages from `Brewfile` before migration

**Warning signs:**
- Errors mentioning `/usr/local/Homebrew` on Apple Silicon
- `arch: arm64` but Homebrew prefix is `/usr/local`
- Commands fail with "Bad CPU type in executable"
- Multiple Homebrew installations detected
- Git commands crash during `brew bundle dump`

**Phase to address:**
**Phase 2 (Homebrew Migration)** - Dedicated phase for capturing Brewfile, uninstalling old Homebrew data, and clean native installation. Test Brewfile installation in Phase 3 before applying to production machine.

---

### Pitfall 4: Shell Configuration PATH Reordering

**What goes wrong:**
After migration, system binaries take precedence over Homebrew binaries despite correct `$PATH` in `.zshenv`. macOS `path_helper` utility re-orders `$PATH` to put system paths first, breaking Homebrew and custom tool installations.

**Why it happens:**
- `.zshenv` sets `$PATH` but `/etc/zprofile` runs AFTER and calls `path_helper`
- `path_helper` sees `$PATH` already contains values and re-orders to prioritize system paths
- Homebrew's `brew shellenv` triggers additional PATH reordering
- Bash-to-zsh migration uses wrong config files for `$PATH` (`.bash_profile` → `.zshrc` instead of `.zshenv`)

**How to avoid:**
1. Put `$PATH` modifications in `.zshrc` AFTER system initialization, not in `.zshenv`
2. If using Homebrew: call `eval "$(/opt/homebrew/bin/brew shellenv)"` in `.zshrc`, then append/prepend custom paths AFTER
3. Use path arrays instead of string manipulation: `path=(/custom/bin $path)`
4. Test PATH order: `echo $PATH | tr ':' '\n'` should show your custom paths before system paths
5. Understand zsh file sourcing order: `.zshenv` → `/etc/zprofile` → `.zshrc`

**Warning signs:**
- `which python` shows system Python instead of Homebrew Python
- `$PATH` looks correct in `.zshenv` but commands use wrong binaries
- Custom scripts in `~/bin` don't execute despite being in `$PATH`
- Different behavior between login shells and subshells

**Phase to address:**
**Phase 3 (Shell Config)** - After Homebrew installation verified. Test PATH order in both login and non-login shells before finalizing.

---

### Pitfall 5: Ansible Idempotency Failures

**What goes wrong:**
Ansible tasks report "changed" on every run even when nothing changed. File permissions show "changed" when using `recurse: yes`, symlinks report changes despite being identical, shell commands run unnecessarily. Makes it impossible to trust Ansible's reporting.

**Why it happens:**
- Using `ansible.builtin.shell` or `ansible.builtin.command` without proper conditionals
- File module with `recurse: yes` always reports changed (known bug)
- Symlink permission tasks not idempotent with default `follow` setting
- Using Stow via shell commands without parsing output to detect actual changes

**How to avoid:**
1. Prefer Ansible modules over shell commands: `file`, `copy`, `template` instead of `shell`
2. For unavoidable shell commands (like Stow), use `changed_when` with output parsing:
   ```yaml
   register: stow_result
   changed_when: "'LINK' in stow_result.stderr or 'UNLINK' in stow_result.stderr"
   ```
3. Avoid `recurse: yes` on file permissions - set permissions at creation time instead
4. Use `creates` and `removes` parameters for shell commands that should only run once
5. Test playbooks twice: first run should show changes, second run should show no changes

**Warning signs:**
- Every playbook run shows "changed" for same tasks
- Can't tell if deployments actually modified system
- File tasks always yellow even when re-running immediately
- No confidence in "check mode" (`--check`) accuracy

**Phase to address:**
**Phase 4 (Ansible Implementation)** - Write tasks with idempotency from start. Add verification phase that runs playbook twice and asserts zero changes on second run.

---

### Pitfall 6: Overwriting Existing Configuration

**What goes wrong:**
Ansible playbook overwrites existing dotfiles on target machine without backup, destroying months of local customization. New machine's fresh configs get replaced before being evaluated for useful differences.

**Why it happens:**
- Using `force: yes` with file/copy modules
- No backup strategy in playbook
- Not checking if target files exist and are different
- Assuming fresh machine has no useful config (false on macOS - has sensible defaults)

**How to avoid:**
1. Use `backup: yes` parameter in file/copy/template tasks
2. Before first run, manually backup target machine's existing dotfiles:
   ```bash
   mkdir -p ~/.config-backup
   mv ~/.zshrc ~/.config-backup/ 2>/dev/null || true
   ```
3. Use `diff` mode during first run: `ansible-playbook --diff`
4. Consider using `state: link` with Stow instead of copying - makes changes reversible
5. Test on VM or container before running on production machine

**Warning signs:**
- No backup directory created before deployment
- Playbook has `force: yes` without `backup: yes`
- No rollback procedure documented
- First deployment on production machine without testing

**Phase to address:**
**Phase 3 (Initial Testing)** - Test full playbook on Docker container or VM. Verify backup creation. Document rollback procedure before Phase 5 (Production Deployment).

---

### Pitfall 7: Git History Contains Old Secrets

**What goes wrong:**
Even after removing secrets from current commit, they remain in git history. Cloning repo and using `git log` reveals committed secrets from early development. Public repo exposes all historical secrets.

**Why it happens:**
- Secrets committed early in development before establishing hygiene
- Removing file from working tree doesn't remove from history
- Not understanding git's DAG structure - history is immutable without rewriting
- Using `git filter-branch` (deprecated) or BFG (less thorough) instead of `git filter-repo`

**How to avoid:**
1. Before first commit, run `gitleaks detect` on source directory
2. Never make initial commit without `.gitignore` in place
3. If secrets found in history, use `git filter-repo` to remove them completely:
   ```bash
   git filter-repo --invert-paths --path .ssh/id_rsa
   git filter-repo --replace-text secrets.txt
   ```
4. After cleaning history, force-push and inform team to re-clone (or keep private)
5. Revoke exposed credentials immediately - cleaning git history doesn't un-leak secrets

**Warning signs:**
- Old commits in `git log` show API keys or tokens
- `.ssh/` directory appears in early commits
- Files with `_history` suffix in commit history
- Grep of entire repo finds secrets: `git grep "BEGIN PRIVATE KEY"`

**Phase to address:**
**Phase 1 (Audit)** - Before first commit to new dotfiles repo. Run `gitleaks` on audit output and use `git filter-repo` if secrets found before initializing new repo.

---

### Pitfall 8: Architecture-Specific Hardcoding

**What goes wrong:**
Dotfiles hardcode Intel-specific paths, x86_64 binary locations, or Rosetta assumptions. Configs break when used on different architectures or fail when Rosetta is disabled.

**Why it happens:**
- Hardcoding `/usr/local/bin` instead of using dynamic Homebrew prefix
- Assuming binary names (some packages have `-x86_64` suffixes on Intel)
- Conditional logic based on outdated architecture detection
- Not testing configs on both architectures

**How to avoid:**
1. Use Homebrew's dynamic prefix: `$(brew --prefix)` instead of `/opt/homebrew`
2. Use `uname -m` to detect architecture and set paths conditionally:
   ```bash
   if [[ "$(uname -m)" == "arm64" ]]; then
     export HOMEBREW_PREFIX="/opt/homebrew"
   else
     export HOMEBREW_PREFIX="/usr/local"
   fi
   ```
3. Let `brew shellenv` handle path configuration instead of hardcoding
4. Avoid architecture-specific packages in `Brewfile` - use `cask` when available
5. Test dotfiles on both Intel (VM) and Apple Silicon if possible

**Warning signs:**
- Hardcoded `/usr/local` paths in shell config
- No architecture detection in dotfiles
- Errors only appear on specific Mac architectures
- Package names include architecture suffixes

**Phase to address:**
**Phase 4 (Ansible Implementation)** - Use Ansible facts to detect architecture and template configs accordingly. Phase 5 testing should verify on target architecture.

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Copying files instead of symlinking | Simpler Ansible tasks | Config drift - changes not reflected in repo | Never - use Stow or file module with state: link |
| Skipping pre-commit hooks during development | Faster commits | Secrets leak into history | Never - always use hooks from start |
| Using `shell` instead of proper Ansible modules | Easier to write familiar bash | Non-idempotent, unreliable, hard to debug | Only when no module exists AND using changed_when |
| Hardcoding paths instead of detecting | Works on current machine | Breaks on different architectures or OS versions | Never - always use dynamic detection |
| Migration Assistant for entire system | One-click migration | Brings corporate artifacts, broken Homebrew, years of cruft | Acceptable for Documents, never for configs |
| Committing before secret scan | Start repo quickly | Requires history rewriting, potential exposure | Never - scan before first commit |
| Global .gitignore only | Don't need repo-specific ignore | Secrets slip through when working in different repos | Never - each dotfiles repo needs own .gitignore |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| 1Password CLI | Hardcoding credentials in scripts | Use `op` CLI with service account token from environment variable |
| Homebrew | Installing on Intel Mac then transferring to Apple Silicon | Export Brewfile, clean install native Homebrew, bundle install from file |
| Git | Using corporate email in .gitconfig globally | Use conditional includes: `[includeIf "gitdir:~/work/"]` for work email |
| SSH | Copying entire .ssh directory including private keys to repo | Use ssh-keygen on new machine, only template config file, store keys in 1Password |
| Ansible become | Hardcoding sudo password | Use `ansible-playbook -K` to prompt, or ansible-vault for automation |
| GNU Stow | Running stow from wrong directory | Always run from dotfiles repo parent, use absolute paths in Ansible |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Recursive file permission in Ansible | Ansible tasks take minutes to complete | Set permissions at file creation, not recursively afterward | >100 files per directory |
| Large Brewfile without organization | `brew bundle install` takes hours, hard to maintain | Split into categories (core, dev, gui), use comments | >50 formulae |
| No ansible tags | Must run entire playbook for small changes | Tag tasks by category: `tags: [brew, shell, vim]` | >20 tasks |
| Copying large files instead of downloading | Slow playbook, large repo size | Use `get_url` module to download from source | Files >10MB |
| Shell history in dotfiles repo | Repo size grows indefinitely | Never commit history files - always .gitignore them | After months of use |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Public dotfiles repo with real email addresses | Spam, phishing, corporate espionage | Use templating with ansible-vault encrypted vars, or use GitHub-provided noreply email |
| SSH config with corporate VPN hosts | Exposes internal infrastructure topology | Audit SSH config before committing - remove all corporate entries |
| Committing .zsh_history or .bash_history | Exposes commands with secrets, API calls, internal hostnames | Add `*_history` to .gitignore globally and in repo |
| Using same GPG key on personal and work machines | Key compromise affects both contexts | Generate separate keys per context, store in 1Password, never commit |
| Ansible playbook cloning from public GitHub | MitM injection of malicious dotfiles | Pin to specific commit hash or tag, verify signatures |
| Storing 1Password service account token in dotfiles | Full vault access if repo compromised | Store in macOS Keychain, reference via environment variable |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No progress indication during `brew bundle install` | Appears frozen for 30+ minutes | Use `brew bundle install --verbose` or add progress hooks |
| Ansible fails midway with no rollback | System in half-configured state | Use block/rescue/always, or use Stow (symlinks easily reversed) |
| No verification checklist after deployment | Don't know if migration succeeded | Create test script: check PATH order, verify tool versions, test key commands |
| Error messages reference Ansible internals | User doesn't know what actually failed | Use `failed_when` with clear custom messages |
| No documentation of manual steps | User forgets what needs to be done outside Ansible | Maintain MANUAL_STEPS.md with checklist, include in playbook output |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Homebrew Migration:** Often missing architecture detection - verify `brew --prefix` returns `/opt/homebrew` on Apple Silicon
- [ ] **SSH Config:** Often missing `IdentitiesOnly yes` - verify connections don't try all keys in agent
- [ ] **Git Config:** Often missing conditional includes for work/personal - verify `git config user.email` in different directories
- [ ] **Pre-commit Hooks:** Often installed but not configured - verify `git commit` actually runs gitleaks
- [ ] **Ansible Idempotency:** Often looks correct but isn't - verify second playbook run shows 0 changes
- [ ] **Shell PATH:** Often set but wrong order - verify `echo $PATH | head -1` shows custom paths first
- [ ] **Secret Scanning:** Often present but not comprehensive - verify scan includes .config, .local, not just root ~
- [ ] **Backup Strategy:** Often documented but not tested - verify backup files can actually restore working config
- [ ] **1Password Integration:** Often uses CLI but hardcodes vault IDs - verify configs use generic vault references

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Secrets committed to history | HIGH | 1. Revoke exposed credentials immediately 2. Use `git filter-repo --replace-text` 3. Force push 4. Notify team to re-clone 5. Make repo private if public |
| Homebrew architecture mismatch | MEDIUM | 1. Uninstall all Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/uninstall.sh)"` 2. Remove `/usr/local/Homebrew` 3. Install native: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` 4. `brew bundle install` |
| Overwritten config without backup | MEDIUM | 1. Check for `.backup` files created by Ansible 2. Check Time Machine if on macOS 3. If using Stow: `stow -D package` to remove symlinks 4. Re-run system defaults or restore from fresh macOS install |
| PATH order broken | LOW | 1. Clear PATH caches: `hash -r` 2. Restart shell 3. Move PATH modification to after `brew shellenv` 4. Use path arrays instead of string concat |
| Ansible non-idempotent | LOW | 1. Add `changed_when` to shell tasks 2. Replace shell with proper modules 3. Add `creates`/`removes` where applicable 4. Test with `--check` mode |
| Corporate artifacts in repo | MEDIUM | 1. `git filter-repo --path-glob '*expedia*' --invert-paths` 2. Manual review of all files 3. Force push 4. Revoke any corporate credentials that leaked |
| Git history with secrets | HIGH | Same as "Secrets committed" above |
| Broken shell config | LOW | 1. Boot into recovery mode or login as different user 2. `mv ~/.zshrc ~/.zshrc.broken` 3. Restore from backup 4. Debug broken config in isolation |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Accidental Secret Commits | Phase 1: Audit Setup | Pre-commit hook blocks test secret, gitleaks passes on clean repo |
| Corporate Artifact Contamination | Phase 1: Audit Execution | Grep for corporate domains returns empty, manual checklist complete |
| Homebrew Architecture Mismatch | Phase 2: Homebrew Migration | `brew --prefix` correct for architecture, `brew doctor` passes |
| Shell PATH Reordering | Phase 3: Shell Config | `which python` shows Homebrew version, PATH order correct in both login/non-login |
| Ansible Idempotency Failures | Phase 4: Ansible Development | Second playbook run shows 0 changes, --check mode matches actual run |
| Overwriting Existing Config | Phase 3: Pre-deployment Testing | Test VM deployment creates backups, --diff shows expected changes |
| Git History Contains Secrets | Phase 1: Pre-commit Setup | `gitleaks detect` on repo history finds nothing |
| Architecture-Specific Hardcoding | Phase 4: Ansible Templates | Playbook runs successfully on both architectures (if testable) |

## Sources

**Dotfiles Migration:**
- [How to Store Dotfiles - Atlassian Git Tutorial](https://www.atlassian.com/git/tutorials/dotfiles)
- [GitHub does dotfiles](https://dotfiles.github.io/)
- [The Ultimate Guide to Mastering Dotfiles](https://www.daytona.io/dotfiles/ultimate-guide-to-dotfiles)
- [Migrating to a new Mac](https://zellwk.com/blog/mac-setup-2/)

**Secrets Management:**
- [Dotfiles Security: How to Stop Leaking Secrets on GitHub](https://instatunnel.my/blog/why-your-public-dotfiles-are-a-security-minefield)
- [Connecting the .dotfiles: Checked-In Secret](https://pure.mpg.de/rest/items/item_3505626/component/file_3505627/content)
- [How to Erase Secrets in Git Repos with git filter-repo](https://octocurious.com/blog/20240525-git-filter-repo/)
- [Organizing your dotfiles — managing secrets](https://medium.com/@htoopyaelwin/organizing-your-dotfiles-managing-secrets-8fd33f06f9bf)

**Homebrew Migration:**
- [What's the best practice to migrate from Intel to Apple Silicon HomeBrew](https://github.com/orgs/Homebrew/discussions/4506)
- [Migrate from Intel (Rosetta2) to ARM brew on M1](https://github.com/orgs/Homebrew/discussions/417)
- [A minimalist guide to migrate Homebrew from Intel to Apple Silicon](https://medium.com/@ravi.mba.techie/a-minimalist-guide-to-migrate-homebrew-from-intel-macs-to-apple-silicon-macs-in-a-simple-5-steps-3e545576dab5)
- [Migrating Homebrew from an Intel to an Apple Silicon Mac](https://ericswpark.com/blog/2023/2023-06-17-migrating-homebrew-from-intel-to-asi-mac/)

**Shell Configuration:**
- [Moving to zsh, part 2: Configuration Files](https://scriptingosx.com/2019/06/moving-to-zsh-part-2-configuration-files/)
- [Properly setting $PATH for zsh on macOS (fighting with path_helper)](https://gist.github.com/Linerre/f11ad4a6a934dcf01ee8415c9457e7b2)
- [The right way to migrate your bash_profile to zsh](https://carlosroso.com/the-right-way-to-migrate-your-bash-profile-to-zsh/)
- [Zsh/Bash startup files loading order](https://medium.com/@rajsek/zsh-bash-startup-files-loading-order-bashrc-zshrc-etc-e30045652f2e)

**Ansible Best Practices:**
- [Ansible for dotfiles: the introduction I wish I've had](https://phelipetls.github.io/posts/introduction-to-ansible/)
- [Manage your dotfiles with Ansible](https://medium.com/espinola-designs/manage-your-dotfiles-with-ansible-6dbedd5532bb)
- [What is idempotency in Ansible?](https://medium.com/@haroldfinch01/what-is-idempotency-in-ansible-9d264c116193)
- [File module not idempotent with symlink perms - Issue #56928](https://github.com/ansible/ansible/issues/56928)

---
*Pitfalls research for: Dotfiles Audit & Ansible Migration*
*Researched: 2026-02-11*
