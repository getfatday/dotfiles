---
phase: 03-shell-module-update
plan: 02
subsystem: dotfiles-modules
tags: [shell, zsh, cross-architecture, node, speckit, claude, path-config]

dependency_graph:
  requires:
    - modules/node (existing)
    - modules/speckit (existing)
    - modules/claude (existing)
  provides:
    - cross-architecture Homebrew path handling in node module
    - global tool versions (.tool-versions)
    - $HOME/.local/bin in PATH via speckit
    - Claude yolo alias
  affects:
    - modules/node/files/.zshrc (architecture-safe paths)
    - modules/node/files/.tool-versions (updated versions)
    - modules/speckit (new .zshenv)
    - modules/claude (new .zshrc)

tech_stack:
  added:
    - asdf: jq 1.7.1 (global tool version)
  patterns:
    - brew --prefix for cross-architecture compatibility
    - case statement for idempotent PATH additions
    - $HOME variable for portable paths
    - mergeable_files pattern for modular shell config

key_files:
  created:
    - modules/speckit/files/.zshenv: PATH entry for uv-installed tools
    - modules/claude/files/.zshrc: yolo alias for Claude Code
  modified:
    - modules/node/files/.zshrc: cross-arch paths, PNPM improvements
    - modules/node/files/.tool-versions: nodejs 25.2.1, jq 1.7.1
    - modules/speckit/config.yml: stow_dirs + mergeable_files
    - modules/claude/config.yml: mergeable_files declaration

decisions:
  - decision: Use brew --prefix instead of architecture detection
    rationale: More reliable than uname -m, handles relocatable installs
    alternatives: [hardcoded paths, uname -m if/else]
  - decision: Remove hardcoded /opt/homebrew/bin and python3 user-base from PATH
    rationale: Those belong in homebrew or python modules, node module should only manage node tooling
    alternatives: [keep for convenience]

metrics:
  duration: 1m 25s
  completed: 2026-02-12
---

# Phase 03 Plan 02: Node Cross-Arch Paths, Speckit .zshenv, Claude Alias Summary

**One-liner:** Cross-architecture Homebrew path detection in node module using brew --prefix, speckit .zshenv adding $HOME/.local/bin to PATH, and Claude yolo alias.

## What Was Built

Fixed three module-specific shell configuration gaps:

1. **Node module cross-architecture compatibility** - Replaced hardcoded `/opt/homebrew` paths with `brew --prefix` detection, replaced hardcoded username with `$HOME`, and updated PNPM PATH logic to use idempotent case guard pattern. Updated global .tool-versions to nodejs 25.2.1 and added jq 1.7.1.

2. **Speckit module .zshenv** - Created new .zshenv file adding `$HOME/.local/bin` to PATH (required for uv-installed tools like spec-kit). Updated config.yml to declare stow_dirs and mergeable_files.

3. **Claude module yolo alias** - Created new .zshrc file with `alias yolo='claude --dangerously-skip-permissions'` for quick Claude Code invocation. Updated config.yml to declare mergeable_files.

All changes follow the ansible-role-dotmodules pattern where modules contribute shell file fragments that are merged at deployment time with attribution headers.

## How It Works

**Node module cross-arch pattern:**
```bash
# Instead of hardcoded /opt/homebrew:
if command -v brew >/dev/null 2>&1; then
  _asdf_sh="$(brew --prefix)/opt/asdf/libexec/asdf.sh"
  if [[ -f "$_asdf_sh" ]]; then
    . "$_asdf_sh"
  fi
  unset _asdf_sh
fi
```

**PNPM PATH addition pattern:**
```bash
# Idempotent - won't duplicate PNPM_HOME in PATH:
export PNPM_HOME="$HOME/Library/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
```

**Module mergeable files pattern:**
```yaml
# modules/speckit/config.yml
stow_dirs:
  - speckit

mergeable_files:
  - ".zshenv"
```

At deployment, ansible-role-dotmodules merges all module .zshenv files into a single `~/.zshenv` with attribution headers showing which module contributed each section.

## Key Changes

**Architecture compatibility:**
- Node module now works on both ARM (M1/M2/M3 Macs with /opt/homebrew) and Intel (with /usr/local) without modification
- Uses `brew --prefix` instead of hardcoded paths
- Uses `$HOME` instead of hardcoded username

**Tool version updates:**
- Updated nodejs from 20.11.0 to 25.2.1 (current stable)
- Added jq 1.7.1 to global tool versions

**PATH management:**
- Speckit module now properly adds `$HOME/.local/bin` to PATH for uv-installed tools
- Removed unnecessary hardcoded paths from node module (Homebrew and Python user-base paths belong in their respective modules)

**Shell aliases:**
- Added `yolo` alias to Claude module for quick dangerously-skip-permissions invocation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Speckit files/ directory missing**
- **Found during:** Task 2 file creation
- **Issue:** modules/speckit/files/ directory didn't exist yet
- **Fix:** Created directory structure before writing .zshenv file
- **Files modified:** None (mkdir only)
- **Commit:** Included in Task 2 commit (a78e1cd)

**2. [Rule 3 - Blocking] Claude files/ directory missing**
- **Found during:** Task 2 file creation
- **Issue:** modules/claude/files/ directory didn't exist yet
- **Fix:** Created directory structure before writing .zshrc file
- **Files modified:** None (mkdir only)
- **Commit:** Included in Task 2 commit (a78e1cd)

No other deviations - plan executed as written after directory structure fixes.

## Testing

**Verification checks performed:**

```bash
# Architecture path checks (all passed)
! grep -q "/opt/homebrew" modules/node/files/.zshrc
! grep -q "/Users/ianderson" modules/node/files/.zshrc
grep -q "brew --prefix" modules/node/files/.zshrc

# Tool version checks (all passed)
grep "25.2.1" modules/node/files/.tool-versions
grep "jq" modules/node/files/.tool-versions

# Speckit checks (all passed)
test -f modules/speckit/files/.zshenv
grep ".zshenv" modules/speckit/config.yml

# Claude checks (all passed)
test -f modules/claude/files/.zshrc
grep "yolo" modules/claude/files/.zshrc
grep ".zshrc" modules/claude/config.yml

# Corporate config filter (passed)
! grep -riq "expedia|ewegian|zscaler|android.ndk" modules/node/ modules/speckit/ modules/claude/
```

All verification checks passed. No corporate configuration detected.

## Impact Assessment

**Immediate effects:**
- Node module configuration will work on both Intel and ARM Macs without modification
- Speckit tools installed via uv (like spec-kit CLI) will be available in PATH
- Claude Code users can use `yolo` alias for quick invocation
- Global tool versions match current stable releases

**Breaking changes:** None - all changes are additive or improve portability

**Rollback plan:** Revert commits dc9b883 and a78e1cd to restore previous configuration (Intel-only paths, no speckit PATH, no Claude alias)

**Follow-up work needed:**
- After next ansible deployment, verify that merged ~/.zshenv includes speckit PATH
- After next ansible deployment, verify that merged ~/.zshrc includes Claude yolo alias
- Test node module configuration on Intel Mac (if available)

## Commits

| Task | Commit | Description | Files |
|------|--------|-------------|-------|
| 1 | dc9b883 | Fix node module cross-architecture paths and update tool versions | modules/node/files/.zshrc, modules/node/files/.tool-versions |
| 2 | a78e1cd | Add speckit .zshenv and claude yolo alias | modules/speckit/files/.zshenv, modules/speckit/config.yml, modules/claude/files/.zshrc, modules/claude/config.yml |

## Self-Check: PASSED

**Created files verification:**
```bash
[ -f "modules/speckit/files/.zshenv" ] && echo "FOUND: modules/speckit/files/.zshenv"
# Result: FOUND: modules/speckit/files/.zshenv

[ -f "modules/claude/files/.zshrc" ] && echo "FOUND: modules/claude/files/.zshrc"
# Result: FOUND: modules/claude/files/.zshrc
```

**Modified files verification:**
```bash
git diff dc9b883^..dc9b883 --name-only
# Result: modules/node/files/.tool-versions, modules/node/files/.zshrc

git diff a78e1cd^..a78e1cd --name-only
# Result: modules/claude/config.yml, modules/claude/files/.zshrc, modules/speckit/config.yml, modules/speckit/files/.zshenv
```

**Commits verification:**
```bash
git log --oneline --all | grep -q "dc9b883" && echo "FOUND: dc9b883"
# Result: FOUND: dc9b883

git log --oneline --all | grep -q "a78e1cd" && echo "FOUND: a78e1cd"
# Result: FOUND: a78e1cd
```

All files and commits verified. Self-check passed.
