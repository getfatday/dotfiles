# Editor Module

This module provides a comprehensive text editor environment with Emacs as the primary editor.

## Features

- **Emacs Configuration** - Complete Emacs setup
- **Editor Aliases** - Productivity shortcuts
- **Environment Variables** - Proper editor configuration
- **Editor Integration** - Shell integration for editors

## What Gets Installed

### Homebrew Packages
- `emacs` - GNU Emacs text editor
- `vim` - Vi Improved text editor
- `neovim` - Modern Vim implementation

### Configuration Files
- `.zshrc` - Editor aliases and functions (merged)
- `.zshenv` - Editor environment variables (merged)

## Editor Aliases

### Emacs Aliases
- `e` - Open Emacs in current directory
- `en` - Open Emacs in new frame
- `eek` - Kill all Emacs processes
- `er` - Restart Emacs
- `ec` - Clean Emacs

## Environment Variables

- `EDITOR` - Set to `emacsclient -t`
- `VISUAL` - Set to `emacsclient -t`

## Usage

### Basic Editor Operations
```bash
# Open Emacs in current directory
e

# Open specific file
e filename.txt

# Open Emacs in new frame
en

# Clean Emacs processes
ec
```

### Editor Integration
The module automatically configures:
- Default editor for Git operations
- Shell integration for editors
- Proper environment variables
- Editor aliases and functions

## Configuration

The module provides:
- Emacs as the default editor
- Editor environment variables
- Shell integration
- Productivity aliases

## Learn More

- [Emacs Documentation](https://www.gnu.org/software/emacs/documentation.html)
- [Vim Documentation](https://vimdoc.sourceforge.net/)
- [Neovim Documentation](https://neovim.io/doc/)
