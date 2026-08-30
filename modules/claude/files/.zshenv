# Claude module contribution to Zsh environment
# This file will be merged with the main .zshenv file

# Machine-local Claude agent secrets (CLAUDE_CODE_OAUTH_TOKEN for headless
# launchd/SSH sessions — see vault research/mini-agent-host-baseline.md).
# The env file lives outside the repo and is never committed.
[ -f "$HOME/.config/claude-agent/env.zsh" ] && source "$HOME/.config/claude-agent/env.zsh"
