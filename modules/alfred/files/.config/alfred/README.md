# Alfred Module

This module provides [Alfred](https://www.alfredapp.com), the award-winning productivity launcher for macOS, with custom workflows, snippets, and automation features.

## Features

- **Alfred application** - Productivity launcher and automation tool
- **Custom workflows** - Git operations and productivity automation
- **Text snippets** - Development, email, and Git snippets
- **Productivity scripts** - Setup and workflow management
- **Integration** - Works with other development tools
- **Hotkeys and keywords** - Custom shortcuts for efficiency
- **Spotlight Integration** - Disables default macOS Spotlight hotkey to avoid conflicts

## What Gets Installed

### Homebrew Casks
- `alfred` - Productivity launcher and automation tool

### Configuration Files
- `.config/alfred/workflows/` - Custom Alfred workflows
- `.config/alfred/snippets/` - Text expansion snippets
- `.config/alfred/themes/` - Custom Alfred themes

### System Configuration
- **Spotlight Hotkey Disabled** - Disables default macOS Spotlight (Command+Space) to avoid conflicts with Alfred
- **Alfred Hotkey** - Alfred can now use Command+Space as its default hotkey without conflicts
- **Setup Script** - `~/.local/bin/disable-spotlight-hotkey.sh` - Manual script to disable Spotlight hotkey

## Workflows

### Git Operations Workflow
- **Keyword**: `git` - Git operations launcher
- **Features**: Git status, push, and common operations
- **Integration**: Works with your Git configuration

## Snippets

### Development Snippets
- **`cl`** - `console.log('$1');` - JavaScript console logging
- **`gc`** - `git commit -m "$1"` - Git commit with message
- **`br`** - `Best regards, Ian Anderson` - Email signature

## Usage

### Basic Commands
```bash
alfred                    # Open Alfred
alfred-prefs              # Open Alfred preferences
alfred-search "query"     # Search with Alfred
```

### Workflow Management
```bash
alfred-workflow git-operations  # Show Git workflow installation
```

### System Configuration
```bash
# Disable Spotlight hotkey to avoid conflicts with Alfred
~/.local/bin/disable-spotlight-hotkey.sh

# Note: Requires logout/login for changes to take effect
```

### Snippet Management
```bash
alfred-snippet development      # Show development snippets
alfred-snippet email           # Show email snippets
alfred-snippet git             # Show Git snippets
```

### Setup Script
```bash
~/.local/bin/setup-alfred.sh
```

## Alfred Features

### Core Features (Free)
- **App launching** - Launch applications with Cmd+Space
- **File search** - Find files and folders quickly
- **Web search** - Search the web with custom keywords
- **Calculator** - Quick calculations
- **System commands** - Sleep, restart, empty trash
- **Clipboard history** - Access copied items
- **Text snippets** - Auto-expand frequently used text

### Powerpack Features (Paid)
- **Workflows** - Custom automation and productivity tools
- **Themes** - Custom Alfred appearance
- **Advanced features** - Deep system integration
- **Remote control** - Control Alfred from iPhone/iPad

## Configuration

### Preferences Location
- **Main preferences**: `~/Library/Preferences/com.runningwithcrayons.Alfred-Preferences.plist`
- **Workflows**: `~/.config/alfred/workflows/`
- **Snippets**: `~/.config/alfred/snippets/`
- **Themes**: `~/.config/alfred/themes/`

### Default Hotkey
- **Cmd+Space** - Open Alfred (default)
- **Cmd+Option+Space** - Open Alfred preferences

## Workflow Installation

### Manual Installation
1. Open Alfred
2. Go to **Preferences** > **Workflows**
3. Click **+** button > **Import Workflow**
4. Select workflow files from `~/.config/alfred/workflows/`
5. Workflows will be imported and available

### Available Workflows
- **Git Operations**: `git-operations.alfredworkflow`
  - Keyword: `git` - Git operations launcher
  - Features: Status, push, commit operations

## Snippet Installation

### Manual Installation
1. Open Alfred
2. Go to **Preferences** > **Features** > **Snippets**
3. Click **+** button > **Import Snippets**
4. Select snippet files from `~/.config/alfred/snippets/`
5. Snippets will be imported and available

### Available Snippets
- **Development**: `development.json`
  - `cl` → `console.log('$1');`
- **Email**: `email.json`
  - `br` → `Best regards, Ian Anderson`
- **Git**: `git.json`
  - `gc` → `git commit -m "$1"`

## Advanced Features

### Custom Keywords
- **`git`** - Git operations workflow
- **`cl`** - Console log snippet
- **`gc`** - Git commit snippet
- **`br`** - Best regards snippet

### Integration
- **Git integration** - Works with your Git configuration
- **Terminal integration** - Launch terminal commands
- **File system** - Navigate and manage files
- **Web search** - Custom search engines

### Productivity Tips
- **Hotkeys** - Custom keyboard shortcuts
- **Keywords** - Quick access to functions
- **Workflows** - Automate repetitive tasks
- **Snippets** - Save time typing

## Troubleshooting

### Alfred Not Opening
```bash
# Check if Alfred is installed
ls -la "/Applications/Alfred 5.app"

# Reinstall if needed
brew install --cask alfred
```

### Workflows Not Working
1. Check workflow files: `ls ~/.config/alfred/workflows/`
2. Verify Alfred Powerpack is installed
3. Import workflows in Alfred preferences

### Snippets Not Working
1. Check snippet files: `ls ~/.config/alfred/snippets/`
2. Verify JSON format
3. Import snippets in Alfred preferences

### Default Launcher Not Set
```bash
# Set Alfred as default launcher
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 64 -dict-add enabled -bool false
```

## Learn More

- [Alfred Documentation](https://www.alfredapp.com/help/)
- [Alfred Workflows](https://www.alfredapp.com/workflows/)
- [Alfred Powerpack](https://www.alfredapp.com/powerpack/)
- [Alfred Remote](https://www.alfredapp.com/remote/)
- [Alfred Themes](https://www.alfredapp.com/themes/)
