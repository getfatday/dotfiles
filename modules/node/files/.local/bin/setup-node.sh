#!/bin/bash

# Node.js development environment setup script
# This script sets up asdf and Node.js for development

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

# Check if asdf is installed
if ! command -v asdf &> /dev/null; then
    error "asdf is not installed. Please install it first:"
    echo "  brew install asdf"
    exit 1
fi

info "Setting up Node.js development environment..."

# Add asdf to shell
if ! grep -q "asdf" ~/.zshrc; then
    info "Adding asdf to shell configuration..."
    echo '' >> ~/.zshrc
    echo '# asdf version manager' >> ~/.zshrc
    echo '. $(brew --prefix asdf)/libexec/asdf.sh' >> ~/.zshrc
    success "Added asdf to ~/.zshrc"
fi

# Install Node.js plugin if not already installed
if ! asdf plugin list | grep -q "nodejs"; then
    info "Installing asdf Node.js plugin..."
    asdf plugin add nodejs https://github.com/asdf-vm/asdf-nodejs.git
    success "Installed asdf Node.js plugin"
else
    info "asdf Node.js plugin already installed"
fi

# Install Node.js version from .tool-versions
if [ -f .tool-versions ]; then
    info "Installing Node.js version from .tool-versions..."
    asdf install
    success "Installed Node.js version from .tool-versions"
else
    warning ".tool-versions file not found"
fi

# Install pnpm globally
if ! command -v pnpm &> /dev/null; then
    info "Installing pnpm globally..."
    npm install -g pnpm
    success "Installed pnpm globally"
else
    info "pnpm already installed"
fi

# Install common global packages
info "Installing common global packages..."
pnpm add -g typescript ts-node nodemon eslint prettier
success "Installed common global packages"

success "Node.js development environment setup complete!"
info "Available commands:"
info "  asdf list nodejs          # List installed Node.js versions"
info "  asdf install nodejs 20.11.0  # Install specific Node.js version"
info "  asdf global nodejs 20.11.0   # Set global Node.js version"
info "  pnpm --version           # Check pnpm version"
info "  node --version            # Check Node.js version"
