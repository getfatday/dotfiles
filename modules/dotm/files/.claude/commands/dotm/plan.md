---
description: Plan and execute dotfiles changes through dotm
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task
argument: task
---

You are working in a dotfiles repo managed by **dotm** (dotfiles module manager).

The user wants to make a change to their dotfiles setup. Their request: $ARGUMENTS

## Workflow

1. **Understand the request** — What does the user want? Which modules are affected?
2. **Check current state** — Run `dotm status` and `dotm verify` for relevant modules
3. **Plan the changes** — Determine which files to create/modify within `modules/`
4. **Make the changes** — Edit module configs, create dotfiles in `files/` directories
5. **Verify** — Run `dotm verify` to ensure everything is correct
6. **Push** — Run `dotm push -m "descriptive commit message"` to deploy

## Key Rules

- All dotfiles live inside `modules/<name>/files/` and get stowed to `~/`
- Module config is `modules/<name>/config.yml` (packages, stow_dirs)
- Never commit secrets — `dotm push` scans automatically
- Test with `dotm sync` before pushing if unsure
- Use `dotm create <name>` to scaffold new modules

## Module config.yml Format

```yaml
homebrew_packages:
  - package-name
homebrew_casks:
  - app-name
stow_dirs:
  - dirname    # directory inside files/ to stow
```

## Stow Mapping

Files in `modules/<name>/files/` map to `~/`:
- `modules/foo/files/.config/app/config` -> `~/.config/app/config`
- `modules/foo/files/.tmux.conf` -> `~/.tmux.conf`
