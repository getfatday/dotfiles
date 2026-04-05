# Workmux module contribution to Zsh configuration
# This file will be merged with the main .zshrc file

# Workmux completions (compinit handled by Prezto completion module)
fpath=(${XDG_CONFIG_HOME:-$HOME/.config}/zsh/completions $fpath)
