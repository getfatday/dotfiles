---
description: AI-assisted module creation
args:
  - name: description
    description: Description of what this module should contain
    required: true
---

Create a dotfiles module based on: $ARGUMENTS

1. Understand the request and search for relevant packages:
   - `brew search` for relevant Homebrew formulae and casks
   - `mas search` for relevant Mac App Store apps
   - Check what's currently installed: `brew list`, `brew list --cask`

2. Check for conflicts with existing modules:
   - Run `dotm list` to see existing modules
   - Read config.yml files for modules that might overlap

3. Propose a module:
   - Suggest a module name (lowercase, hyphenated if needed)
   - List homebrew_packages, homebrew_casks, mas_installed_apps as appropriate
   - Decide if it needs stow_dirs (for config files)
   - Show the proposed config.yml

4. After user approval:
   - Create the module: `dotm create <name> --brew <pkgs> --cask <casks>`
   - Run security scan: `dotm push --dry-run`
   - Verify: `dotm verify <name>`

5. If the module needs dotfiles (config files), create them in the files/ directory.
