---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - ~/src/ansible-role-dotmodules/tasks/main.yml
autonomous: true

must_haves:
  truths:
    - "stow --no-folding is present in the stow command so multiple modules can target ~/.config without conflicts"
    - "All local improvements from the installed role are committed upstream so the source repo is authoritative"
    - "ansible-galaxy reinstall pulls the fixed version into ~/.ansible/roles/"
  artifacts:
    - path: "~/src/ansible-role-dotmodules/tasks/main.yml"
      provides: "Fixed stow command with --no-folding and all accumulated improvements"
      contains: "--no-folding"
  key_links:
    - from: "~/src/ansible-role-dotmodules (GitHub repo)"
      to: "~/.ansible/roles/ansible-role-dotmodules (installed role)"
      via: "ansible-galaxy install -r requirements.yml --force"
      pattern: "git+https://github.com/getfatday/ansible-role-dotmodules"
---

<objective>
Sync the upstream ansible-role-dotmodules repo with all local improvements that were made directly to the installed role, including the critical --no-folding fix for stow multi-module conflicts. Then reinstall the role via ansible-galaxy so the installed copy matches the source of truth.

Purpose: When multiple dotmodules target ~/.config, stow without --no-folding creates a directory symlink for the first module, then subsequent modules fail with "existing target is not owned by stow: .config". The --no-folding flag forces stow to create real directories, allowing multiple modules to coexist. Additionally, several other improvements (git repos support, homebrew taps, improved mergeable file filtering, per-item brew install) were made to the installed role but never pushed upstream.

Output: Updated upstream repo with all fixes pushed, and freshly installed role via ansible-galaxy.
</objective>

<execution_context>
@/Users/ianderson/.claude/get-shit-done/workflows/execute-plan.md
@/Users/ianderson/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
The installed role at ~/.ansible/roles/ansible-role-dotmodules/tasks/main.yml has diverged from the source repo at ~/src/ansible-role-dotmodules/tasks/main.yml. A diff reveals these changes in the installed version that need to be ported upstream:

1. **--no-folding on stow command** (the primary fix): line 133 `stow --adopt` -> `stow --adopt --no-folding`
2. **Improved mergeable files filtering**: The installed version uses a simpler single set_fact with inline conditional instead of initializing an empty list and looping with a separate when clause.
3. **Git repositories installation task**: New task block to clone/update git repos from config before Homebrew runs.
4. **Homebrew taps support**: New task to tap configured homebrew taps.
5. **Per-item homebrew install**: Changed from passing full list to `name:` to looping with `loop:` for packages and casks (more resilient to individual failures).

Source repo: ~/src/ansible-role-dotmodules (remote: https://github.com/getfatday/ansible-role-dotmodules.git)
Installed role: ~/.ansible/roles/ansible-role-dotmodules
Role requirements: ~/src/dotfiles/requirements.yml
</context>

<tasks>

<task type="auto">
  <name>Task 1: Copy installed role improvements to source repo and push</name>
  <files>~/src/ansible-role-dotmodules/tasks/main.yml</files>
  <action>
    Copy the contents of ~/.ansible/roles/ansible-role-dotmodules/tasks/main.yml over ~/src/ansible-role-dotmodules/tasks/main.yml. This is the simplest and most reliable approach since the installed version IS the desired state with all improvements.

    After copying, verify the key changes are present:
    - `--no-folding` flag on the stow command
    - Git repositories installation task
    - Homebrew taps task
    - Per-item loop for homebrew packages and casks
    - Improved mergeable files filtering

    Then commit and push to origin/main:
    - Commit message: "fix: add --no-folding to stow and sync accumulated improvements"
    - Push to origin main

    IMPORTANT: Do NOT modify any other files in the repo. Only tasks/main.yml has diverged.
  </action>
  <verify>
    Run: `cd ~/src/ansible-role-dotmodules && git diff HEAD~1 --stat` to confirm only tasks/main.yml changed.
    Run: `grep -- '--no-folding' ~/src/ansible-role-dotmodules/tasks/main.yml` to confirm the flag is present.
    Run: `cd ~/src/ansible-role-dotmodules && git log --oneline -1` to confirm commit exists.
    Run: `cd ~/src/ansible-role-dotmodules && git status` to confirm clean and up to date with remote.
  </verify>
  <done>Source repo at ~/src/ansible-role-dotmodules has tasks/main.yml matching the installed role, committed and pushed to GitHub.</done>
</task>

<task type="auto">
  <name>Task 2: Reinstall role via ansible-galaxy to confirm round-trip</name>
  <files>~/.ansible/roles/ansible-role-dotmodules/tasks/main.yml</files>
  <action>
    Reinstall the role using ansible-galaxy from the dotfiles project:

    ```
    cd ~/src/dotfiles && ansible-galaxy install -r requirements.yml --force
    ```

    This will pull the freshly-pushed version from GitHub and overwrite the installed role directory. After installation, diff the source and installed versions to confirm they match.
  </action>
  <verify>
    Run: `diff ~/src/ansible-role-dotmodules/tasks/main.yml ~/.ansible/roles/ansible-role-dotmodules/tasks/main.yml` — should produce NO output (files identical).
    Run: `grep -- '--no-folding' ~/.ansible/roles/ansible-role-dotmodules/tasks/main.yml` — should show the stow line with --no-folding.
  </verify>
  <done>Installed role at ~/.ansible/roles/ansible-role-dotmodules matches the source repo exactly. The --no-folding fix is live and will be used on next ansible-playbook run.</done>
</task>

</tasks>

<verification>
1. `grep -- '--no-folding' ~/src/ansible-role-dotmodules/tasks/main.yml` shows the flag
2. `diff ~/src/ansible-role-dotmodules/tasks/main.yml ~/.ansible/roles/ansible-role-dotmodules/tasks/main.yml` produces no output
3. `cd ~/src/ansible-role-dotmodules && git log --oneline -1` shows the fix commit
4. `cd ~/src/ansible-role-dotmodules && git status` shows clean, up to date with origin/main
</verification>

<success_criteria>
- The stow command in ansible-role-dotmodules includes --no-folding
- All accumulated local improvements are committed and pushed to the GitHub repo
- ansible-galaxy reinstall produces an installed role identical to the source repo
- Multiple dotmodules targeting ~/.config will no longer conflict on next deploy
</success_criteria>

<output>
After completion, create `.planning/quick/1-fix-stow-conflicts-by-adding-no-folding-/1-SUMMARY.md`
</output>
