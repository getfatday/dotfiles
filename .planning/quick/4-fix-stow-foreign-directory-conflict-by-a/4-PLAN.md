---
phase: quick-4
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - /Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml
autonomous: true

must_haves:
  truths:
    - "stow command includes --override='.*' flag to handle foreign directory conflicts"
    - "ansible-role-dotmodules is committed and pushed to github.com/getfatday/ansible-role-dotmodules"
    - "ansible-galaxy role is reinstalled with the updated version"
    - "ansible-playbook deploy runs without stow errors"
  artifacts:
    - path: "/Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml"
      provides: "Updated stow command with --override flag"
      contains: "--override='.*'"
  key_links:
    - from: "/Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml"
      to: "stow CLI invocation"
      via: "ansible.builtin.command"
      pattern: "stow --adopt --no-folding --override='.*'"
---

<objective>
Add --override='.*' to the stow command in ansible-role-dotmodules to handle foreign directory conflicts, then commit, push, reinstall via ansible-galaxy, and test deploy.

Purpose: When ~/.config or other target directories already exist as real directories (created by macOS or other apps before the playbook runs), stow may refuse to operate on them as "foreign" directories not owned by stow. The --override='.*' flag tells stow to override any existing targets regardless of ownership, providing a belt-and-suspenders fix alongside the existing --adopt and --no-folding flags.

Output: Updated role pushed to GitHub, reinstalled locally, deploy tested.
</objective>

<execution_context>
@/Users/ianderson/.claude/get-shit-done/workflows/execute-plan.md
@/Users/ianderson/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml
@/Users/ianderson/src/dotfiles/requirements.yml
@/Users/ianderson/src/dotfiles/playbooks/deploy.yml
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add --override='.*' to stow command and push to GitHub</name>
  <files>/Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml</files>
  <action>
In /Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml, find the stow command task at line 160 ("Deploy all dotfiles using stow"):

Current command (line 161):
```
stow --adopt --no-folding -d "{{ dotmodules.dest }}/{{ item }}" -t "{{ ansible_env.HOME }}" files
```

Change to:
```
stow --adopt --no-folding --override='.*' -d "{{ dotmodules.dest }}/{{ item }}" -t "{{ ansible_env.HOME }}" files
```

The --override='.*' flag is placed after --no-folding and before -d. This tells GNU stow (v2.4.1) to force stowing over any existing targets matching the regex '.*' (i.e., all files), even if they are owned by another stow package or are foreign. Combined with --adopt (which imports existing files into the stow package) and --no-folding (which creates individual symlinks instead of directory symlinks), this handles all known conflict scenarios.

After editing, commit the change in the ansible-role-dotmodules repo:
```bash
cd /Users/ianderson/src/ansible-role-dotmodules
git add tasks/main.yml
git commit -m "fix: add --override='.*' to stow for foreign directory conflicts"
git push origin main
```

Note: SSH signing is already disabled in this repo (commit.gpgsign=false).
  </action>
  <verify>
1. Verify the file contains the updated stow command:
   grep "override='.*'" /Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml
2. Verify the commit was pushed:
   cd /Users/ianderson/src/ansible-role-dotmodules && git log --oneline -1
   git status (should show clean, up to date with origin/main)
  </verify>
  <done>tasks/main.yml contains stow --adopt --no-folding --override='.*' and the change is committed and pushed to GitHub</done>
</task>

<task type="auto">
  <name>Task 2: Reinstall role via ansible-galaxy and test deploy</name>
  <files></files>
  <action>
1. Reinstall the role from GitHub with --force to pick up the new commit:
```bash
ansible-galaxy install -r /Users/ianderson/src/dotfiles/requirements.yml --force
```

2. Run the deploy playbook to test (skip MAS tasks which require --ask-become-pass):
```bash
cd /Users/ianderson/src/dotfiles
ansible-playbook playbooks/deploy.yml -i playbooks/inventory --diff --skip-tags mas 2>&1
```

If --skip-tags doesn't work (the MAS tasks may not be tagged), use --check mode or just run it and accept the MAS failure at the end as expected (it's a known blocker per STATE.md -- "MAS apps require sudo password via --ask-become-pass").

The key verification is that the stow tasks complete successfully without "existing target is not owned by stow" errors. The MAS failure at the end is expected and unrelated.
  </action>
  <verify>
1. ansible-galaxy install output shows the role was installed successfully
2. ansible-playbook output shows "Deploy all dotfiles using stow" tasks completed (changed or ok, not failed)
3. No stow-related error messages in the output
  </verify>
  <done>ansible-role-dotmodules reinstalled from GitHub, deploy playbook stow tasks pass without foreign directory errors</done>
</task>

</tasks>

<verification>
1. grep "override='.*'" /Users/ianderson/src/ansible-role-dotmodules/tasks/main.yml returns the updated line
2. cd /Users/ianderson/src/ansible-role-dotmodules && git log --oneline -1 shows the fix commit
3. ansible-galaxy role list | grep dotmodules confirms role is installed
4. Deploy playbook stow tasks completed without errors
</verification>

<success_criteria>
- stow command in tasks/main.yml includes --override='.*' flag
- Change committed and pushed to github.com/getfatday/ansible-role-dotmodules
- Role reinstalled via ansible-galaxy --force
- Deploy playbook stow tasks pass (MAS sudo failure is expected/known)
</success_criteria>

<output>
After completion, create `.planning/quick/4-fix-stow-foreign-directory-conflict-by-a/4-SUMMARY.md`
</output>
