# Git Configuration Module

This module provides a comprehensive Git development environment with enhanced productivity features.

## Features

- **Git configuration** - User settings, aliases, and preferences
- **Git open command** - Open repositories in browser with advanced features
- **Git aliases** - Common Git shortcuts for productivity
- **Merge tool integration** - kdiff3 for visual diffs
- **Credential management** - macOS keychain integration

## What Gets Installed

### Homebrew Packages
- `git` - Git version control
- `kdiff3` - Visual diff and merge tool
- `gh` - GitHub CLI
- `git-flow` - Git workflow extensions

### Homebrew Casks
- `google-chrome` - Web browser for git open

### Configuration Files
- `.gitconfig` - Git configuration with aliases and settings
- `.local/bin/git-open` - Advanced git open script
- `.local/bin/git-*` - Custom Git utilities (see below)

## Git Open Command

The `git open` command opens the current repository in your browser with advanced features:

### Basic Usage
```bash
git open                    # Open repository
git browse                  # Alternative command (same as git open)
```

### Advanced Usage
```bash
git open -f src/main.js                    # Open specific file
git open -f src/main.js -l 42              # Open file at line 42
git open -b feature-branch                  # Open specific branch
git open -c abc1234                         # Open specific commit
```

### Supported Git Hosting Services
- **GitHub** - github.com
- **GitLab** - gitlab.com
- **Bitbucket** - bitbucket.org
- **Azure DevOps** - dev.azure.com
- **Any Git hosting service** with standard URL patterns

## Custom Git Binaries

This module includes several custom Git utilities in `~/.local/bin/`:

### Git Workflow Utilities
- **`git-fixup`** - Creates a fixup commit for the last commit
- **`git-last`** - Shows diff between two commits (default: HEAD~1 to HEAD)
- **`git-now`** - Shows diff for current working directory vs HEAD

### Git Branch Management
- **`git-recent`** - Lists recent branches you've worked on
  ```bash
  git recent -n 5    # Show last 5 branches
  git recent         # Show last 10 branches (default)
  ```
- **`git-unused`** - Finds and optionally deletes branches that are gone from origin
  ```bash
  git unused         # Show branches that would be deleted
  git unused -D      # Actually delete the unused branches
  ```

### Git History Management
- **`git-update-author`** - Updates author/committer email in commit history
  ```bash
  git-update-author old@email.com new@email.com
  git-update-author old@email.com  # Uses current git config user.email
  ```

## Git Aliases

### Commit Aliases
```bash
git c "message"              # git commit -m "message"
git ca                       # git commit -a
git cm "message"             # git commit -m "message"
git cam "message"            # git commit -am "message"
```

### Diff Aliases
```bash
git d                        # git diff
git dc                       # git diff --cached
```

### Log Aliases
```bash
git l                        # Pretty log with graph
```

### Open Aliases
```bash
git open                     # Open repository in browser
git browse                   # Alternative to git open
```

## Configuration Details

### User Settings
```ini
[user]
  name = Ian Anderson
  email = ianderson@example.com
```

### Core Settings
```ini
[core]
  editor = vi
  excludesfile = ~/.gitignore
  autocrlf = input
```

### Color Settings
```ini
[color]
  branch = auto
  diff = auto
  interactive = auto
  status = auto
```

### Merge Tool
```ini
[merge]
  tool = kdiff3
```

### Credential Helper
```ini
[credential]
  helper = osxkeychain
```

## Git Open Script Features

### URL Detection
- Automatically detects SSH vs HTTPS URLs
- Converts SSH URLs to HTTPS for browser compatibility
- Supports various Git hosting services

### Browser Support
- **macOS**: Uses `open` command
- **Linux**: Uses `xdg-open` command  
- **Windows**: Uses `start` command

### Advanced Features
- **File opening**: Open specific files in the repository
- **Line numbers**: Jump to specific lines in files
- **Branch support**: Open specific branches
- **Commit support**: Open specific commits
- **Help system**: Built-in help with examples

## Examples

### Repository Navigation
```bash
# Open current repository
git open

# Open specific branch
git open -b feature/new-feature

# Open specific commit
git open -c abc1234
```

### File Navigation
```bash
# Open specific file
git open -f src/components/Header.jsx

# Open file at specific line
git open -f src/utils/helpers.js -l 42

# Open file in specific branch
git open -f README.md -b main
```

### Workflow Integration
```bash
# After making changes, open the repository
git add .
git commit -m "Add new feature"
git push
git open  # Opens the repository to create a PR
```

## Troubleshooting

### Git Open Not Working
1. Check if the script is executable: `ls -la ~/.local/bin/git-open`
2. Verify Git repository: `git remote -v`
3. Check browser command: `which open` (macOS) or `which xdg-open` (Linux)

### Permission Issues
```bash
chmod +x ~/.local/bin/git-open
```

### SSH URL Issues
The script automatically converts SSH URLs to HTTPS:
- `git@github.com:user/repo.git` → `https://github.com/user/repo`

## Learn More

- [Git Documentation](https://git-scm.com/doc)
- [Git Aliases](https://git-scm.com/book/en/v2/Git-Basics-Git-Aliases)
- [GitHub CLI](https://cli.github.com/)
- [kdiff3 Documentation](https://kdiff3.sourceforge.net/)
