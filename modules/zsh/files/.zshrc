# Productivity module contribution to Zsh configuration
# This file will be merged with the main .zshrc file

# Auto jump Commands
export AUTOJUMP_AUTOCOMPLETE_CMDS='e en cat less vi open'

# Z directory navigation
if command -v brew >/dev/null 2>&1 && (( $+commands[brew] )) ; then
    if [[ -f `brew --prefix`/etc/profile.d/z.sh ]]; then
        . `brew --prefix`/etc/profile.d/z.sh
    fi
fi

# Autojump integration
if (( $+commands["brew"] )) ; then
    [[ -s `brew --prefix`/etc/autojump.sh ]] && . `brew --prefix`/etc/autojump.sh
fi

# Productivity aliases
alias f="find . -name"
alias jc="j --complete"
alias jw="jump-window"
alias reload="source ~/.zshrc"
alias fs="foreman start"

# Caffeinate for keeping system awake
alias wtfu="caffeinate -idm"

# Redact Shell History function
redact () {
  if [ -z "$@" ]; then
    echo "Missing statement to redact" 1>&2
    return;
  fi
  LC_ALL=C sed -i '' '/'$@'/d' $HISTFILE;
  fc -R;
  clear;
}
