# CLAUDE.md — dotfiles repo

## System Overview

This is a modular dotfiles system managed by **dotm** (dotfiles module manager). Each module lives in `modules/<name>/` and can contain Homebrew packages, casks, Mac App Store apps, and stow-managed dotfiles.

Repo location: `~/src/dotfiles`

## dotm Commands

| Command | Description |
|---------|-------------|
| `dotm list` | List all modules (--installed, --available, --excluded) |
| `dotm status` | Show system status summary |
| `dotm verify [modules...]` | Verify module installations are correct |
| `dotm install <module>` | Install a module (adds to deploy.yml, runs ansible) |
| `dotm uninstall <module>` | Remove a module (symlinks only, keeps packages) |
| `dotm create <name>` | Create a new module (--brew, --cask, --mas, --interactive) |
| `dotm analyze` | Detect drift — packages installed outside module management |
| `dotm catalog` | Auto-create modules from unmanaged packages |
| `dotm sync` | Pull latest changes and apply all modules |
| `dotm push -m "msg"` | Security scan, commit, and push module changes |
| `dotm exclude <module>` | Skip a module during sync |
| `dotm include <module>` | Re-include an excluded module |
| `dotm doctor` | Diagnose common issues |
| `dotm plan [prompt]` | Open Claude Code in this repo for interactive planning |

## Architecture

### Module Structure
```
modules/<name>/
  config.yml          # Module definition (packages, stow dirs)
  files/              # Stow root — maps to ~/ via GNU Stow
    .config/app/...   # Becomes ~/.config/app/...
    .tmux.conf        # Becomes ~/.tmux.conf
```

### Stow Flow
1. Module's `config.yml` declares `stow_dirs: [<name>]`
2. Ansible role runs `stow -d modules/<name>/files -t ~ <dir>` for each stow dir
3. Symlinks are created from `~/` pointing into the repo

### Module config.yml Format
```yaml
---
# Module description comment

homebrew_packages:
  - package-name          # Comment describing package

homebrew_casks:
  - app-name              # macOS application

mas_apps:
  - 123456789             # App Store app ID

stow_dirs:
  - dirname               # Directory inside files/ to stow (usually module name)
```

### Profiles & Deploy
- `playbooks/deploy.yml` lists which modules to install
- Each machine can exclude modules via `dotm exclude <name>`
- Exclusions stored in `~/.config/dotm/config.yml`

### Sync & Propagation
- `dotm sync` = git pull + ansible apply (installs packages, stows files)
- LaunchAgent `com.getfatday.dotm-sync` runs `dotm sync` periodically
- Changes pushed from one machine auto-propagate to others via git

## Rules

1. **No secrets** — Never commit API keys, tokens, passwords, or private keys
2. **Use `dotm push`** — It runs a security scan before committing
3. **Verify before pushing** — Run `dotm verify` to check your changes
4. **Module changes go in modules/** — Don't scatter dotfiles at repo root
5. **Test locally first** — Run `dotm sync` after changes to verify they apply

## Slash Commands

- `/dotm:plan` — Plan and execute dotfiles changes through dotm
- `/dotm:status` — Show system status with AI interpretation
- `/dotm:analyze` — Detect drift and suggest module organization
- `/dotm:install` — AI-assisted module installation
- `/dotm:create` — AI-assisted module creation
- `/dotm:sync` — Sync dotfiles with AI monitoring
