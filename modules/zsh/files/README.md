# Zsh Module with Prezto

This module provides a complete Zsh shell environment with the Prezto framework.

## Features

- **Zsh Shell**: Modern shell with powerful features
- **Prezto Framework**: Instant shell configuration and productivity boost
- **History Substring Search**: Search through command history
- **Syntax Highlighting**: Visual feedback for command syntax
- **Git Integration**: Enhanced Git prompt and helpers
- **Custom Configuration**: Integrated with your existing .zshrc

## Installation

This module is installed via `ansible-role-dotmodules`. It will:
1. Install Zsh and required packages via Homebrew
2. Deploy configuration files via GNU Stow
3. Provide setup script for Prezto installation

## Setup

After deployment, run the Prezto setup script:

```bash
~/.local/bin/setup-prezto.sh
```

This script will:
- Clone Prezto repository to `~/.zprezto`
- Create necessary symlinks
- Set Zsh as default shell (if not already)

## Configuration Files

- `.zshrc` - Main Zsh configuration
- `.zpreztorc` - Prezto module configuration
- `.inputrc` - Input configuration for readline
- `.local/bin/setup-prezto.sh` - Prezto installation script

## Prezto Modules

The default configuration includes:
- `environment` - Sets general shell options
- `terminal` - Terminal configuration
- `editor` - Editor configuration
- `history` - Command history management
- `directory` - Directory navigation helpers
- `spectrum` - Color support
- `utility` - General utility functions
- `completion` - Tab completion
- `prompt` - Customizable prompt
- `git` - Git aliases and prompt info
- `syntax-highlighting` - Command syntax highlighting
- `history-substring-search` - History search with arrows

## Usage

### Basic Commands

```bash
# Reload Zsh configuration
exec zsh

# Update Prezto
cd ~/.zprezto && git pull && git submodule update --init --recursive
```

### Prezto Commands

```bash
# Show Prezto modules
zprezto-show

# Update Prezto
zprezto-update
```

### Customization

To customize Prezto, edit `~/.zpreztorc` and modify:
- Module loading order
- Module-specific options
- Prompt theme
- Color schemes

## Troubleshooting

### Prezto Not Loading

If Prezto isn't loading, ensure:
1. Prezto is installed: `ls -la ~/.zprezto`
2. Symlinks are created: `ls -la ~/.zshrc ~/.zpreztorc`
3. Zsh is your default shell: `echo $SHELL`

### Re-run Setup

```bash
~/.local/bin/setup-prezto.sh
```

## Learn More

- [Prezto GitHub](https://github.com/sorin-ionescu/prezto)
- [Prezto Documentation](https://github.com/sorin-ionescu/prezto/tree/master/modules)
- [Zsh Documentation](https://zsh.sourceforge.io/Doc/)
