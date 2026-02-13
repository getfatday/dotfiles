---
phase: quick-5
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - /Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml
autonomous: true

must_haves:
  truths:
    - "Dotfiles deploy without stow and without any foreign directory errors"
    - "Each module's files are symlinked individually into HOME at correct relative paths"
    - "Existing files/symlinks at target paths are replaced with correct symlinks"
    - "Parent directories are created as real directories (not symlinks)"
  artifacts:
    - path: "/Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml"
      provides: "Direct symlink deployment replacing stow command"
      contains: "ansible.builtin.file"
  key_links:
    - from: "ansible.builtin.find"
      to: "ansible.builtin.file (state: link)"
      via: "find files in module/files/, symlink each to HOME/relative_path"
      pattern: "state:\\s*link"
---

<objective>
Replace stow with direct symlink creation using ansible.builtin.file module in ansible-role-dotmodules.

Purpose: Eliminate ALL stow-related issues (foreign directory conflicts, tree-folding, ownership tracking) by creating symlinks directly with Ansible. Quick tasks 1-4 all attempted stow flag workarounds; this is the definitive fix.

Output: Updated tasks/main.yml committed, pushed, reinstalled via ansible-galaxy, and tested with a real deploy.
</objective>

<execution_context>
@/Users/ianderson/.claude/get-shit-done/workflows/execute-plan.md
@/Users/ianderson/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/Users/ianderson/src/dotfiles/.planning/STATE.md
@/Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml
</context>

<tasks>

<task type="auto">
  <name>Task 1: Replace stow command with find+symlink in tasks/main.yml</name>
  <files>/Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml</files>
  <action>
In /Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml, replace the stow deployment task (lines 158-163) with direct symlink creation. The replacement should:

1. KEEP the existing pre-create directory tasks (lines 123-156) — they are still useful and correct.

2. REPLACE the stow task block (lines 158-163, the "Deploy all dotfiles using stow" task) with these tasks:

   a. **Find all files in each module's files directory:**
      ```yaml
      - name: Find all files in module files directories
        ansible.builtin.find:
          paths: "{{ dotmodules.dest }}/{{ item }}/files"
          recurse: yes
          file_type: file
          hidden: yes
        register: module_files
        loop: "{{ stow_dirs_filtered }}"
        when: stow_dirs_filtered | length > 0
      ```

   b. **Build a flat list of {src, dest} pairs for symlinking:**
      ```yaml
      - name: Build symlink map from module files
        ansible.builtin.set_fact:
          symlink_map: >-
            {{
              module_files.results
              | selectattr('files', 'defined')
              | map(attribute='files')
              | flatten
              | map(attribute='path')
              | map('regex_replace',
                  '^' + (dotmodules.dest | regex_escape) + '/[^/]+/files/(.+)$',
                  '\1')
              | list
            }}
          symlink_sources: >-
            {{
              module_files.results
              | selectattr('files', 'defined')
              | map(attribute='files')
              | flatten
              | map(attribute='path')
              | list
            }}
        when: stow_dirs_filtered | length > 0
      ```

   c. **Create symlinks with force (handles existing files/symlinks):**
      ```yaml
      - name: Create dotfile symlinks in HOME
        ansible.builtin.file:
          src: "{{ item.0 }}"
          dest: "{{ ansible_env.HOME }}/{{ item.1 }}"
          state: link
          force: yes
        loop: "{{ symlink_sources | zip(symlink_map) | list }}"
        loop_control:
          label: "{{ item.1 }}"
        when: symlink_map is defined and symlink_map | length > 0
      ```

3. REMOVE the stow task comment on line 158 ("# Run Stow once for all modules...").

4. DO NOT touch anything else in the file — leave merge_files, conflict_resolution, homebrew, git_repositories, and all other tasks unchanged.

**Important implementation notes:**
- `force: yes` on `ansible.builtin.file` with `state: link` will remove an existing file or symlink and replace it with the new symlink. This is the equivalent of stow's --adopt behavior but works with symlinks too.
- `hidden: yes` on `ansible.builtin.find` ensures dotfiles (files starting with `.`) inside the files/ directory are found.
- The regex_replace strips the module prefix to get the HOME-relative path (e.g., `/path/to/modules/zsh/files/.zshrc` becomes `.zshrc`).
- The zip approach pairs source paths with their relative destinations.
  </action>
  <verify>
    1. `cd /Users/ianderson/src/ansible-role-dotmodules && grep -c 'stow' tasks/main.yml` should return 0 (or only appear in variable names like stow_dirs_filtered which are fine to keep for now).
    2. `grep 'state: link' tasks/main.yml` shows the new symlink task.
    3. `grep 'ansible.builtin.find' tasks/main.yml` shows the file discovery task.
    4. `python3 -c "import yaml; yaml.safe_load(open('tasks/main.yml'))"` in the ansible-role-dotmodules directory confirms valid YAML.
  </verify>
  <done>
    The stow command task is completely replaced with find+symlink tasks. The YAML is valid. No reference to the `stow` command remains in task actions (variable names like stow_dirs_filtered are acceptable).
  </done>
</task>

<task type="auto">
  <name>Task 2: Commit, push, reinstall role, and test deploy</name>
  <files>/Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml</files>
  <action>
1. **Commit and push in ansible-role-dotmodules:**
   ```bash
   cd /Users/ianderson/src/ansible-role-dotmodules
   git add tasks/main.yml
   git commit -m "fix: replace stow with direct symlink creation via ansible file module

   Stow's foreign directory handling is fundamentally broken for our use case:
   --override only handles inter-package conflicts, not foreign targets.
   --adopt only handles real files, not existing symlinks.
   --no-folding prevents tree-folding but conflicts with prior tree-fold symlinks.

   Replace with ansible.builtin.find + ansible.builtin.file (state: link, force: yes)
   which handles all cases: existing files, existing symlinks, and missing targets."
   git push origin main
   ```

2. **Reinstall the role via ansible-galaxy:**
   ```bash
   cd /Users/ianderson/src/dotfiles
   ansible-galaxy install -r requirements.yml --force
   ```

3. **Run a deploy test (skip homebrew/MAS for speed):**
   ```bash
   cd /Users/ianderson/src/dotfiles
   ansible-playbook playbooks/deploy.yml -i playbooks/inventory --tags dotmodules --diff
   ```
   If the playbook requires become password, run without --ask-become-pass first to see if dotmodules tag works without privilege escalation. The dotmodules tasks should NOT need sudo.

4. **Verify symlinks were created correctly:**
   ```bash
   ls -la ~/.zshrc ~/.config/git/config ~/.config/starship.toml 2>/dev/null
   ```
   Each should be a symlink pointing into the dotfiles/modules/ tree.
  </action>
  <verify>
    1. `cd /Users/ianderson/src/ansible-role-dotmodules && git log --oneline -1` shows the commit.
    2. `ansible-galaxy list | grep dotmodules` confirms the role is installed.
    3. The ansible-playbook run completes without "existing target is not owned by stow" errors.
    4. `readlink ~/.zshrc` or similar shows symlink target in dotfiles/modules/.
  </verify>
  <done>
    Role is committed, pushed, reinstalled. Deploy runs cleanly with no stow errors. Symlinks in HOME point to correct module files.
  </done>
</task>

</tasks>

<verification>
1. No stow command references remain in tasks/main.yml (variable names stow_dirs_filtered are acceptable)
2. Deploy playbook runs without foreign directory errors
3. Dotfile symlinks are correctly created in HOME
4. The fix is pushed to GitHub and the role is reinstalled locally
</verification>

<success_criteria>
- tasks/main.yml uses ansible.builtin.find + ansible.builtin.file instead of stow
- ansible-playbook deploy runs cleanly with --tags dotmodules
- Symlinks in HOME correctly point to module files
- Change is committed, pushed, and role reinstalled
</success_criteria>

<output>
After completion, create `.planning/quick/5-fix-stow-foreign-directory-conflict-repl/5-SUMMARY.md`
</output>
