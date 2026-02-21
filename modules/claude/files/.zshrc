# Claude module contribution to Zsh configuration
# This file will be merged with the main .zshrc file

# Claude Code aliases
alias yolo='claude --dangerously-skip-permissions'

# Claude Squad completions
if command -v claude-squad >/dev/null 2>&1; then
  eval "$(claude-squad completion zsh)" 2>/dev/null
fi

# Remote session management
alias ccr='cc-remote'
