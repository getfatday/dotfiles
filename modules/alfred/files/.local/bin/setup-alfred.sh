#!/bin/bash

# Alfred setup script
# This script sets up Alfred with custom workflows and snippets

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

# Check if Alfred is installed
if ! [ -d "/Applications/Alfred 5.app" ]; then
    error "Alfred is not installed. Please install it first:"
    echo "  brew install --cask alfred"
    exit 1
fi

info "Setting up Alfred..."

# Create Alfred configuration directory
mkdir -p ~/.config/alfred/{workflows,snippets,themes}

# Copy configuration files
if [ -d ~/.dotmodules/alfred/.config/alfred ]; then
    info "Copying Alfred configuration files..."
    cp -r ~/.dotmodules/alfred/.config/alfred/* ~/.config/alfred/
    success "Configuration files copied"
else
    warning "Alfred configuration files not found in ~/.dotmodules/alfred/"
fi

# Create useful aliases
info "Creating Alfred aliases..."
cat >> ~/.zshrc << 'EOF'

# Alfred aliases
alias alfred="open -a 'Alfred 5'"
alias alfred-prefs="open -a 'Alfred 5' --args --preferences"

# Alfred functions
alfred-search() {
    if [ -z "$1" ]; then
        echo "Usage: alfred-search <query>"
        return 1
    fi
    osascript -e "tell application \"Alfred 5\" to search \"$1\""
}

alfred-workflow() {
    if [ -z "$1" ]; then
        echo "Usage: alfred-workflow <workflow-name>"
        echo "Available workflows: git-operations"
        return 1
    fi
    osascript -e "tell application \"Alfred 5\" to search \"$1\""
}

EOF

success "Alfred aliases added to ~/.zshrc"

# Create Alfred workflow installer
info "Creating Alfred workflow installer..."
cat > ~/.local/bin/alfred-workflow << 'EOF'
#!/bin/bash

# Alfred workflow installer
# Usage: alfred-workflow <workflow-name>

if [ -z "$1" ]; then
    echo "Usage: alfred-workflow <workflow-name>"
    echo "Available workflows: git-operations"
    exit 1
fi

WORKFLOW_FILE="$HOME/.config/alfred/workflows/$1.alfredworkflow"
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "Workflow file not found: $WORKFLOW_FILE"
    exit 1
fi

echo "Workflow file found: $WORKFLOW_FILE"
echo "To install this workflow:"
echo "1. Open Alfred"
echo "2. Go to Preferences > Workflows"
echo "3. Click the '+' button > Import Workflow"
echo "4. Select: $WORKFLOW_FILE"
echo "5. The workflow will be imported and available"
EOF

chmod +x ~/.local/bin/alfred-workflow
success "Alfred workflow installer created"

# Create Alfred snippet installer
info "Creating Alfred snippet installer..."
cat > ~/.local/bin/alfred-snippet << 'EOF'
#!/bin/bash

# Alfred snippet installer
# Usage: alfred-snippet <snippet-name>

if [ -z "$1" ]; then
    echo "Usage: alfred-snippet <snippet-name>"
    echo "Available snippets: development, email, git"
    exit 1
fi

SNIPPET_FILE="$HOME/.config/alfred/snippets/$1.json"
if [ ! -f "$SNIPPET_FILE" ]; then
    echo "Snippet file not found: $SNIPPET_FILE"
    exit 1
fi

echo "Snippet file found: $SNIPPET_FILE"
echo "To install this snippet:"
echo "1. Open Alfred"
echo "2. Go to Preferences > Features > Snippets"
echo "3. Click the '+' button > Import Snippets"
echo "4. Select: $SNIPPET_FILE"
echo "5. The snippet will be imported and available"
EOF

chmod +x ~/.local/bin/alfred-snippet
success "Alfred snippet installer created"

# Set up Alfred as default launcher (optional)
info "Setting up Alfred as default launcher..."
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 64 -dict-add enabled -bool false
success "Alfred set as default launcher"

success "Alfred setup complete!"
info "Available commands:"
info "  alfred                    # Open Alfred"
info "  alfred-prefs              # Open Alfred preferences"
info "  alfred-search <query>     # Search with Alfred"
info "  alfred-workflow <name>    # Show workflow installation instructions"
info "  alfred-snippet <name>     # Show snippet installation instructions"
info ""
info "Available workflows: git-operations"
info "Available snippets: development, email, git"
info ""
info "To install workflows and snippets:"
info "1. Open Alfred"
info "2. Go to Preferences > Workflows/Snippets"
info "3. Import files from ~/.config/alfred/"
info ""
info "Default hotkey: Cmd+Space"
info "Powerpack features require Alfred Powerpack license"
