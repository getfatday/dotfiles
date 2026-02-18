# Sesh module contribution to Zsh configuration

# Zoxide — smart cd (replaces z and autojump)
eval "$(zoxide init zsh)"

# Sesh session picker (Alt-s in any terminal)
function sesh-sessions() {
  {
    exec </dev/tty
    exec <&1
    local session
    session=$(sesh list -t -c | fzf --height 40% --reverse \
      --border-label ' sesh ' --border --prompt '⚡ ')
    zle reset-prompt > /dev/null 2>&1 || true
    [[ -z "$session" ]] && return
    sesh connect $session
  }
}
zle -N sesh-sessions
bindkey -M emacs '\es' sesh-sessions
bindkey -M vicmd '\es' sesh-sessions
bindkey -M viins '\es' sesh-sessions
