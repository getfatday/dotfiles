# Git module contribution to Zsh configuration
# This file will be merged with the main .zshrc file

# Git aliases and functions from legacy configuration
alias gdt="git difftool"
alias gR="gf && gwR @{u}"
alias gtool="git mergetool"
alias gro='export GIT_ONTO=$(git rev-parse --abbrev-ref HEAD); git rebase --onto'
alias gpr="git open"
alias gpfu="gpf -u"
alias gre="git recent -n 5"
alias grel="git recent"
alias gqf='git add . && git fixup && GIT_SEQUENCE_EDITOR=: gri --autosquash HEAD~2'
alias gqfu='gqf && gpfu'

# GitHub CLI aliases
alias ib="gh issue create -l bug"
alias ic="gh issue create"
alias ie="gh issue create -l enhancement"
alias il="gh issue list"
alias io="gh issue list --web"
alias iq="gh issue create -l question"

# Git functions
git_recent() {
    git recent -n 5
}

git_recent_long() {
    git recent
}

git_quick_fix() {
    git add . && git fixup && GIT_SEQUENCE_EDITOR=: gri --autosquash HEAD~2
}

git_quick_fix_upstream() {
    git_quick_fix && gpfu
}
