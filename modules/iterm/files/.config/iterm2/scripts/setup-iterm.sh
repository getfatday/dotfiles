#!/bin/bash

# iTerm2 setup script
# This script sets up iTerm2 with custom profiles and themes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if iTerm2 is installed
if ! [ -d "/Applications/iTerm.app" ]; then
    error "iTerm2 is not installed. Please install it first:"
    echo "  brew install --cask iterm2"
    exit 1
fi

info "Setting up iTerm2..."

# Create iTerm2 preferences directory if it doesn't exist
mkdir -p ~/Library/Preferences

# Backup existing preferences
if [ -f ~/Library/Preferences/com.googlecode.iterm2.plist ]; then
    info "Backing up existing iTerm2 preferences..."
    cp ~/Library/Preferences/com.googlecode.iterm2.plist ~/Library/Preferences/com.googlecode.iterm2.plist.backup.$(date +%Y%m%d_%H%M%S)
    success "Preferences backed up"
fi

# Create iTerm2 configuration directory
mkdir -p ~/.config/iterm2/{profiles,themes,scripts}

# Copy configuration files
if [ -d ~/.dotmodules/iterm/.config/iterm2 ]; then
    info "Copying iTerm2 configuration files..."
    cp -r ~/.dotmodules/iterm/.config/iterm2/* ~/.config/iterm2/
    success "Configuration files copied"
else
    warning "iTerm2 configuration files not found in ~/.dotmodules/iterm/"
fi

# Set up iTerm2 as default terminal (optional)
info "Setting up iTerm2 as default terminal..."
defaults write com.apple.Terminal "Default Window Settings" -string "iTerm2"
defaults write com.apple.Terminal "Startup Window Settings" -string "iTerm2"
success "iTerm2 set as default terminal"

# Create useful aliases
info "Creating iTerm2 aliases..."
cat >> ~/.zshrc << 'EOF'

# iTerm2 aliases
alias iterm="open -a iTerm"
alias iterm-here="open -a iTerm ."
alias iterm-new="open -a iTerm --args --new-window"

# iTerm2 functions
iterm-profile() {
    if [ -z "$1" ]; then
        echo "Usage: iterm-profile <profile-name>"
        echo "Available profiles: development, server"
        return 1
    fi
    open -a iTerm --args --profile "$1"
}

EOF

success "iTerm2 aliases added to ~/.zshrc"

# Create iTerm2 profile switcher
info "Creating iTerm2 profile switcher..."
cat > ~/.local/bin/iterm-profile << 'EOF'
#!/bin/bash

# iTerm2 profile switcher
# Usage: iterm-profile <profile-name>

if [ -z "$1" ]; then
    echo "Usage: iterm-profile <profile-name>"
    echo "Available profiles: development, server"
    exit 1
fi

open -a iTerm --args --profile "$1"
EOF

chmod +x ~/.local/bin/iterm-profile
success "iTerm2 profile switcher created"

# Create iTerm2 theme installer
info "Creating iTerm2 theme installer..."
cat > ~/.local/bin/iterm-theme << 'EOF'
#!/bin/bash

# iTerm2 theme installer
# Usage: iterm-theme <theme-name>

if [ -z "$1" ]; then
    echo "Usage: iterm-theme <theme-name>"
    echo "Available themes: dracula, nord, solarized-dark"
    exit 1
fi

THEME_FILE="$HOME/.config/iterm2/themes/$1.json"
if [ ! -f "$THEME_FILE" ]; then
    echo "Theme file not found: $THEME_FILE"
    exit 1
fi

echo "Theme file found: $THEME_FILE"
echo "To install this theme:"
echo "1. Open iTerm2"
echo "2. Go to Preferences > Profiles > Colors"
echo "3. Click 'Color Presets' > 'Import'"
echo "4. Select: $THEME_FILE"
echo "5. Click 'Color Presets' > 'Apply Preset' > '$1'"
EOF

chmod +x ~/.local/bin/iterm-theme
success "iTerm2 theme installer created"

success "iTerm2 setup complete!"
info "Available commands:"
info "  iterm                    # Open iTerm2"
info "  iterm-here               # Open iTerm2 in current directory"
info "  iterm-new                # Open new iTerm2 window"
info "  iterm-profile <name>     # Open iTerm2 with specific profile"
info "  iterm-theme <name>       # Show theme installation instructions"
info ""
info "Available profiles: development, server"
info "Available themes: dracula, nord, solarized-dark"
info ""
info "To apply themes:"
info "1. Open iTerm2"
info "2. Go to Preferences > Profiles > Colors"
info "3. Click 'Color Presets' > 'Import'"
info "4. Select theme files from ~/.config/iterm2/themes/"
info "5. Apply the desired theme"
