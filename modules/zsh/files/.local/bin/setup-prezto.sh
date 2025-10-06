#!/bin/bash

# Prezto setup script for Zsh module
# This script installs and configures Prezto framework

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

# Check if zsh is installed
if ! command -v zsh &> /dev/null; then
    error "Zsh is not installed. Please install zsh first."
fi

# Set Prezto directory
PREZTO_DIR="$HOME/.zprezto"

info "Setting up Prezto framework..."

# Clone Prezto if it doesn't exist
if [ ! -d "$PREZTO_DIR" ]; then
    info "Cloning Prezto repository..."
    git clone --recursive https://github.com/sorin-ionescu/prezto.git "$PREZTO_DIR"
    success "Prezto cloned successfully"
else
    info "Prezto already exists, updating..."
    cd "$PREZTO_DIR"
    git pull && git submodule update --init --recursive
    success "Prezto updated successfully"
fi

# Create symlinks for Prezto configuration files
info "Creating Prezto configuration symlinks..."

# Backup existing files if they exist
for rcfile in "${PREZTO_DIR}"/runcoms/z*; do
    if [ -f "$rcfile" ]; then
        filename=$(basename "$rcfile")
        if [ -f "$HOME/.${filename}" ] && [ ! -L "$HOME/.${filename}" ]; then
            warn "Backing up existing ~/.${filename} to ~/.${filename}.backup"
            mv "$HOME/.${filename}" "$HOME/.${filename}.backup"
        fi
        if [ ! -L "$HOME/.${filename}" ]; then
            ln -s "$rcfile" "$HOME/.${filename}"
            success "Linked ~/.${filename}"
        fi
    fi
done

# Set zsh as default shell if not already
if [ "$SHELL" != "/bin/zsh" ] && [ "$SHELL" != "/usr/bin/zsh" ]; then
    info "Setting zsh as default shell..."
    if command -v chsh &> /dev/null; then
        chsh -s /bin/zsh
        success "Zsh set as default shell (restart terminal to take effect)"
    else
        warn "Could not change shell automatically. Please run: chsh -s /bin/zsh"
    fi
fi

success "Prezto setup complete!"
info "Restart your terminal or run 'exec zsh' to start using Prezto"
