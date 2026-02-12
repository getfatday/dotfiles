# Spotify Module

## Overview

The Spotify module provides automated installation of the Spotify music streaming application via Homebrew Cask. This module follows the dotfiles constitution principles of modularity, idempotency, and automation-first deployment.

## What Gets Installed

- **Spotify Application**: The official Spotify desktop application for macOS
- **Cross-Platform Support**: Works on both Apple Silicon (ARM64) and Intel (x86_64) Macs
- **Homebrew Integration**: Installed via Homebrew Cask for consistent package management

## Features

- **Music Streaming**: Access to Spotify's full music library
- **Offline Playback**: Download music for offline listening
- **Cross-Device Sync**: Seamless playback across devices
- **High-Quality Audio**: Support for high-quality audio streaming
- **Podcast Support**: Access to Spotify's podcast library
- **Social Features**: Share music and discover new content

## Usage

### Launching Spotify

After deployment, Spotify will be available in your Applications folder:

1. **Finder**: Navigate to Applications → Spotify
2. **Spotlight**: Press `Cmd+Space`, type "Spotify", press Enter
3. **Launchpad**: Click the Spotify icon in Launchpad
4. **Dock**: If you've added it to your dock, click the Spotify icon

### First-Time Setup

1. **Launch Spotify** using any method above
2. **Sign In** with your Spotify account credentials
3. **Choose Plan** (Free or Premium)
4. **Start Listening** to your music

### Basic Usage

- **Search**: Use the search bar to find artists, albums, or songs
- **Playlists**: Create and manage your playlists
- **Library**: Access your saved music and podcasts
- **Browse**: Discover new music and podcasts
- **Settings**: Customize audio quality, download settings, and preferences

## Integration with Other Modules

This module works independently and doesn't require other modules. However, it integrates well with:

- **macos**: Uses macOS system preferences and notifications
- **zsh**: Can be launched from terminal (if added to PATH)
- **productivity**: Fits into productivity workflows

## Configuration

### Audio Quality Settings

1. Open Spotify
2. Go to **Spotify** → **Preferences** (or `Cmd+,`)
3. Scroll to **Audio Quality**
4. Choose your preferred quality:
   - **Normal**: 96 kbps
   - **High**: 160 kbps  
   - **Very High**: 320 kbps (Premium only)

### Download Settings

1. Go to **Preferences** → **Local Files**
2. Configure download location and quality
3. Set storage limits for offline content

### Keyboard Shortcuts

Spotify supports many keyboard shortcuts:

- **Space**: Play/Pause
- **Cmd+Right**: Next track
- **Cmd+Left**: Previous track
- **Cmd+Up**: Volume up
- **Cmd+Down**: Volume down
- **Cmd+L**: Like/Unlike current track

## Troubleshooting

### Spotify Won't Launch

**Symptoms**: Spotify icon appears but application doesn't start

**Solutions**:
1. **Restart Spotify**: Force quit and relaunch
2. **Check Permissions**: Ensure Spotify has necessary permissions in System Preferences
3. **Reinstall**: Run the deployment again to reinstall Spotify
4. **Clear Cache**: Delete `~/Library/Caches/com.spotify.client` and restart

### Audio Issues

**Symptoms**: No sound, distorted audio, or poor quality

**Solutions**:
1. **Check System Audio**: Ensure other apps can play audio
2. **Audio Output**: Check Spotify's audio output settings
3. **Audio Quality**: Verify quality settings in preferences
4. **Restart Audio**: Quit and restart Spotify

### Login Issues

**Symptoms**: Can't sign in or account issues

**Solutions**:
1. **Check Internet**: Ensure stable internet connection
2. **Account Status**: Verify account is active on Spotify's website
3. **Clear Data**: Sign out and sign back in
4. **Reset Password**: Use Spotify's password reset if needed

### Performance Issues

**Symptoms**: Slow loading, crashes, or high CPU usage

**Solutions**:
1. **Update Spotify**: Ensure you have the latest version
2. **Restart Application**: Force quit and relaunch
3. **Check Resources**: Monitor Activity Monitor for high usage
4. **Reinstall**: Run deployment to reinstall if needed

### Homebrew Issues

**Symptoms**: Installation fails or Spotify not found

**Solutions**:
1. **Update Homebrew**: `brew update && brew upgrade`
2. **Check Cask**: `brew list --cask | grep spotify`
3. **Reinstall Cask**: `brew reinstall --cask spotify`
4. **Run Deployment**: Use Ansible to reinstall via module

## Advanced Usage

### Command Line Integration

While Spotify doesn't have an official CLI, you can:

1. **Launch from Terminal**: `open -a Spotify`
2. **Use AppleScript**: Control Spotify via AppleScript
3. **Third-Party Tools**: Use tools like `shpotify` for CLI control

### Automation

- **Shortcuts App**: Create iOS/macOS shortcuts for Spotify
- **Automator**: Build workflows for Spotify automation
- **AppleScript**: Script Spotify for advanced automation

## Dependencies

- **macOS**: Requires macOS 10.15 or later
- **Homebrew**: Must be installed for automated deployment
- **Internet**: Required for music streaming and account access
- **Spotify Account**: Free or Premium account required

## Support

- **Spotify Support**: [support.spotify.com](https://support.spotify.com)
- **Community**: [community.spotify.com](https://community.spotify.com)
- **Documentation**: [developer.spotify.com](https://developer.spotify.com)

## Module Information

- **Module Type**: App-only (no configuration files)
- **Installation Method**: Homebrew Cask
- **Dependencies**: None (independent module)
- **Configuration Files**: None
- **Cross-Platform**: Yes (ARM64 and x86_64)

---

*This module follows the dotfiles constitution principles of modularity, idempotency, and automation-first deployment.*
