# Productivity module contribution to Zsh configuration
# This file will be merged with the main .zshrc file

# Productivity aliases
alias f="find . -name"
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
