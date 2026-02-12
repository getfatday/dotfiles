# Node module contribution to Zsh configuration
# This file will be merged with the main .zshrc file

# pnpm configuration
export PNPM_HOME="$HOME/Library/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac

# ASDF integration (cross-architecture)
if command -v brew >/dev/null 2>&1; then
  _asdf_sh="$(brew --prefix)/opt/asdf/libexec/asdf.sh"
  if [[ -f "$_asdf_sh" ]]; then
    . "$_asdf_sh"
  fi
  unset _asdf_sh
fi

# ASDF direnv integration
if [[ -f "${XDG_CONFIG_HOME:-$HOME/.config}/asdf-direnv/zshrc" ]]; then
  source "${XDG_CONFIG_HOME:-$HOME/.config}/asdf-direnv/zshrc"
fi
