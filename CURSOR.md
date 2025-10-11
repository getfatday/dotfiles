# Dotfiles Development Guidelines for Cursor

Auto-generated context for AI-assisted development. Last updated: 2025-10-11

## Project Overview

This is a dotfiles management system using **ansible-role-dotmodules** for automated deployment across macOS systems. The project uses modular configuration with GNU Stow for file deployment and Homebrew for package management.

**Constitution**: See `.specify/memory/constitution.md` for governing principles (v1.0.0)

## Active Technologies

- **Automation**: Ansible 2.19+, ansible-role-dotmodules
- **File Deployment**: GNU Stow with --adopt flag
- **Package Management**: Homebrew (packages + casks), Mac App Store (mas)
- **Configuration Format**: YAML (config.yml files)
- **Shell**: Zsh with Prezto framework
- **Version Control**: Git
- **Python Tooling**: UV (package manager), spec-kit (this framework)

## Project Structure

```
dotfiles/
├── modules/                    # Dotfile modules (each tool/app gets one)
│   ├── chrome/                 # Example: Chrome browser
│   │   ├── config.yml          # Module configuration
│   │   └── files/              # Files to deploy via stow
│   │       └── README.md       # Module documentation (required)
│   ├── git/                    # Git with aliases and configuration
│   ├── zsh/                    # Zsh shell with Prezto
│   ├── node/                   # Node.js development
│   └── speckit/                # Spec-kit for spec-driven development
├── playbooks/                  # Ansible playbooks
│   ├── deploy.yml              # Main deployment playbook
│   └── inventory               # Ansible inventory (localhost)
├── .cursor/                    # Cursor configuration
│   └── commands/               # Custom slash commands (spec-kit)
├── .specify/                   # Spec-kit framework
│   ├── memory/
│   │   └── constitution.md     # Project constitution
│   ├── scripts/                # Helper scripts
│   └── templates/              # Spec, plan, task templates
└── specs/                      # Feature specifications (created as needed)
```

## Module Configuration Format

Every module has a `config.yml` with these optional fields:

```yaml
---
# Module name and description
homebrew_packages:      # Homebrew formulae to install
  - package-name
homebrew_casks:         # Homebrew casks to install
  - cask-name
mas_installed_apps:     # Mac App Store app IDs
  - 1234567890
stow_dirs:              # Directories to deploy via stow (omit if no files/)
  - module-name
mergeable_files:        # Files merged from multiple modules
  - ".zshrc"
  - ".config/file"
```

**Critical Rules**:
- Only include `stow_dirs` if `files/` directory exists
- Always declare `mergeable_files` if contributing to shared configs like `.zshrc`
- Every module must have `files/README.md` if it has config files

## Commands

### Deployment
```bash
# Install/update Ansible role
ansible-galaxy install -r requirements.yml --force

# Deploy all modules
ansible-playbook -i playbooks/inventory playbooks/deploy.yml

# Dry run (check mode)
ansible-playbook -i playbooks/inventory playbooks/deploy.yml --check
```

### Module Development
```bash
# Create new module
mkdir -p modules/newmodule/files
touch modules/newmodule/config.yml
# Add module to playbooks/deploy.yml install list
```

### Spec-kit Workflow
```bash
# Install spec-kit
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# Verify installation
specify check

# Use slash commands in Cursor (Cmd+K)
/speckit.specify     # Create feature spec
/speckit.plan        # Create implementation plan
/speckit.implement   # Execute implementation
```

## Code Style

### YAML (config.yml)
- Use 2-space indentation
- Comments above each section explaining purpose
- Include "Note:" section listing what module provides

### Markdown (README.md)
- H1: Module name (e.g., "# Chrome Module")
- Sections: Features, What Gets Installed, Usage, Integration, Configuration
- Code blocks with language specified
- Tables for structured information

### Ansible
- Use ansible-role-dotmodules role
- Declare all dependencies explicitly
- No sudo requirements (use community.general.homebrew modules)
- Idempotent operations only

## Recent Changes & Key Learnings

### 2025-10-11: Chrome Module + Critical Bug Fixes

**Added**:
- Chrome module with comprehensive documentation
- Spec-kit module for spec-driven development  
- Dotfiles constitution (v1.0.0)

**Fixed in ansible-role-dotmodules**:
- **Configuration Merging Bug**: Changed list reduction to accumulate values instead of replacing
  - Before: Only last module's `homebrew_casks` kept
  - After: All modules' casks properly collected
  - Critical for multi-module package installation

- **Stow Conflicts**: Added `--adopt` flag to both regular and merged file stow commands
  - Handles pre-existing files gracefully
  - Prevents deployment failures

- **Sudo Requirement**: Replaced `geerlingguy.mac.homebrew` with `community.general` modules
  - No interactive password prompts needed
  - Fully automated deployment

- **Extract Filter Compatibility**: Fixed Ansible 2.19 compatibility
  - Replaced broken `select('extract', ...)` pattern
  - Used explicit loop for module filtering

**Modules Requiring Mergeable Files**:
- `zsh` - Declares `.zshrc`, `.zpreztorc`
- `macos` - Declares `.osx`
- `git`, `node`, `editor`, `docker`, `productivity` - Already declared

## Common Patterns

### Adding a New Application Module

**Pattern**: App-only module (no config files)
```yaml
# config.yml
---
homebrew_casks:
  - app-name
# Note: No stow_dirs since no files to deploy
```

**Pattern**: App with config files
```yaml
# config.yml
---
homebrew_casks:
  - app-name
stow_dirs:
  - module-name
mergeable_files:    # Only if contributing to .zshrc, etc.
  - ".zshrc"
```

### Adding Shell Configuration

If your module adds to `.zshrc`:
1. Declare in `mergeable_files: [".zshrc"]`
2. Create `files/.zshrc` with header comment
3. Keep contributions modular and self-contained

### Homebrew Package Installation

All packages across all modules are collected and installed together:
- `homebrew_packages` merged from all modules
- `homebrew_casks` merged from all modules  
- `mas_installed_apps` merged from all modules

## Troubleshooting

### Stow Conflicts
If deployment fails with stow conflicts:
- Check if files already exist in home directory
- Ensure mergeable files declared in all contributing modules
- Verify `--adopt` flag present in ansible-role-dotmodules

### Missing Packages
If packages don't install:
- Check configuration reduction in ansible-role-dotmodules
- Ensure list merging uses accumulation, not replacement
- Verify `homebrew_packages`/`homebrew_casks` present in final_config

### Module Not Deploying
- Verify module in `playbooks/deploy.yml` install list
- Check `config.yml` syntax
- Don't declare `stow_dirs` without `files/` directory

## Dependencies

**Required Tools**:
- macOS (required for Homebrew)
- Ansible 2.9+
- GNU Stow
- Homebrew
- Git

**Python Tools** (via UV):
- spec-kit (specify CLI)

**Ansible Roles**:
- ansible-role-dotmodules (from github.com/getfatday/ansible-role-dotmodules)

**Ansible Collections**:
- geerlingguy.mac (for MAS support)
- community.general (for Homebrew modules)

## Architecture Decisions

### Why ansible-role-dotmodules?
Provides modular dotfile management with:
- Module aggregation (collects all config.yml files)
- File merging (handles shared configs like .zshrc)
- Stow deployment automation
- Homebrew package aggregation

### Why GNU Stow?
- Creates symlinks to version-controlled files
- No file duplication
- Easy to update (edit source, changes reflected immediately)
- `--adopt` flag handles conflicts

### Why Configuration Merging?
Multiple modules need to contribute to `.zshrc`:
- `zsh` - Base shell config
- `git` - Git aliases and functions
- `node` - Node.js and pnpm paths
- `editor` - Editor-specific aliases
- `productivity` - Productivity tools

Merging creates single `.zshrc` from all contributions.

## Best Practices

### When Adding Modules
1. Use `/speckit.specify` to define what the module does
2. Use `/speckit.plan` to plan the implementation
3. Follow constitution principles (all 8 required)
4. Test deployment before committing
5. Document thoroughly in README.md

### When Modifying ansible-role-dotmodules
- Test changes locally first
- Update both source repo and dotfiles repo
- Reinstall role: `ansible-galaxy install -r requirements.yml --force`
- Verify deployment still works

### When Creating Mergeable Files
- Keep contributions focused and independent
- Add comment header identifying source module
- Test that merging doesn't create conflicts
- Document in module README what gets merged

## Spec-Kit Integration

Custom slash commands available in Cursor (press `Cmd+K`):

- `/speckit.constitution` - Update project principles
- `/speckit.specify` - Create feature specifications  
- `/speckit.clarify` - Interactive requirement clarification
- `/speckit.plan` - Generate implementation plans
- `/speckit.tasks` - Break down into actionable tasks
- `/speckit.implement` - Execute implementation
- `/speckit.analyze` - Verify cross-artifact consistency
- `/speckit.checklist` - Quality validation gates

## Example Workflows

### Adding a New Browser Module

```
# 1. Create specification
/speckit.specify Add Firefox Developer Edition module with developer tools,
privacy-focused settings, and integration with development workflow

# 2. Create plan
/speckit.plan Install via Homebrew Cask, no config files needed since Firefox
manages its own profiles

# 3. Generate tasks
/speckit.tasks

# 4. Implement
/speckit.implement
```

### Adding a Development Tool Module

```
# 1. Specify
/speckit.specify Add PostgreSQL module with automated backups, performance
tuning, and connection pooling configuration

# 2. Clarify requirements
/speckit.clarify

# 3. Plan
/speckit.plan Use Homebrew for PostgreSQL 15, create config files for 
postgresql.conf, setup automated backup script, integrate with launchd

# 4. Generate tasks
/speckit.tasks

# 5. Implement
/speckit.implement
```

## Known Issues & Solutions

### Issue: Homebrew Casks Only From Last Module
**Solution**: Fixed in ansible-role-dotmodules commit a7eba7b
- Configuration reduction now accumulates list values
- All modules' casks properly collected

### Issue: Stow Fails on Existing Files  
**Solution**: Fixed in ansible-role-dotmodules commits a7eba7b, ab3e695
- Added `--adopt` flag to stow commands
- Handles conflicts gracefully

### Issue: Extract Filter Error in Ansible 2.19
**Solution**: Fixed in ansible-role-dotmodules commit c31bffe
- Replaced `select('extract', ...)` with explicit loop
- Compatible with modern Ansible versions

### Issue: Modules Without files/ Causing Stow Errors
**Solution**: Don't declare `stow_dirs` in app-only modules
- Only declare if `files/` directory exists
- Example: handbrake, 1password modules

## Related Repositories

- **ansible-role-dotmodules**: https://github.com/getfatday/ansible-role-dotmodules
  - Core automation role
  - Maintains module aggregation and deployment logic
  - Contributions welcome for improvements

- **spec-kit**: https://github.com/github/spec-kit
  - Spec-driven development toolkit
  - Provides slash commands and templates
  - Installed via UV

## Quick Reference

### File Locations
- Constitution: `.specify/memory/constitution.md`
- Module configs: `modules/*/config.yml`
- Module docs: `modules/*/files/README.md`
- Deployment playbook: `playbooks/deploy.yml`
- Ansible inventory: `playbooks/inventory`

### Important Paths
- Dotmodules destination: `~/.dotmodules/`
- Merged files: `~/.dotmodules/merged/`
- Stowed files: Symlinked from `~/.dotmodules/*/files/`
- UV tools: `~/.local/bin/`

### Git Workflow
- Main branch: `main`
- All changes pushed to origin
- Clean working tree maintained
- Stash used for temporary work

---

**Note**: This file is auto-updated by spec-kit. Manual additions should go between the `<!-- MANUAL ADDITIONS START/END -->` markers if this template is regenerated.

