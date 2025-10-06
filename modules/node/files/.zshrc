# Node module contribution to Zsh configuration
# This file will be merged with the main .zshrc file

# pnpm configuration
export PNPM_HOME="/Users/ianderson/Library/pnpm"
export PATH="/opt/homebrew/bin:`python3 -m site --user-base`/bin:$PNPM_HOME:$PATH"

# ASDF integration
if [ -f /opt/homebrew/opt/asdf/libexec/asdf.sh ]; then
  . /opt/homebrew/opt/asdf/libexec/asdf.sh
fi

# ASDF direnv integration
if [ -f "${XDG_CONFIG_HOME:-$HOME/.config}/asdf-direnv/zshrc" ]; then
  source "${XDG_CONFIG_HOME:-$HOME/.config}/asdf-direnv/zshrc"
fi
