# Quick Task 2: Fix stow directory ownership conflicts

## Goal
Pre-create shared parent directories before the stow loop runs in ansible-role-dotmodules, so that multiple modules stowing into the same parent (e.g. `~/.config`, `~/.local/bin`) don't conflict.

## Context
- **Repo:** ~/src/ansible-role-dotmodules
- **File to modify:** tasks/main.yml
- **Stow command location:** Line 124-128 (the "Deploy all dotfiles using stow" task)
- **Current stow flags:** `--adopt --no-folding` (keep both)

## Tasks

### Task 1: Add pre-create directories task to tasks/main.yml
**Objective:** Insert Ansible tasks BEFORE the stow loop (line 124) that scan all modules' `files/` directories, collect unique parent directory paths, and `mkdir -p` them in `$HOME`.

**Implementation:**
1. Add a task that uses `ansible.builtin.find` with `recurse: yes` and `file_type: directory` to scan `{{ dotmodules.dest }}/{{ item }}/files/` for each module in `stow_dirs_filtered`
2. Collect all unique relative directory paths found
3. Add a task using `ansible.builtin.file` with `state: directory` to create each path under `{{ ansible_env.HOME }}`
4. Keep existing `--adopt --no-folding` flags on the stow command

**Files:** ~/src/ansible-role-dotmodules/tasks/main.yml

**Commit:** Atomic commit in ansible-role-dotmodules repo with message: "fix: pre-create shared parent dirs before stow to prevent ownership conflicts"

### Task 2: Push, reinstall role, and test
**Objective:** Push the fix upstream, reinstall via ansible-galaxy, and run the deploy playbook.

**Steps:**
1. `cd ~/src/ansible-role-dotmodules && git push`
2. `ansible-galaxy install -r ~/src/dotfiles/playbooks/requirements.yml --force`
3. `ansible-playbook ~/src/dotfiles/playbooks/deploy.yml -i ~/src/dotfiles/playbooks/inventory --diff`

**Commit:** No additional commit needed in dotfiles repo (role is external dependency)

## Success Criteria
- [ ] tasks/main.yml has pre-create directory task before stow loop
- [ ] Stow command still uses --adopt --no-folding
- [ ] Changes committed and pushed to github.com/getfatday/ansible-role-dotmodules
- [ ] Role reinstalled via ansible-galaxy
- [ ] Deploy playbook runs without stow ownership conflicts
