# Editor module contribution to Zsh configuration
# This file will be merged with the main .zshrc file

# Emacs configuration
em() {
    if [ -z "$@" ]; then
        emacsclient -nw $(pwd)
    else
        emacsclient -nw $@
    fi
}

# Emacs aliases
alias e='em'
alias eek='killall -USR2 emacs'
alias en="emacsclient -n"
alias er="emacs-restart"
alias ec="emacs-clean"

# Editor configuration
[[ $EMACS = t ]] && unsetopt zle
