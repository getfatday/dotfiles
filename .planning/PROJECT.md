# Dotfiles Laptop Audit & Migration

## What This Is

A systematic audit of Ian's old work laptop (mounted at `/Volumes/Macintosh HD-1/Users/ianderson/`) to capture all personal configuration, scripts, and settings into this dotfiles/ansible repository. The goal is to make the old laptop wipeable by ensuring everything worth keeping is tracked in the repo and deployable to the current Mac Mini via ansible.

## Core Value

Every personal configuration and script from the old laptop is captured in the repo — nothing is lost when the old laptop is wiped.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Audit old laptop's .gitconfig and reconcile with repo (SSH signing, diff tools, credential helpers)
- [ ] Audit and capture ~/bin/ personal utility scripts into appropriate module
- [ ] Identify missing app/tool modules not yet in repo but present on old laptop
- [ ] Audit shell config (.zshrc, .zprofile, aliases, functions) for gaps
- [ ] Auto-filter all Expedia/corporate artifacts by pattern (domains, paths, org names)
- [ ] Ensure no secrets are committed (repo is public GitHub) — secrets route to 1Password
- [ ] Ansible dry-run passes cleanly on current Mac Mini
- [ ] Ansible real apply succeeds on Mac Mini

### Out of Scope

- Expedia corporate configuration — corporate VPN, internal tool configs, work email/calendar, org-specific paths
- Corporate SSH keys or credentials — Expedia-specific auth material
- One-off temporary files or caches — .cache, .tmp, node_modules, build artifacts
- Application data (databases, media libraries) — only config files, not data
- macOS system preferences that ansible can't manage — handled separately if needed

## Context

- **Old laptop:** Mounted read-only at `/Volumes/Macintosh HD-1/Users/ianderson/`
- **Current machine:** Mac Mini (Apple Silicon, macOS 15.x)
- **Repo structure:** Ansible-based dotfiles with module structure (modules/*)
- **Secrets management:** 1Password integration already established in the repo
- **Repo visibility:** PUBLIC on GitHub — zero tolerance for secrets in commits
- **Corporate filter patterns:** Expedia, expediagroup, ewegian, hotels.com, vrbo, EG org paths, corporate VPN configs, Jamf/MDM artifacts

## Constraints

- **Public repo**: No secrets, tokens, API keys, or corporate credentials can be committed
- **Read-only source**: Old laptop volume is mounted — treat as read-only reference
- **Ansible-compatible**: All new config must fit the existing module/role structure
- **Dry-run first**: Changes must be validated in check mode before real application
- **Pattern filtering**: Corporate artifacts identified by domain/org patterns, not manual review

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Auto-filter corporate artifacts by pattern | Old laptop was corporate-managed; patterns (expedia, ewegian, etc.) are distinctive enough for automated filtering | — Pending |
| Mirror old laptop fully (minus corporate) | Goal is to make old laptop wipeable — can't cherry-pick without risk of losing something | — Pending |
| Dry-run before real apply | First ansible run on Mac Mini should be non-destructive to validate changes | — Pending |
| Secrets to 1Password | Repo is public, 1Password integration already exists | — Pending |

---
*Last updated: 2026-02-11 after initialization*
