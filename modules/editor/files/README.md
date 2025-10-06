# Editor Module

This module provides a comprehensive Emacs development environment with Prelude framework and custom configuration.

## Features

- **Emacs with Prelude** - Complete Emacs setup with Prelude framework
- **Custom Configuration** - Personal Emacs configuration from legacy setup
- **TypeScript Support** - Full TypeScript development environment
- **LSP Integration** - Language Server Protocol support
- **Web Development** - Web mode and modern web development tools
- **Editor Scripts** - Productivity scripts for Emacs management

## What Gets Installed

### Homebrew Packages
- `emacs` - GNU Emacs text editor
- `vim` - Vi Improved text editor
- `neovim` - Modern Vim implementation

### Configuration Files
- `.emacs.d/` - Complete Emacs configuration directory
- `.zshrc` - Editor aliases and functions (merged)
- `.zshenv` - Editor environment variables (merged)
- `.local/bin/emacs-*` - Emacs management scripts

## Emacs Configuration

### Prelude Modules Enabled
- **prelude-ivy** - Modern completion system
- **prelude-company** - Auto-completion framework
- **prelude-emacs-lisp** - Emacs Lisp development
- **prelude-lisp** - Common Lisp setup
- **prelude-lsp** - Language Server Protocol
- **prelude-shell** - Shell integration
- **prelude-yaml** - YAML support

### Custom Features
- **Dracula Theme** - Dark theme with syntax highlighting
- **TypeScript Support** - Full TypeScript development
- **Web Mode** - Modern web development
- **LSP Grammarly** - Grammar checking integration
- **Custom Key Bindings** - Optimized key combinations
- **Mouse Support** - iTerm2 mouse integration

## Editor Aliases

### Emacs Aliases
- `e` - Open Emacs in current directory
- `en` - Open Emacs in new frame
- `eek` - Kill all Emacs processes
- `er` - Restart Emacs
- `ec` - Clean Emacs

## Editor Scripts

### Emacs Management
- **`emacs-clean`** - Clean up Emacs lock files
- **`emacs-restart`** - Restart Emacs service

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

### Emacs Management
```bash
# Clean up lock files
~/.local/bin/emacs-clean

# Restart Emacs service
~/.local/bin/emacs-restart
```

### Development Features
- **TypeScript**: Full TypeScript support with LSP
- **Web Development**: Web mode for modern web development
- **Grammar Checking**: LSP Grammarly integration
- **Auto-completion**: Company mode with intelligent completion

## Configuration Details

### Personal Configuration
- **Theme**: Dracula theme with transparency
- **Key Bindings**: Custom key combinations for productivity
- **Mouse Support**: Full mouse support for iTerm2
- **Backup Settings**: Configured backup and version control
- **Whitespace**: Custom whitespace handling

### Development Setup
- **TypeScript**: Full TypeScript development environment
- **LSP**: Language Server Protocol integration
- **Web Mode**: Modern web development support
- **Grammar**: LSP Grammarly integration for text editing

## Learn More

- [Emacs Documentation](https://www.gnu.org/software/emacs/documentation.html)
- [Prelude Framework](https://github.com/bbatsov/prelude)
- [Vim Documentation](https://vimdoc.sourceforge.net/)
- [Neovim Documentation](https://neovim.io/doc/)
