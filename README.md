# Dotfiles Repository

A comprehensive dotfiles management system using the `ansible-role-dotmodules` role for automated system configuration and dotfile deployment.

**Governance**: See [Constitution v1.0.0](.specify/memory/constitution.md) for project principles  
**AI-Assisted Development**: Integrated with [GitHub Spec-Kit](https://github.com/github/spec-kit) for spec-driven development

## Overview

This repository contains modular dotfile configurations that can be deployed using Ansible automation. Each module is self-contained and can be mixed and matched to create a personalized development environment.

All development follows the [8 core principles](.specify/memory/constitution.md) defined in the project constitution, ensuring modularity, idempotency, automation, and quality.

## Repository Structure

```
dotfiles/
├── modules/           # Dotfile modules (each with config.yml and files/)
│   ├── shell/         # Shell configurations (zsh, bash, starship, etc.)
│   ├── git/           # Git configuration and tools
│   ├── dev-tools/     # General development utilities
│   ├── editor/        # Editor configurations (vim, neovim, etc.)
│   ├── python/        # Python development environment
│   ├── node/          # Node.js development environment
│   └── go/            # Go development environment
├── playbooks/         # Ansible playbooks for deployment
└── README.md          # This file
```

## Module Structure

Each module follows this structure:

```
module-name/
├── config.yml         # Module configuration (Homebrew packages, stow dirs, etc.)
└── files/             # Dotfiles to be deployed
    ├── .config/       # Configuration files
    ├── .local/        # Local user files
    └── .*rc           # Shell configuration files
```

## Usage

### Prerequisites

- macOS (required for Homebrew integration)
- Ansible 2.9+
- GNU Stow (for dotfile deployment)
- Homebrew (for package management)

### Installation

1. **Clone this repository:**
   ```bash
   gh repo clone getfatday/dotfiles ~/src/dotfiles
   cd ~/src/dotfiles
   ```
   `gh` must be logged in as the repository owner first (`gh auth login --web`).

2. **Install the ansible-role-dotmodules role:**
   ```bash
   ansible-galaxy install getfatday.dotmodules
   ```

3. **Create a playbook** (see example below)

4. **Run the playbook:**
   ```bash
   ansible-playbook -i inventory playbook.yml
   ```

### Example Playbook

```yaml
---
- name: Deploy dotfiles
  hosts: localhost
  vars:
    dotmodules:
      repo: "file://{{ playbook_dir }}/modules"
      dest: "{{ ansible_env.HOME }}/.dotmodules"
      install:
        - shell
        - git
        - dev-tools
        - editor
        - python
        - node
        - go
  roles:
    - getfatday.dotmodules
```

### Available Modules

| Module | Description | Key Tools |
|--------|-------------|-----------|
| `shell` | Shell configurations | zsh, bash, starship, fzf, bat, exa, ripgrep |
| `git` | Git configuration | git, git-delta, gh, git-flow |
| `dev-tools` | General development tools | node, python, go, rust, jq, yq, httpie |
| `editor` | Editor configurations | neovim, vim, emacs |
| `python` | Python development | python@3.11, python@3.12, pipenv, poetry |
| `node` | Node.js development | node, npm, yarn, pnpm |
| `go` | Go development | go, goreleaser, golangci-lint |

## Configuration

Each module's `config.yml` file defines:

- **Homebrew packages** to install
- **Homebrew taps** to add
- **Homebrew casks** to install
- **Stow directories** for dotfile deployment
- **Mac App Store apps** to install
- **apt packages** (`apt_packages`) to install where the machine's platform provides apt
- **GitHub releases** (`github_releases`): tools installed from a release asset pinned by tag and
  sha256 instead of a third-party Homebrew tap. Each entry names `repo`, `tag`, `asset`, `sha256`,
  `install: {app: <name.app>, bin: [<path in the tree>]}` and an optional `strip_components`. The
  role caches the asset under `~/.local/share/dotm/releases/<repo>/<tag>/`, verifies the checksum
  before anything is extracted, copies the `.app` into `~/Applications`, links the binaries into
  `~/.local/bin` and stamps the tag directory so a second run changes nothing. Every platform
  unlocks the key. See `modules/tart/config.yml` for an example.
- **Requirements** (`requires`): capabilities the machine must have for the module to apply;
  a module whose packages are all Homebrew or Mac App Store items declares `requires: [macos]`

Each machine declares its role and platform in `~/.config/dotm/config.yml`. The platform is a
capability list (`platform: [macos, brew, gui]` for a Mac, `platform: [linux-arm, apt, headless]`
for a Raspberry Pi; unset means the Mac list). It joins the role's capabilities when modules are
selected and decides which package keys are installed: `brew` unlocks the `homebrew_*` keys,
`macos` unlocks `mas_installed_apps`, `apt` unlocks `apt_packages`, and `github_releases` is read on
every platform. Preview the per-manager
lists with `python -m dotm.modules resolve [--platform linux-arm,apt,headless]`.

Example `config.yml`:
```yaml
---
# Shell configuration module
homebrew_packages:
  - zsh
  - bash
  - starship
  - fzf
  - bat
  - exa
  - ripgrep

homebrew_taps:
  - homebrew/cask

stow_dirs:
  - shell

# Debian/Ubuntu equivalents, installed where the platform provides apt.
apt_packages:
  - zsh
  - bash
  - fzf
  - bat
  - ripgrep
```

## Customization

### Adding New Modules

1. Create a new directory in `modules/`
2. Add a `config.yml` file with your configuration
3. Create a `files/` directory with your dotfiles
4. Add the module to your playbook's `install` list

### Modifying Existing Modules

1. Edit the module's `config.yml` to change dependencies
2. Modify files in the `files/` directory
3. Re-run your playbook to apply changes

## How It Works

1. **Module Processing**: Each module is processed independently
2. **Configuration Aggregation**: All module configurations are merged
3. **Dependency Resolution**: Homebrew packages, taps, and casks are collected
4. **Dotfile Deployment**: GNU Stow deploys all dotfiles
5. **Package Installation**: Homebrew installs all dependencies

## Benefits

- **Modular**: Mix and match modules for different setups
- **Automated**: One command sets up your entire environment
- **Reproducible**: Same setup across multiple machines
- **Version Controlled**: All configurations in Git
- **Conflict Resolution**: Intelligent handling of configuration conflicts

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure all required Ansible roles are installed
2. **Stow conflicts**: Check for existing dotfiles that might conflict
3. **Homebrew issues**: Ensure Homebrew is properly installed

### Debug Mode

Run with verbose output to see what's happening:
```bash
ansible-playbook -i inventory playbook.yml -v
```

## Development with Spec-Kit

This repository uses [GitHub Spec-Kit](https://github.com/github/spec-kit) for spec-driven development with Cursor AI.

### Quick Start

Press `Cmd+K` in Cursor and use slash commands:

1. **Create specification**: `/speckit.specify Add Firefox module with developer edition`
2. **Create plan**: `/speckit.plan Install via Homebrew, configure for development`
3. **Generate tasks**: `/speckit.tasks`
4. **Implement**: `/speckit.implement`

### Available Commands

- `/speckit.constitution` - View/update project principles
- `/speckit.specify` - Create feature specifications
- `/speckit.clarify` - Interactive requirement clarification
- `/speckit.plan` - Generate implementation plans
- `/speckit.tasks` - Break down into actionable tasks
- `/speckit.implement` - Execute implementation
- `/speckit.analyze` - Verify cross-artifact consistency
- `/speckit.checklist` - Quality validation gates

### Constitution

All development must comply with [8 core principles](.specify/memory/constitution.md):
- Modularity, Idempotency, Automation-First, Cross-Platform Awareness
- Configuration Merging, Documentation-First, Version Control, Declarative Over Imperative

See [CURSOR.md](./CURSOR.md) for comprehensive development guidelines and patterns.

## Contributing

1. Fork the repository
2. Use spec-kit workflow for new features (`/speckit.specify` → `/speckit.plan` → `/speckit.implement`)
3. Ensure constitution compliance (all 8 principles)
4. Test deployment thoroughly
5. Submit a pull request with spec documentation

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built on top of [ansible-role-dotmodules](https://github.com/getfatday/ansible-role-dotmodules)
- Uses [GNU Stow](https://www.gnu.org/software/stow/) for dotfile management
- Integrates with [Homebrew](https://brew.sh/) for package management
- Spec-driven development powered by [GitHub Spec-Kit](https://github.com/github/spec-kit)