# Chrome Module

This module provides [Google Chrome](https://www.google.com/chrome/), the popular web browser with developer tools and extensive extension support.

## Features

- **Modern Web Browser** - Fast, secure browsing experience
- **Developer Tools** - Comprehensive DevTools for web development
- **Extension Ecosystem** - Thousands of extensions for productivity and development
- **Cross-Platform Sync** - Sync bookmarks, history, and settings across devices
- **Performance** - V8 JavaScript engine and optimized rendering

## What Gets Installed

### Applications
- **Google Chrome** - Installed via Homebrew Cask to `/Applications/`

### Configuration Files
- `.config/chrome/` - Configuration and settings (if needed)

### Installation Notes
- Installed via Homebrew Cask: `brew install --cask google-chrome`
- Available for both Apple Silicon (ARM64) and Intel (x86_64) Macs

## Usage

### Basic Commands
```bash
# Open Chrome
open -a "Google Chrome"

# Open Chrome with a specific URL
open -a "Google Chrome" https://example.com

# Open Chrome in incognito mode
open -a "Google Chrome" --args --incognito
```

### Developer Features
- **DevTools** - `Cmd+Option+I` to open developer tools
- **Console** - `Cmd+Option+J` to open JavaScript console
- **Inspect Element** - `Cmd+Shift+C` to inspect elements
- **Network Tab** - Monitor network requests and performance
- **Performance Profiling** - Analyze page load and runtime performance

## Common Extensions for Developers

### Development Tools
- **React Developer Tools** - Inspect React component hierarchies
- **Vue.js devtools** - Debug Vue.js applications
- **Redux DevTools** - Debug Redux state changes
- **Wappalyzer** - Identify technologies used on websites
- **JSON Formatter** - Pretty-print JSON in the browser

### Productivity
- **1Password** - Password management integration
- **Grammarly** - Writing assistance
- **Dark Reader** - Dark mode for all websites
- **uBlock Origin** - Ad blocker
- **Tab Wrangler** - Automatic tab management

## Integration

### With Development Tools
- **VS Code** - Debug web apps with Chrome DevTools Protocol
- **Cursor** - Test web applications during development
- **Node.js** - Debugging Node.js applications
- **iTerm2** - Launch Chrome from terminal

### With Productivity Apps
- **Alfred** - Quick launcher for Chrome and bookmarks
- **Obsidian** - Web clipper for saving articles
- **1Password** - Password autofill and management

## Configuration

### Settings Location
- **User Data**: `~/Library/Application Support/Google/Chrome/`
- **Preferences**: `~/Library/Application Support/Google/Chrome/Default/Preferences`
- **Extensions**: `~/Library/Application Support/Google/Chrome/Default/Extensions/`

### Useful Flags
```bash
# Launch with custom user data directory
open -a "Google Chrome" --args --user-data-dir=/path/to/profile

# Disable web security (for local development only!)
open -a "Google Chrome" --args --disable-web-security

# Enable experimental features
open -a "Google Chrome" --args --enable-experimental-web-platform-features
```

## Profiles

Chrome supports multiple profiles for different contexts:
- **Personal** - Personal browsing and accounts
- **Work** - Work-related browsing and accounts
- **Development** - Testing with different extensions and settings

Access profiles via: `Menu > Profiles` or `chrome://settings/manageProfile`

## Learn More

- [Chrome Website](https://www.google.com/chrome/)
- [Chrome DevTools Documentation](https://developer.chrome.com/docs/devtools/)
- [Chrome Extensions](https://chrome.google.com/webstore/category/extensions)
- [Chrome Flags](chrome://flags/) - Experimental features

