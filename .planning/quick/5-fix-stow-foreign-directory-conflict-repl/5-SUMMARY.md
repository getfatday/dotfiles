---
phase: quick-5
plan: 01
subsystem: dotfiles-deployment
tags: [ansible, dotfiles, symlinks, stow-replacement]
dependency_graph:
  requires: [ansible-role-dotmodules]
  provides: [direct-symlink-deployment]
  affects: [all-dotmodules]
tech_stack:
  added: []
  patterns: [ansible.builtin.find, ansible.builtin.file, force-symlink-creation]
key_files:
  created: []
  modified:
    - /Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml
decisions: []
metrics:
  duration_seconds: 120
  completed_date: 2026-02-13T04:32:27Z
---

# Quick Task 5: Replace Stow with Direct Symlink Creation

**One-liner:** Completely replaced stow with ansible.builtin.find + ansible.builtin.file to create symlinks directly, eliminating all stow-related conflicts (foreign directory, ownership, tree-folding).

## Context

Quick tasks 1-4 attempted various stow flag workarounds:
- Task 1: Added `--no-folding` (prevented tree-folding but conflicted with existing tree-fold symlinks)
- Task 2: Pre-created shared parent directories (prevented ownership conflicts)
- Task 3: Consolidated .local/bin ownership (fixed leaf directory conflict)
- Task 4: Added `--override='.*'` (attempted to override foreign directory conflicts)

None of these addressed the root cause: **stow's foreign directory handling is fundamentally incompatible with our use case where existing files/symlinks may already exist at target paths.**

## Solution

Replaced the stow command (lines 158-163 in tasks/main.yml) with three new tasks:

1. **Find all files in module files directories** - Uses `ansible.builtin.find` with `recurse: yes` and `hidden: yes` to discover all dotfiles in each module's `files/` directory.

2. **Build symlink map** - Uses Jinja2 filters to:
   - Extract file paths from find results
   - Strip module prefix with regex to get HOME-relative paths
   - Create parallel lists of source paths and destination paths

3. **Create symlinks with force** - Uses `ansible.builtin.file` with `state: link` and `force: yes` to create each symlink, **replacing any existing file or symlink** at the target path.

The `force: yes` parameter is the critical piece - it removes an existing file or symlink and replaces it with the new symlink. This handles:
- Existing regular files (like stow's --adopt)
- Existing symlinks (which stow couldn't handle)
- Missing targets (normal symlink creation)

## Implementation

### Regex Pattern

```yaml
| map('regex_replace',
    '^' + (dotmodules.dest | regex_escape) + '/[^/]+/files/(.+)$',
    '\1')
```

This strips the module prefix to get HOME-relative paths:
- `/path/to/modules/zsh/files/.zshrc` → `.zshrc`
- `/path/to/modules/bin/files/.local/bin/setup-prezto.sh` → `.local/bin/setup-prezto.sh`

### Force Symlink Creation

```yaml
ansible.builtin.file:
  src: "{{ item.0 }}"
  dest: "{{ ansible_env.HOME }}/{{ item.1 }}"
  state: link
  force: yes
```

The `force: yes` ensures idempotency - running the playbook multiple times safely replaces symlinks if module files change.

## Execution

### Task 1: Replace stow command with find+symlink

**Files modified:**
- `/Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml`

**Changes:**
- Removed stow command task (lines 158-163)
- Added ansible.builtin.find task
- Added ansible.builtin.set_fact task to build symlink_map and symlink_sources
- Added ansible.builtin.file task with force: yes

**Verification:**
```bash
$ cd /Users/ianderson/src/ansible-role-dotmodules && grep -c 'stow --' tasks/main.yml
0

$ grep 'state: link' tasks/main.yml
    state: link
    state: link

$ python3 -c "import yaml; yaml.safe_load(open('tasks/main.yml'))"
YAML is valid
```

**Commit:** `c8019c5`

### Task 2: Commit, push, reinstall role, and test deploy

**Actions:**
1. Committed and pushed changes to ansible-role-dotmodules
2. Reinstalled role via `ansible-galaxy install -r requirements.yml --force`
3. Ran full deploy with `ansible-playbook playbooks/deploy.yml -i playbooks/inventory --diff`

**Deploy results:**
- **142 tasks OK** - all dotmodules tasks completed successfully
- **3 tasks changed** - symlinks were updated from regular files to symlinks
- **No stow errors** - no "foreign directory" or "ownership" errors
- **MAS tasks failed** (expected) - requires --ask-become-pass

**Diff output showed:**
```yaml
--- before
+++ after
@@ -1,4 +1,4 @@
 {
     "path": "/Users/ianderson/.config/iterm2/scripts/setup-iterm.sh",
-    "state": "file"
+    "state": "link"
 }
```

This confirms `force: yes` successfully replaced existing files with symlinks.

**Symlink verification:**
```bash
$ ls -la ~/.local/bin/setup-prezto.sh
lrwxr-xr-x@ 1 ianderson  staff  65 Feb 12 22:31 /Users/ianderson/.local/bin/setup-prezto.sh -> /Users/ianderson/.dotmodules/bin/files/.local/bin/setup-prezto.sh

$ readlink ~/.config/iterm2/scripts/setup-iterm.sh
/Users/ianderson/.dotmodules/iterm/files/.config/iterm2/scripts/setup-iterm.sh
```

All symlinks correctly point to module files in `.dotmodules/MODULE/files/` directories.

## Deviations from Plan

None - plan executed exactly as written.

## Results

### Success Criteria Met

- ✅ tasks/main.yml uses ansible.builtin.find + ansible.builtin.file instead of stow
- ✅ ansible-playbook deploy runs cleanly (no stow errors)
- ✅ Symlinks in HOME correctly point to module files
- ✅ Change is committed, pushed, and role reinstalled

### Key Outcomes

1. **Stow completely removed** - No more dependency on GNU stow or its problematic foreign directory handling
2. **Force replacement works** - Existing files and symlinks are cleanly replaced
3. **Idempotent deployment** - Can run playbook multiple times safely
4. **Clean diffs** - Ansible shows exactly what changed (file → link)

### Files Modified

| File | Change | Purpose |
|------|--------|---------|
| /Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml | Replaced stow command with find+symlink tasks | Direct symlink creation with force: yes |

### Commits

| Repo | Hash | Message |
|------|------|---------|
| ansible-role-dotmodules | c8019c5 | fix(quick-5): replace stow with direct symlink creation via ansible file module |

## Next Steps

Quick tasks 1-5 comprehensively addressed stow issues:
- Tasks 1-4: Attempted stow flag workarounds
- Task 5: **Definitive fix** - replaced stow entirely

No further stow-related quick tasks are needed. The deployment system now uses pure Ansible for all dotfile management.

## Self-Check: PASSED

**Files created:**
```bash
$ [ -f "/Users/ianderson/src/dotfiles/.planning/quick/5-fix-stow-foreign-directory-conflict-repl/5-SUMMARY.md" ] && echo "FOUND" || echo "MISSING"
FOUND
```

**Commits exist:**
```bash
$ cd /Users/ianderson/src/ansible-role-dotmodules && git log --oneline --all | grep -q "c8019c5" && echo "FOUND: c8019c5" || echo "MISSING: c8019c5"
FOUND: c8019c5
```

**Symlinks verified:**
```bash
$ readlink ~/.local/bin/setup-prezto.sh
/Users/ianderson/.dotmodules/bin/files/.local/bin/setup-prezto.sh
```
