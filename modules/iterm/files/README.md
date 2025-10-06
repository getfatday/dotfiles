# iTerm2 Module

This module provides iTerm2, the advanced terminal emulator for macOS, with custom profiles, themes, and productivity features.

## Features

- **iTerm2 application** - Advanced terminal emulator for macOS
- **Custom profiles** - Development and server profiles
- **Color themes** - Dracula, Nord, and Solarized Dark themes
- **Productivity scripts** - Setup and theme management
- **Keyboard shortcuts** - Custom key mappings for efficiency
- **Integration** - Works with shell configurations

## What Gets Installed

### Homebrew Casks
- `iterm2` - Advanced terminal emulator

### Configuration Files
- `.config/iterm2/profiles/` - Custom iTerm2 profiles
- `.config/iterm2/themes/` - Color schemes and themes
- `.config/iterm2/scripts/` - iTerm2 automation scripts

## Profiles

### Development Profile
- **Background**: Dark theme with transparency
- **Font**: Monaco 12pt
- **Features**: Blur effect, transparency, custom key mappings
- **Shortcuts**: Split panes, new tabs, close tabs

### Server Profile
- **Background**: Black with green text (classic terminal look)
- **Font**: Monaco 11pt
- **Features**: No transparency, clear buffer, reset terminal
- **Shortcuts**: Clear buffer, reset terminal

## Themes

### Dracula
- **Background**: #282a36
- **Foreground**: #f8f8f2
- **Colors**: Vibrant purple, pink, and cyan accents
- **Style**: Dark theme with high contrast

### Nord
- **Background**: #2e3440
- **Foreground**: #d8dee9
- **Colors**: Arctic-inspired blue and gray palette
- **Style**: Calm, professional appearance

### Solarized Dark
- **Background**: #002b36
- **Foreground**: #839496
- **Colors**: Carefully designed color palette
- **Style**: Scientifically balanced for readability

## Usage

### Basic Commands
```bash
iterm                    # Open iTerm2
iterm-here               # Open iTerm2 in current directory
iterm-new                # Open new iTerm2 window
```

### Profile Management
```bash
iterm-profile development  # Open with development profile
iterm-profile server       # Open with server profile
```

### Theme Management
```bash
iterm-theme dracula        # Show Dracula theme installation
iterm-theme nord          # Show Nord theme installation
iterm-theme solarized-dark # Show Solarized Dark theme installation
```

### Setup Script
```bash
~/.config/iterm2/scripts/setup-iterm.sh
```

## Keyboard Shortcuts

### Development Profile
- `Cmd+D` - Split vertically
- `Cmd+Shift+D` - Split horizontally
- `Cmd+W` - Close tab
- `Cmd+T` - New tab

### Server Profile
- `Cmd+K` - Clear buffer
- `Cmd+R` - Reset terminal

## Configuration

### Preferences Location
- **Main preferences**: `~/Library/Preferences/com.googlecode.iterm2.plist`
- **Profiles**: `~/.config/iterm2/profiles/`
- **Themes**: `~/.config/iterm2/themes/`
- **Scripts**: `~/.config/iterm2/scripts/`

### Default Terminal
The setup script automatically sets iTerm2 as the default terminal:
```bash
defaults write com.apple.Terminal "Default Window Settings" -string "iTerm2"
defaults write com.apple.Terminal "Startup Window Settings" -string "iTerm2"
```

## Theme Installation

### Manual Installation
1. Open iTerm2
2. Go to **Preferences** > **Profiles** > **Colors**
3. Click **Color Presets** > **Import**
4. Select theme files from `~/.config/iterm2/themes/`
5. Click **Color Presets** > **Apply Preset** > **Theme Name**

### Available Themes
- **Dracula**: `~/.config/iterm2/themes/dracula.json`
- **Nord**: `~/.config/iterm2/themes/nord.json`
- **Solarized Dark**: `~/.config/iterm2/themes/solarized-dark.json`

## Advanced Features

### Split Panes
- **Vertical split**: `Cmd+D`
- **Horizontal split**: `Cmd+Shift+D`
- **Navigate**: `Cmd+[` and `Cmd+]`

### Tabs and Windows
- **New tab**: `Cmd+T`
- **New window**: `Cmd+N`
- **Close tab**: `Cmd+W`
- **Close window**: `Cmd+Shift+W`

### Search and Selection
- **Find**: `Cmd+F`
- **Find next**: `Cmd+G`
- **Find previous**: `Cmd+Shift+G`
- **Select all**: `Cmd+A`

### History and Navigation
- **Command history**: `Cmd+;`
- **Recent directories**: `Cmd+Shift+;`
- **Jump to mark**: `Cmd+J`

## Integration

### Shell Integration
iTerm2 works seamlessly with:
- **Zsh** - Enhanced shell experience
- **Oh My Zsh** - Framework integration
- **Prezto** - Zsh framework
- **Custom prompts** - Git status, directory info

### Development Tools
- **Git integration** - Enhanced Git commands
- **Node.js** - Terminal-based development
- **Docker** - Container management
- **Kubernetes** - Cluster management

## Troubleshooting

### iTerm2 Not Opening
```bash
# Check if iTerm2 is installed
ls -la /Applications/iTerm.app

# Reinstall if needed
brew install --cask iterm2
```

### Themes Not Working
1. Check theme file exists: `ls ~/.config/iterm2/themes/`
2. Verify JSON format: `cat ~/.config/iterm2/themes/dracula.json`
3. Reimport theme in iTerm2 preferences

### Profiles Not Loading
1. Check profile files: `ls ~/.config/iterm2/profiles/`
2. Verify JSON format
3. Restart iTerm2

### Default Terminal Not Set
```bash
# Set iTerm2 as default terminal
defaults write com.apple.Terminal "Default Window Settings" -string "iTerm2"
defaults write com.apple.Terminal "Startup Window Settings" -string "iTerm2"
```

## Learn More

- [iTerm2 Documentation](https://iterm2.com/documentation.html)
- [iTerm2 Features](https://iterm2.com/features.html)
- [iTerm2 Scripts](https://iterm2.com/python-api/)
- [iTerm2 Color Schemes](https://iterm2colorschemes.com/)
- [iTerm2 Profiles](https://iterm2.com/profiles.html)
