# Quick Task 3: Fix bin/zsh leaf directory conflict for .local/bin

## Goal
Resolve the stow ownership conflict where both `modules/bin` and `modules/zsh` claim `~/.local/bin/`. Move the one legitimate script (`setup-prezto.sh`) into the `bin` module, remove the two machine-specific symlinks (`claude`, `nano-pdf`) that were accidentally adopted, and delete `modules/zsh/files/.local/bin/` entirely.

## Context
- **Repo:** ~/src/dotfiles
- **Conflict:** Both `modules/bin/files/.local/bin/` and `modules/zsh/files/.local/bin/` exist. Stow cannot have two modules own the same leaf directory.
- **zsh module has 3 files in .local/bin/:**
  - `setup-prezto.sh` -- legitimate script, should move to bin module
  - `claude` -- symlink to `/Users/ianderson/.local/share/claude/versions/2.1.39` (machine-specific, adopted by stow, should be removed from repo)
  - `nano-pdf` -- symlink to `/Users/ianderson/.local/share/uv/tools/nano-pdf/bin/nano-pdf` (machine-specific, adopted by stow, should be removed from repo)
- **Previous fixes:** Quick task 1 added `--no-folding` to stow. Quick task 2 added parent directory pre-creation. This resolves the final leaf-level conflict.

## Tasks

### Task 1: Move setup-prezto.sh to bin module and clean up zsh module
**Objective:** Consolidate `.local/bin/` ownership under the `bin` module only.

**Steps:**
1. Copy `modules/zsh/files/.local/bin/setup-prezto.sh` to `modules/bin/files/.local/bin/setup-prezto.sh` (preserve executable permission)
2. Remove the machine-specific symlinks from git tracking:
   - `git rm modules/zsh/files/.local/bin/claude`
   - `git rm modules/zsh/files/.local/bin/nano-pdf`
3. Remove the moved script: `git rm modules/zsh/files/.local/bin/setup-prezto.sh`
4. Remove the now-empty directory: `rmdir modules/zsh/files/.local/bin/` (if git rm didn't already)
5. Also remove `modules/zsh/files/.local/` if it is now empty
6. Stage all changes: the new file in `modules/bin/files/.local/bin/setup-prezto.sh` and the removals

**Files:**
- `modules/bin/files/.local/bin/setup-prezto.sh` (created)
- `modules/zsh/files/.local/bin/setup-prezto.sh` (removed)
- `modules/zsh/files/.local/bin/claude` (removed)
- `modules/zsh/files/.local/bin/nano-pdf` (removed)
- `modules/zsh/files/.local/bin/` (directory removed)

**Verify:**
- `ls modules/bin/files/.local/bin/setup-prezto.sh` exists and is executable
- `ls modules/zsh/files/.local/bin/` fails (directory gone)
- `git status` shows clean staged changes (no untracked .local/bin remnants in zsh module)

### Task 2: Commit, push, and test deployment
**Objective:** Commit the fix, push to remote, and verify the deploy playbook runs without stow conflicts.

**Steps:**
1. Commit with message: `fix: resolve bin/zsh leaf directory conflict for .local/bin`
   - Move setup-prezto.sh from zsh to bin module
   - Remove machine-specific symlinks (claude, nano-pdf) that were accidentally adopted
2. `git push`
3. Run: `ansible-playbook ~/src/dotfiles/playbooks/deploy.yml -i ~/src/dotfiles/playbooks/inventory --diff`
4. Verify no stow errors in output

**Files:** No new files, commit only.

**Verify:**
- `git log --oneline -1` shows the fix commit
- Deploy playbook completes without stow ownership errors
- `ls -la ~/.local/bin/setup-prezto.sh` is a symlink managed by stow (points into modules/bin)

## Success Criteria
- [ ] `modules/zsh/files/.local/bin/` directory no longer exists
- [ ] `modules/bin/files/.local/bin/setup-prezto.sh` exists and is executable
- [ ] Machine-specific symlinks (claude, nano-pdf) removed from repo
- [ ] Changes committed and pushed
- [ ] Deploy playbook runs without stow leaf directory conflicts
