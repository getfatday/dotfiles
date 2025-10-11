<!--
Sync Impact Report - Constitution v1.0.0
========================================
Version Change: [TEMPLATE] → 1.0.0
Change Type: MAJOR (Initial ratification)
Date: 2025-10-11

Principles Defined:
- I. Modularity
- II. Idempotency
- III. Automation-First
- IV. Cross-Platform Awareness
- V. Configuration Merging
- VI. Documentation-First
- VII. Version Control Everything
- VIII. Declarative Over Imperative

Sections Added:
- Core Principles (8 principles)
- Module Requirements
- Deployment Standards
- Governance

Templates Requiring Updates:
✅ plan-template.md - Updated Constitution Check section
✅ spec-template.md - Verified compatibility
✅ tasks-template.md - Verified task categorization aligns

Follow-up: None - all placeholders resolved
-->

# Dotfiles Management System Constitution

## Core Principles

### I. Modularity

Each tool or application must have its own independent module. Modules are self-contained units that can be deployed separately without dependencies on other modules' internal structure.

**Rules**:
- One module per tool/application (e.g., `chrome`, `git`, `node`)
- Module independence: no cross-module file references
- Module structure: `config.yml` + optional `files/` directory
- Clear single responsibility per module

**Rationale**: Modularity enables selective deployment, easier maintenance, and the ability to mix and match configurations across different machines.

### II. Idempotency

All deployments must be safely repeatable without side effects. Running the same deployment multiple times must produce identical results.

**Rules**:
- No destructive operations without explicit user confirmation
- Deployment state is deterministic
- Check before modify (e.g., "install if not present")
- Use declarative tools (Ansible, Stow) that handle idempotency

**Rationale**: Idempotency prevents configuration drift and makes deployments safe to run repeatedly for updates or verification.

### III. Automation-First

All configurations must be deployable through automation. Manual installation or configuration steps are not acceptable.

**Rules**:
- Every module declares dependencies explicitly in `config.yml`
- No manual post-installation steps (except one-time setup scripts)
- Use Ansible automation for all deployments
- Package manager integration (Homebrew, MAS) required for applications

**Rationale**: Automation ensures consistent deployments across systems, reduces human error, and makes onboarding new machines trivial.

### IV. Cross-Platform Awareness

Modules must handle both Apple Silicon (ARM64) and Intel (x86_64) Macs gracefully.

**Rules**:
- Architecture-specific configurations clearly documented
- Homebrew path detection (`/opt/homebrew` vs `/usr/local`)
- Graceful degradation when platform-specific tools unavailable
- Architecture differences explicitly noted in README files

**Rationale**: Supports diverse hardware while maintaining single configuration source.

### V. Configuration Merging

Multiple modules can contribute to shared configuration files (e.g., `.zshrc`, `.zpreztorc`, `.osx`). 

**Rules**:
- Mergeable files must be explicitly declared in `config.yml`
- Each module's contribution must be self-contained
- No conflicting settings between modules
- Merged files deployed via merge process, not stow

**Rationale**: Enables modular contributions to shared configs while preventing conflicts and maintaining independence.

### VI. Documentation-First

Every module must include comprehensive documentation explaining its purpose, contents, and usage.

**Rules**:
- Every module must have `files/README.md`
- README must document: what gets installed, how to use it, integration points
- Installation requirements and post-deployment steps documented
- Examples and common use cases included

**Rationale**: Documentation ensures modules are understandable and maintainable by others (and future you).

### VII. Version Control Everything

All configuration files, scripts, and module definitions must be in version control. Nothing important lives only on local machines.

**Rules**:
- All dotfiles committed to git
- Generated files (e.g., `modules/merged/`) must be gitignored
- Sensitive data never committed (use env vars or external secret management)
- Machine-specific state excluded from version control

**Rationale**: Version control provides history, backup, and synchronization across machines.

### VIII. Declarative Over Imperative

System state should be defined declaratively, not through imperative scripts.

**Rules**:
- Configuration in `config.yml` (declarative), not shell scripts
- Prefer native package managers (Homebrew) over manual downloads
- Ansible playbooks over bash scripts
- Shell scripts only for orchestration or one-time setup tasks

**Rationale**: Declarative configurations are easier to understand, audit, and maintain than imperative scripts.

## Module Requirements

All modules must adhere to:

**Structure**:
- `config.yml` - Module configuration (packages, casks, stow dirs, mergeable files)
- `files/` - Dotfiles to deploy (optional, omit if module only installs apps)
- `files/README.md` - Module documentation (required)

**Configuration Elements** (`config.yml`):
- `homebrew_packages` - List of Homebrew formulae
- `homebrew_casks` - List of Homebrew casks
- `mas_installed_apps` - List of Mac App Store app IDs
- `stow_dirs` - List of directories to deploy via GNU Stow (only if `files/` exists)
- `mergeable_files` - List of files merged from multiple modules

**Documentation Requirements** (`files/README.md`):
- Module title and purpose
- Features list
- What gets installed
- Usage examples
- Integration with other tools
- Configuration details
- Troubleshooting section

## Deployment Standards

**Deployment Process**:
- Use `ansible-playbook` with `ansible-role-dotmodules`
- All modules declared in playbook `install` list
- GNU Stow for file deployment
- Merge process for shared configuration files

**Testing Requirements**:
- Test module independently before adding to deployment
- Use `--check` mode for dry runs
- Verify installations after deployment
- Document known issues and workarounds

**Quality Gates**:
- All modules must deploy without errors
- No manual interventions during deployment
- Homebrew packages resolve successfully
- Stow conflicts handled via merge or --adopt flag

## Governance

**Authority**: This constitution supersedes all other development practices and preferences. When in conflict, the constitution wins.

**Amendment Process**:
- Amendments require documented rationale
- Version number incremented (MAJOR.MINOR.PATCH)
- Impact analysis on existing modules required
- Migration plan for breaking changes

**Compliance**:
- All pull requests must verify constitutional compliance
- New modules must follow all core principles
- Deviations require explicit justification and approval
- Regular audits to ensure continued compliance

**Versioning**:
- MAJOR: Backward-incompatible principle changes or removals
- MINOR: New principles added or existing principles expanded
- PATCH: Clarifications, typo fixes, non-semantic changes

**Review**: Constitution reviewed quarterly or when significant architectural changes proposed.

**Version**: 1.0.0 | **Ratified**: 2025-10-11 | **Last Amended**: 2025-10-11
