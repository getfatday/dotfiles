# Rust module contribution to Zsh environment
# This file will be merged with the main .zshenv file

# Source Cargo environment (adds ~/.cargo/bin to PATH)
[[ -f "$HOME/.cargo/env" ]] && . "$HOME/.cargo/env"
