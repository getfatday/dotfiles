# Dotfiles Implementation Patterns

**Last Updated**: 2025-10-11  
**Purpose**: Critical patterns and solutions discovered during dotfiles development

This document captures important implementation patterns that must be followed when working with this dotfiles system. These patterns complement the constitution by providing concrete solutions to common challenges.

---

## ansible-role-dotmodules Patterns

### Pattern 1: Configuration List Accumulation

**Problem**: When multiple modules define the same list (e.g., `homebrew_casks`), only the last module's values were kept.

**Solution**: Use accumulation pattern in `tasks/main.yml`:
```yaml
final_config: >-
  {{
    final_config | default({}) | combine({
      item.key: (
        ((final_config | default({}))[item.key] | default([]) + item.value) | flatten | unique
        if item.value is iterable and item.value is not string and item.value is not mapping
        else item.value
      )
    }, recursive=True)
  }}
```

**Rationale**: Ensures all modules' packages, casks, and mas apps are collected and installed.

**Commits**: a7eba7b in ansible-role-dotmodules

---

### Pattern 2: Stow File Adoption

**Problem**: Stow fails when files already exist in home directory.

**Solution**: Always use `--adopt` flag:
```yaml
- name: Deploy all dotfiles using stow
  ansible.builtin.command: >-
    stow --adopt -d "{{ dotmodules.dest }}/{{ item }}" -t "{{ ansible_env.HOME }}" files
```

**Apply to**:
- Regular stow deployment (tasks/main.yml)
- Merged files stow deployment (tasks/merge_files.yml)

**Rationale**: Allows stow to adopt pre-existing files, making deployments repeatable and resilient.

**Commits**: a7eba7b, ab3e695 in ansible-role-dotmodules

---

### Pattern 3: Homebrew Without Sudo

**Problem**: The `geerlingguy.mac.homebrew` role requires interactive sudo password.

**Solution**: Use Ansible's built-in Homebrew modules directly:
```yaml
- name: Install Homebrew packages
  community.general.homebrew:
    name: "{{ homebrew_packages }}"
    state: present
  when: homebrew_packages is defined and homebrew_packages | length > 0

- name: Install Homebrew casks
  community.general.homebrew_cask:
    name: "{{ homebrew_casks }}"
    state: present
    accept_external_apps: yes
  when: homebrew_casks is defined and homebrew_casks | length > 0
```

**Rationale**: Eliminates sudo requirement, enables fully automated deployments, handles already-installed apps gracefully.

**Commits**: a7eba7b in ansible-role-dotmodules

---

### Pattern 4: Ansible 2.19+ Filter Compatibility

**Problem**: `select('extract', dict, 'key')` pattern fails with "No test named 'extract'".

**Solution**: Use explicit loop instead:
```yaml
- name: Initialize list
  ansible.builtin.set_fact:
    modules_with_mergeable_files: []

- name: Check each module
  ansible.builtin.set_fact:
    modules_with_mergeable_files: >-
      {{
        modules_with_mergeable_files +
        ([item] if (collected_configs[item].mergeable_files is defined and
                    collected_configs[item].mergeable_files | length > 0)
         else [])
      }}
  loop: "{{ dotmodules.install }}"
  when: item in collected_configs
```

**Rationale**: The `extract` filter must be used with `map`, not `select`. Modern Ansible requires explicit patterns.

**Commits**: c31bffe in ansible-role-dotmodules

---

## Module Development Patterns

### Pattern 5: App-Only Modules

**When**: Module only installs an application without config files

**Pattern**:
```yaml
---
# Module description
homebrew_casks:
  - app-name

# Note: No stow_dirs since no files to deploy
```

**Example Modules**: `1password`, `handbrake`

**Anti-Pattern**: Declaring `stow_dirs` when `files/` directory doesn't exist causes stow errors.

---

### Pattern 6: Modules with Configuration

**When**: Module installs app AND provides configuration files

**Pattern**:
```yaml
---
homebrew_casks:
  - app-name

stow_dirs:
  - module-name

# Note: files/ directory must exist
```

**Example Modules**: `chrome`, `cursor`, `iterm`

---

### Pattern 7: Shell Configuration Contributions

**When**: Module adds commands, aliases, or PATH modifications to shell

**Pattern**:
```yaml
---
homebrew_packages:
  - tool-name

stow_dirs:
  - module-name

mergeable_files:
  - ".zshrc"        # Must declare!
  - ".zshenv"       # If contributing to this too
```

**In files/.zshrc**:
```bash
# ModuleName module contribution to Zsh configuration
# This file will be merged with the main .zshrc file

# Module-specific shell configuration here
```

**Example Modules**: `git`, `node`, `editor`, `productivity`

**Critical**: MUST declare mergeable files or deployment will conflict!

---

## File Organization Patterns

### Pattern 8: Mergeable File Declaration

**Rule**: ALL modules that provide `.zshrc`, `.zpreztorc`, or `.osx` MUST declare them as mergeable.

**Modules requiring declaration**:
- `zsh` - Owns `.zshrc` and `.zpreztorc`
- `macos` - Owns `.osx`
- `git`, `node`, `editor`, `docker`, `productivity` - Contribute to `.zshrc`
- `alfred` - Contributes to `.osx`

**Why**: The merge process creates unified files. If not declared, stow tries to deploy module files separately, causing conflicts.

---

### Pattern 9: Directory Structure Requirements

**Rule**: Match file structure to deployment location

**Example**: Shell configuration
```
modules/zsh/files/
├── .zshrc                    → ~/
├── .zpreztorc               → ~/
└── .local/
    └── bin/
        └── setup-prezto.sh  → ~/.local/bin/
```

Stow creates symlinks maintaining the directory structure relative to `files/`.

---

## Testing Patterns

### Pattern 10: Pre-Deployment Testing

**Before ANY commit**:
```bash
# 1. Check mode (dry run)
ansible-playbook -i playbooks/inventory playbooks/deploy.yml --check

# 2. Actual deployment
ansible-playbook -i playbooks/inventory playbooks/deploy.yml

# 3. Verify success
# Look for: failed=0, changed=X, ok=X

# 4. Verify applications installed
ls /Applications/ | grep "App Name"
brew list --cask | grep app-name
```

**Never**:
- Commit without testing deployment
- Push without verifying deployment succeeds
- Skip check mode for significant changes

---

## Cross-Repository Patterns

### Pattern 11: Fixing ansible-role-dotmodules Bugs

**Workflow**:
1. Identify bug in deployment
2. Fix in source repo: `~/src/ansible-role-dotmodules`
3. Test fix locally by editing `~/.ansible/roles/ansible-role-dotmodules/`
4. Once working, apply to source repo
5. Commit and push to ansible-role-dotmodules repo
6. Reinstall in dotfiles: `ansible-galaxy install -r requirements.yml --force`
7. Test deployment in dotfiles repo
8. Commit any dotfiles changes (module updates, etc.)

**Critical**: Always update BOTH repositories and verify integration.

---

## Architecture Decisions

### Decision 1: Two-Repository Structure

**Repositories**:
- `dotfiles` - Module definitions, playbooks (this repo)
- `ansible-role-dotmodules` - Core automation engine

**Rationale**: Separates module definitions (user-specific) from automation logic (reusable role).

---

### Decision 2: Merge vs Stow

**Merge Process**: For `.zshrc`, `.zpreztorc`, `.osx`
- Multiple modules contribute
- Files concatenated in `~/.dotmodules/merged/`
- Single symlink created from home directory

**Stow Process**: For all other files
- Each module's files stowed independently
- Direct symlinks to module files
- Module independence maintained

**Rationale**: Shared config files need merging; other files remain independent for clarity.

---

### Decision 3: Declarative Configuration

**Chosen**: YAML-based `config.yml` files
**Rejected**: Shell scripts for package installation

**Rationale**: 
- Declarative configs easier to audit
- Ansible handles idempotency automatically
- Less error-prone than imperative scripts
- Constitution Principle VIII compliance

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Manual Installation
Never install packages manually. Always use Ansible automation.

### ❌ Anti-Pattern 2: Empty stow_dirs
Don't declare `stow_dirs` without a corresponding `files/` directory.

### ❌ Anti-Pattern 3: Undeclared Mergeable Files
If your module contributes to `.zshrc`, you MUST declare it in `mergeable_files`.

### ❌ Anti-Pattern 4: Module Dependencies
Don't create dependencies between modules. Each module must be independently deployable.

### ❌ Anti-Pattern 5: Imperative Package Installation
Don't create shell scripts that run `brew install`. Use `config.yml` declarations.

---

## Version History

**2025-10-11**: Initial patterns documented
- Configuration merging fix
- Stow adoption pattern
- Homebrew without sudo
- Ansible filter compatibility
- Mergeable file requirements

---

**Note**: This document should be updated when new patterns are discovered or anti-patterns identified. Reference from specifications and plans when making architectural decisions.

