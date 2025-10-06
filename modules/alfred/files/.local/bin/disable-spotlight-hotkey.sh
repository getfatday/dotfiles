#!/bin/bash

# Disable Spotlight hotkey (Command+Space) to avoid conflicts with Alfred
# This script properly handles the symbolic hotkeys configuration

echo "Disabling Spotlight hotkey (Command+Space) to avoid conflicts with Alfred..."

# Method 1: Use the correct syntax for symbolic hotkeys
# Note: This may require manual configuration in System Preferences
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 64 -dict-add enabled -bool false 2>/dev/null || {
    echo "Note: The defaults command failed. You may need to manually disable Spotlight hotkey:"
    echo "1. Open System Preferences > Keyboard > Shortcuts"
    echo "2. Select 'Spotlight' from the left sidebar"
    echo "3. Uncheck 'Show Spotlight search' or change the shortcut"
    echo "4. This will allow Alfred to use Command+Space without conflicts"
}

echo ""
echo "Spotlight hotkey should be disabled. Please log out and log back in for changes to take effect."
echo "Alfred can now use Command+Space as its default hotkey without conflicts."
