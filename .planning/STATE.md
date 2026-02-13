# Project State

## Current Position

- **Phase:** 7/7 (Validation & Deploy)
- **Plan:** 1 of 1 complete
- **Status:** All phases complete — real deploy deferred to interactive terminal
- **Last activity:** 2026-02-13 — Replaced stow with direct symlink creation (quick task 5)

Progress: ██████████ 100% (7/7 phases complete)

## Decisions Made

| Phase | Decision | Rationale |
|-------|----------|-----------|
| 02 | Placeholder email and SSH signing key | Requires manual 1Password GUI interaction |
| 02 | Switched excludesfile to ~/.config/git/ignore | XDG standard, better separation |
| 02 | Removed google-chrome from git casks | Not a git dependency |
| 03 | Removed productivity content from zsh module .zshrc | Content was duplicate of productivity module; modular architecture requires each module to own its own content |
| 03 | Disabled SSH signing for plan execution commits | Placeholder SSH key from phase 02 causes commit failures; manual 1Password configuration required |
| 03 | Use brew --prefix instead of architecture detection | More reliable than uname -m, handles relocatable installs |
| 03 | Remove hardcoded paths from node module PATH | Homebrew and Python paths belong in respective modules, not node module |
| 04 | Skip 04-02 old laptop script migration | Old laptop volume at /Volumes/Macintosh HD-1/ is disconnected |
| 05 | Guard cargo env with file existence test | Prevents errors if rustup not yet initialized |
| 05 | Exclude hosts.yml from git module | Contains OAuth tokens from gh auth login |
| 07 | Defer real deploy to interactive terminal | MAS apps require sudo password via --ask-become-pass |
| quick-1 | Disabled SSH signing for ansible-role-dotmodules commits | Same placeholder SSH key issue as dotfiles repo |
| quick-2 | Pre-create shared parent directories before stow | Prevents ownership conflicts when multiple modules stow into same parent (.config, .local) |
| quick-3 | Consolidate .local/bin ownership to bin module | Resolves leaf directory conflict — zsh's setup-prezto.sh moved to bin, machine-specific symlinks removed |

## Blockers/Concerns Carried Forward

**SSH Signing:** Commits require `git config --local commit.gpgsign false` until 1Password SSH key is configured manually via 1Password GUI. This is a temporary workaround documented in phase 02 decisions.

**Old Laptop Volume:** Disconnected. Phase 4 Plan 02 and any future tasks requiring /Volumes/Macintosh HD-1/ are blocked.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | Fix stow conflicts by adding --no-folding to ansible-role-dotmodules | 2026-02-12 | 6817fc2 | [1-fix-stow-conflicts-by-adding-no-folding-](./quick/1-fix-stow-conflicts-by-adding-no-folding-/) |
| 2 | Pre-create shared parent dirs before stow to prevent ownership conflicts | 2026-02-13 | 9884720 | [2-fix-stow-directory-ownership-conflicts-i](./quick/2-fix-stow-directory-ownership-conflicts-i/) |
| 3 | Fix bin/zsh leaf directory conflict for .local/bin | 2026-02-13 | 722bfe2 | [3-fix-bin-zsh-leaf-directory-conflict-for-](./quick/3-fix-bin-zsh-leaf-directory-conflict-for-/) |
| 4 | Add --override='.*' to stow for foreign directory conflicts | 2026-02-13 | 34daf5d | [4-fix-stow-foreign-directory-conflict-by-a](./quick/4-fix-stow-foreign-directory-conflict-by-a/) |
| 5 | Replace stow with direct symlink creation via ansible.builtin.file | 2026-02-13 | c8019c5 | [5-fix-stow-foreign-directory-conflict-repl](./quick/5-fix-stow-foreign-directory-conflict-repl/) |

## Session Continuity

- **Last session:** 2026-02-13
- **Stopped at:** Quick task 5 complete — Replaced stow with direct symlink creation
- **Resume file:** All phases complete; stow completely removed from deployment
- **Remaining:**
  - Run `ansible-playbook playbooks/deploy.yml -i playbooks/inventory --ask-become-pass --diff` interactively for MAS apps
