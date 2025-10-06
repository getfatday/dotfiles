# Productivity Module

This module provides productivity tools and navigation utilities for enhanced shell productivity.

## Features

- **Auto Jump** - Intelligent directory jumping
- **Z Navigation** - Fast directory navigation
- **Fuzzy Finding** - Enhanced file searching with fzf
- **Productivity Aliases** - Common productivity shortcuts

## What Gets Installed

### Homebrew Packages
- `autojump` - Intelligent directory jumping
- `z` - Fast directory navigation
- `fzf` - Command-line fuzzy finder

### Configuration Files
- `.zshrc` - Productivity aliases and functions (merged)

## Productivity Aliases

### Navigation
- `f` - Find files by name
- `jc` - Jump complete
- `jw` - Jump window
- `reload` - Reload shell configuration

### System Management
- `wtfu` - Keep system awake (caffeinate)
- `fs` - Foreman start

## Functions

### History Management
- `redact` - Remove specific commands from shell history

## Usage

### Directory Navigation
```bash
# Jump to frequently used directories
j project-name
j ~/Documents

# Auto jump to directories
j /path/to/directory
```

### File Finding
```bash
# Find files by name
f "*.txt"
f "config"
```

### System Productivity
```bash
# Keep system awake
wtfu

# Start foreman processes
fs
```

### History Management
```bash
# Remove sensitive commands from history
redact "password"
redact "secret"
```

## Configuration

The module automatically configures:
- Auto jump for intelligent directory navigation
- Z for fast directory jumping
- FZF for fuzzy finding
- Productivity aliases and functions

## Learn More

- [Auto Jump](https://github.com/wting/autojump)
- [Z Directory Jumper](https://github.com/rupa/z)
- [FZF Fuzzy Finder](https://github.com/junegunn/fzf)
