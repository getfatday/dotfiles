# Claude Squad completions
if command -v claude-squad >/dev/null 2>&1; then
  eval "$(claude-squad completion zsh 2>/dev/null)"
fi

# Remote session management
alias ccr='cc-remote'
