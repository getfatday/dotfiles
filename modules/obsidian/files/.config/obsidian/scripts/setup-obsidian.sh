#!/bin/bash

# Obsidian setup script
# This script sets up Obsidian with custom templates and configurations

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

# Check if Obsidian is installed
if ! [ -d "/Applications/Obsidian.app" ]; then
    error "Obsidian is not installed. Please install it first:"
    echo "  brew install --cask obsidian"
    exit 1
fi

info "Setting up Obsidian..."

# Create Obsidian configuration directory
mkdir -p ~/.config/obsidian/{templates,snippets,plugins}

# Copy configuration files
if [ -d ~/.dotmodules/obsidian/.config/obsidian ]; then
    info "Copying Obsidian configuration files..."
    cp -r ~/.dotmodules/obsidian/.config/obsidian/* ~/.config/obsidian/
    success "Configuration files copied"
else
    warning "Obsidian configuration files not found in ~/.dotmodules/obsidian/"
fi

# Create useful aliases
info "Creating Obsidian aliases..."
cat >> ~/.zshrc << 'EOF'

# Obsidian aliases
alias obsidian="open -a Obsidian"
alias obsidian-vault="open -a Obsidian --args --vault"

# Obsidian functions
obsidian-new-vault() {
    if [ -z "$1" ]; then
        echo "Usage: obsidian-new-vault <vault-name> [path]"
        echo "Example: obsidian-new-vault 'My Vault' ~/Documents/Obsidian"
        return 1
    fi

    local vault_name="$1"
    local vault_path="${2:-$HOME/Documents/Obsidian/$vault_name}"

    mkdir -p "$vault_path"
    open -a Obsidian --args --vault "$vault_path"
    echo "Created new Obsidian vault: $vault_name at $vault_path"
}

obsidian-open-vault() {
    if [ -z "$1" ]; then
        echo "Usage: obsidian-open-vault <vault-path>"
        echo "Example: obsidian-open-vault ~/Documents/Obsidian/MyVault"
        return 1
    fi

    if [ ! -d "$1" ]; then
        echo "Vault directory not found: $1"
        return 1
    fi

    open -a Obsidian --args --vault "$1"
    echo "Opened Obsidian vault: $1"
}

EOF

success "Obsidian aliases added to ~/.zshrc"

# Create Obsidian vault manager
info "Creating Obsidian vault manager..."
cat > ~/.local/bin/obsidian-vault << 'EOF'
#!/bin/bash

# Obsidian vault manager
# Usage: obsidian-vault <command> [options]

case "$1" in
    "new")
        if [ -z "$2" ]; then
            echo "Usage: obsidian-vault new <vault-name> [path]"
            exit 1
        fi
        obsidian-new-vault "$2" "$3"
        ;;
    "open")
        if [ -z "$2" ]; then
            echo "Usage: obsidian-vault open <vault-path>"
            exit 1
        fi
        obsidian-open-vault "$2"
        ;;
    "list")
        echo "Available Obsidian vaults:"
        find ~/Documents -name "*.obsidian" -type d 2>/dev/null | while read -r vault; do
            vault_dir=$(dirname "$vault")
            vault_name=$(basename "$vault_dir")
            echo "  - $vault_name: $vault_dir"
        done
        ;;
    *)
        echo "Usage: obsidian-vault <command> [options]"
        echo ""
        echo "Commands:"
        echo "  new <name> [path]    Create a new vault"
        echo "  open <path>          Open an existing vault"
        echo "  list                 List available vaults"
        ;;
esac
EOF

chmod +x ~/.local/bin/obsidian-vault
success "Obsidian vault manager created"

# Create Obsidian template installer
info "Creating Obsidian template installer..."
cat > ~/.local/bin/obsidian-templates << 'EOF'
#!/bin/bash

# Obsidian template installer
# Usage: obsidian-templates <vault-path>

if [ -z "$1" ]; then
    echo "Usage: obsidian-templates <vault-path>"
    echo "Example: obsidian-templates ~/Documents/Obsidian/MyVault"
    exit 1
fi

VAULT_PATH="$1"
TEMPLATES_DIR="$VAULT_PATH/.obsidian/templates"

if [ ! -d "$VAULT_PATH" ]; then
    echo "Vault directory not found: $VAULT_PATH"
    exit 1
fi

echo "Installing templates to: $TEMPLATES_DIR"
mkdir -p "$TEMPLATES_DIR"

# Copy templates from configuration
if [ -d ~/.config/obsidian/templates ]; then
    cp ~/.config/obsidian/templates/* "$TEMPLATES_DIR/"
    echo "Templates installed successfully!"
    echo "Available templates:"
    ls -la "$TEMPLATES_DIR"
else
    echo "No templates found in ~/.config/obsidian/templates"
fi
EOF

chmod +x ~/.local/bin/obsidian-templates
success "Obsidian template installer created"

# Create default vault if it doesn't exist
DEFAULT_VAULT="$HOME/Documents/Obsidian/Personal"
if [ ! -d "$DEFAULT_VAULT" ]; then
    info "Creating default Obsidian vault..."
    mkdir -p "$DEFAULT_VAULT"
    success "Default vault created: $DEFAULT_VAULT"
fi

success "Obsidian setup complete!"
info "Available commands:"
info "  obsidian                    # Open Obsidian"
info "  obsidian-vault new <name>   # Create new vault"
info "  obsidian-vault open <path>  # Open existing vault"
info "  obsidian-vault list         # List available vaults"
info "  obsidian-templates <path>  # Install templates to vault"
info ""
info "Default vault: $DEFAULT_VAULT"
info ""
info "To get started:"
info "1. Open Obsidian: obsidian"
info "2. Create a new vault or open existing one"
info "3. Install templates: obsidian-templates <vault-path>"
info "4. Start taking notes and organizing your knowledge!"
info ""
info "Web Clipper:"
info "- Install the Obsidian Web Clipper from the Mac App Store"
info "- Configure it to work with your vault"
info "- Use templates for consistent web content formatting"
