---
description: AI-assisted module installation
args:
  - name: package
    description: Package, app, or tool name to install
    required: true
---

The user wants to install: $ARGUMENTS

Help install this package into the dotfiles system:

1. Search for the package:
   - `brew search $ARGUMENTS` for Homebrew formulae and casks
   - `mas search $ARGUMENTS` for Mac App Store apps

2. Determine the best fit:
   - Check if it belongs in an existing module: `dotm list --installed` and read relevant config.yml files
   - If it fits an existing module, update that module's config.yml
   - If it needs a new module, use `dotm create`

3. Install and verify:
   - Run `dotm install <module>` if using an existing module
   - Or create a new module with `dotm create <name> --brew <pkg>` (or --cask/--mas)
   - Run `dotm verify <module>` to confirm success

4. Report what was done and verify the installation worked.
