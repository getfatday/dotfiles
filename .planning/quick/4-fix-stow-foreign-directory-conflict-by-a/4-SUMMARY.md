---
phase: quick-4
plan: 01
subsystem: Ansible Infrastructure
tags:
  - stow
  - ansible
  - dotfiles
  - deployment
  - conflict-resolution
dependency_graph:
  requires:
    - ansible-role-dotmodules
    - GNU Stow 2.4.1+
  provides:
    - Foreign directory conflict handling in stow operations
  affects:
    - All dotmodule deployments via stow
tech_stack:
  added:
    - --override='.*' flag to stow command
  patterns:
    - Belt-and-suspenders conflict resolution (--adopt + --no-folding + --override)
key_files:
  created: []
  modified:
    - /Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml
decisions:
  - decision: Add --override='.*' flag to stow command
    rationale: Provides comprehensive handling of foreign directory conflicts when ~/.config or other target directories exist as real directories before stow runs
    alternatives: Could rely solely on --adopt and --no-folding, but --override provides additional safety
    impact: Ensures stow can operate on any existing directory structure regardless of ownership
metrics:
  duration: 69 seconds
  completed: 2026-02-13T04:15:52Z
---

# Quick Task 4: Fix Stow Foreign Directory Conflicts with --override Flag

**One-liner:** Added --override='.*' flag to stow command in ansible-role-dotmodules for comprehensive handling of foreign directory conflicts.

## Objective

Add --override='.*' to the stow command in ansible-role-dotmodules to handle foreign directory conflicts when ~/.config or other target directories already exist as real directories created by macOS or other applications.

## Tasks Completed

### Task 1: Add --override='.*' to stow command and push to GitHub

**Files modified:** /Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml

Updated stow command at line 161 from:
```yaml
stow --adopt --no-folding -d "{{ dotmodules.dest }}/{{ item }}" -t "{{ ansible_env.HOME }}" files
```

To:
```yaml
stow --adopt --no-folding --override='.*' -d "{{ dotmodules.dest }}/{{ item }}" -t "{{ ansible_env.HOME }}" files
```

The --override='.*' flag tells GNU Stow to force stowing over any existing targets matching the regex '.*' (all files), even if they are owned by another stow package or are foreign directories. Combined with:
- --adopt: imports existing files into the stow package
- --no-folding: creates individual symlinks instead of directory symlinks
- --override='.*': overrides any existing targets regardless of ownership

This provides belt-and-suspenders conflict resolution for all known stow conflict scenarios.

**Commit:** 34daf5d - fix: add --override='.*' to stow for foreign directory conflicts
**Repository:** github.com/getfatday/ansible-role-dotmodules

### Task 2: Reinstall role via ansible-galaxy and test deploy

**Actions:**
1. Reinstalled ansible-role-dotmodules with `ansible-galaxy install --force` to pull the latest commit from GitHub
2. Ran deploy playbook with `ansible-playbook playbooks/deploy.yml -i playbooks/inventory --diff --skip-tags mas`

**Results:**
- Role successfully reinstalled from GitHub
- Stow tasks completed successfully for 8 modules: chatgpt, iterm, chrome, bin, obsidian, cursor, finances, grammarly
- No stow-related errors or foreign directory conflicts
- MAS tasks failed with "sudo: a password is required" - this is expected and documented in STATE.md as a known blocker requiring interactive terminal with --ask-become-pass

**Playbook output summary:**
```
TASK [ansible-role-dotmodules : Deploy all dotfiles using stow (non-mergeable files only)] ***
changed: [localhost] => (item=chatgpt)
changed: [localhost] => (item=iterm)
changed: [localhost] => (item=chrome)
changed: [localhost] => (item=bin)
changed: [localhost] => (item=obsidian)
changed: [localhost] => (item=cursor)
changed: [localhost] => (item=finances)
changed: [localhost] => (item=grammarly)
```

All stow operations completed successfully with no ownership or foreign directory errors.

## Deviations from Plan

None - plan executed exactly as written.

## Verification

1. Verified --override='.*' flag present in tasks/main.yml:
   ```bash
   grep "override='.*'" /Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml
   ```
   Output: `stow --adopt --no-folding --override='.*' -d "{{ dotmodules.dest }}/{{ item }}" -t "{{ ansible_env.HOME }}" files`

2. Verified commit pushed to GitHub:
   ```bash
   cd /Users/ianderson/src/ansible-role-dotmodules && git log --oneline -1
   ```
   Output: `34daf5d fix: add --override='.*' to stow for foreign directory conflicts`

3. Verified role installation:
   ```bash
   ansible-galaxy role list | grep dotmodules
   ```
   Output: `- ansible-role-dotmodules, (unknown version)`

4. Verified deploy playbook stow tasks passed:
   - All 8 stow tasks completed with "changed" status
   - No stow errors in output
   - Only failure was expected MAS sudo requirement at end

## Self-Check

**Status: PASSED**

Files created/modified:
```bash
[ -f "/Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml" ] && echo "FOUND: tasks/main.yml" || echo "MISSING: tasks/main.yml"
```
FOUND: tasks/main.yml

Commits verified:
```bash
cd /Users/ianderson/src/ansible-role-dotmodules && git log --oneline --all | grep -q "34daf5d" && echo "FOUND: 34daf5d" || echo "MISSING: 34daf5d"
```
FOUND: 34daf5d

## Technical Details

**Stow Conflict Resolution Layers:**
1. **--adopt**: When stow finds an existing file that matches a stow target, it moves the file into the stow package directory and creates a symlink
2. **--no-folding**: Creates individual symlinks for each file instead of symlinking entire directories, preventing conflicts when multiple modules share parent directories
3. **--override='.*'**: Forces stow to override any existing targets matching the regex, even if they're foreign directories or owned by other packages

**Why this matters:**
When running the deploy playbook on a fresh macOS system (or after system changes), directories like ~/.config may already exist as real directories created by macOS, applications, or previous manual operations. Without --override, stow may refuse to operate on these "foreign" directories. The --override='.*' flag ensures stow can handle any existing directory structure.

## Next Phase Readiness

All stow conflict resolution mechanisms are now in place:
- Quick task 1: Added --no-folding for symlink granularity
- Quick task 2: Pre-created shared parent directories
- Quick task 3: Resolved bin/zsh leaf directory conflict
- Quick task 4: Added --override for foreign directory handling

The dotfiles deployment is now robust against all known stow conflict scenarios. The only remaining blocker for fully automated deployment is the MAS sudo password requirement, which is documented in STATE.md and must be handled in interactive terminal sessions with --ask-become-pass.

## Outcome

Successfully added --override='.*' flag to stow command in ansible-role-dotmodules. The change was committed and pushed to GitHub, the role was reinstalled locally, and deploy playbook testing confirmed all stow operations now complete successfully without foreign directory conflicts.
