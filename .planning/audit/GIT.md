# Git Config Audit

## Missing from Dotfiles (carry forward)

### SSH Commit Signing (1Password)
```ini
[gpg]
  format = ssh
[gpg "ssh"]
  program = "/Applications/1Password.app/Contents/MacOS/op-ssh-sign"
[commit]
  gpgsign = true
[user]
  signingkey = <configure via 1Password>
```
The old laptop had full 1Password SSH signing. The current dotfiles have none.

### Kaleidoscope Diff/Merge Tool
```ini
[diff]
  tool = Kaleidoscope
[difftool "Kaleidoscope"]
  cmd = ksdiff --partial-changeset --relative-path \"$MERGED\" -- \"$LOCAL\" \"$REMOTE\"
[merge]
  tool = Kaleidoscope
[mergetool "Kaleidoscope"]
  cmd = ksdiff --merge --output \"$MERGED\" --base \"$BASE\" -- \"$LOCAL\" --snapshot \"$REMOTE\" --snapshot
  trustExitCode = true
[mergetool]
  prompt = false
```
Current dotfiles use kdiff3. Kaleidoscope was actually in use on the old laptop.

### Rebase Autosquash
```ini
[rebase]
  autosquash = true
```
Required by the `gqf` alias. Missing from current dotfiles.

### Default Branch
Old laptop: `defaultBranch = main`. Current dotfiles: `defaultBranch = master`. **Regression.**

### GitHub Credential Helper
```ini
[credential "https://github.com"]
  helper =
  helper = !/opt/homebrew/bin/gh auth git-credential
[credential "https://gist.github.com"]
  helper =
  helper = !/opt/homebrew/bin/gh auth git-credential
```
Current dotfiles only have `osxkeychain`. Should use `gh auth git-credential` for GitHub.

### Global Gitignore Entry
Old laptop had `~/.config/git/ignore` with:
```
**/.claude/settings.local.json
```
Not present in current dotfiles.

### User Email
Old: `ianderson@expediagroup.com` (corporate). Current: `ianderson@example.com` (placeholder).
**Action:** Set to actual personal email.

## Present in Dotfiles, Missing from Old Laptop

These are fine to keep:
- `[core]` section (editor, excludesfile, autocrlf)
- `[color]` section
- `[alias]` section (c, ca, cm, cam, d, dc, l, open, browse)
- `[pull] rebase = true`
- `[web] browser = google-chrome`
- `[push] default = simple`

## Corporate Items (DO NOT carry forward)

- `[credential "https://dev.azure.com"]` — Azure DevOps
- `[credential "https://github.expedia.biz"]` — Expedia GitHub Enterprise
- `[credential] helper = /usr/local/share/gcm-core/git-credential-manager` — GCM Core fallback
- `[user] email = ianderson@expediagroup.com`
