#!/bin/bash

# Emacs with Prelude setup script
# This script installs and configures Emacs with Prelude framework

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

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Check if emacs is installed
if ! command -v emacs &> /dev/null; then
    error "Emacs is not installed. Please install emacs first."
fi

# Set Emacs directory
EMACS_DIR="$HOME/.emacs.d"

info "Setting up Emacs with Prelude framework..."

# Backup existing .emacs.d if it exists
if [ -d "$EMACS_DIR" ] && [ ! -L "$EMACS_DIR" ]; then
    warn "Backing up existing .emacs.d to .emacs.d.backup"
    mv "$EMACS_DIR" "$EMACS_DIR.backup"
fi

# Clone Prelude if it doesn't exist
if [ ! -d "$EMACS_DIR" ]; then
    info "Cloning Prelude repository..."
    git clone --depth 1 https://github.com/bbatsov/prelude.git "$EMACS_DIR"
    success "Prelude cloned successfully"
else
    info "Prelude already exists, updating..."
    cd "$EMACS_DIR"
    git pull
    success "Prelude updated successfully"
fi

# Create personal directory if it doesn't exist
if [ ! -d "$EMACS_DIR/personal" ]; then
    info "Creating personal configuration directory..."
    mkdir -p "$EMACS_DIR/personal"
    success "Personal directory created"
fi

# Copy personal configuration files
info "Copying personal configuration files..."

# Copy prelude-modules.el
if [ -f "$HOME/.emacs.d/personal/prelude-modules.el" ]; then
    success "prelude-modules.el already exists"
else
    cp "$HOME/.emacs.d/samples/prelude-modules.el" "$HOME/.emacs.d/personal/"
    success "prelude-modules.el copied"
fi

# Copy custom.el
if [ -f "$HOME/.emacs.d/personal/custom.el" ]; then
    success "custom.el already exists"
else
    cp "$HOME/.emacs.d/samples/custom.el" "$HOME/.emacs.d/personal/"
    success "custom.el copied"
fi

# Create preload directory
mkdir -p "$HOME/.emacs.d/personal/preload"

success "Emacs with Prelude setup complete!"
info "Your personal configuration is located in ~/.emacs.d/personal/"
info "Start Emacs to begin using your new configuration"
