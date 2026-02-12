# ~/bin Scripts Audit

**Source:** `/Volumes/Macintosh HD-1/Users/ianderson/bin/` (77 items)

## Already in Dotfiles Repo

These are in `modules/bin/files/.local/bin/` or `modules/git/files/.local/bin/`:

git-find-first-term, git-fixup, git-last, git-now, git-recent, git-unused,
git-update-author, preview, reset-dns, ripcord, slack-api, slack-channels

## Candidates for Migration

| Script | Description | Notes |
|--------|-------------|-------|
| slack-members | Fetch Slack channel members | Complements slack-api/slack-channels already in repo |
| slack-token | Read Slack token from config | Dependency for slack-api |
| slack-user | Fetch Slack user info | Complements slack-api |
| emacs-clean | Remove Emacs lock files (.#*) | Pairs with `ec` alias in editor module |
| emacs-restart | `brew services restart emacs` | Pairs with `er` alias in editor module |
| jump-window | Tmux jump helper | Symlink to iCloud tmux config |
| jsonl2tsv | Convert JSON Lines to TSV | Generic utility, standalone |
| git-report | Git repo reporting tool | **Has 1 corporate line** (expediagroup.com email fallback on line 174). Remove/parameterize that line and it's reusable |

## Corporate Scripts (DO NOT migrate)

| Script | Corporate Reference |
|--------|-------------------|
| aql | `artylab.expedia.biz` Artifactory queries |
| asset-import | `dsrs.expedia.biz` internal trigger URL |
| rotate-artifactory-auth | `artylab.expedia.biz`, `artifactory-edge.expedia.biz` |
| rcp-cli | x86_64 binary, corporate match |
| adoption-tracker-report | Symlink to `~/src/ops-metrics/` |
| dsrs-connect | Symlink to `~/src/dsrs-scripts/` |
| dsrs-env | **Contains plaintext DB password** |
| dsrs-import | Symlink to `~/src/dsrs-scripts/` |
| az-token | Azure AD token helper |
| ms-graph | Microsoft Graph API client |
| graph-org-report | MS Graph org reports, `@expediagroup.com` |
| graph-user | MS Graph user lookup, `@expediagroup.com` |
| graph-user-id | MS Graph user ID lookup, `@expediagroup.com` |
| hillia + 16 hillia-* | Project tracking tool (Hillia) |
| cyclops-import-ooo | Symlink to `~/src/cyclops/` |
| gh-* (22 scripts) | GitHub metrics scripts for work |

## Binaries (skip)

| Binary | Arch | Size |
|--------|------|------|
| actions-sync | x86_64 | 14MB |
| rcp-cli | x86_64 | 21MB |

Both are Intel-only and not compatible with Apple Silicon natively.

## Obsolete

| Script | Reason |
|--------|--------|
| foo | Test script (`echo bar`) |
