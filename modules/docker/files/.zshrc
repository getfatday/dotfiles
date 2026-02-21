# Docker module contribution to Zsh configuration
# This file will be merged with the main .zshrc file

# Docker machine aliases
alias dm='docker-machine'
alias dme='function () { e="$(docker-machine env ${1-default})"; echo $e; eval $e }'
alias dms='function () { docker-machine start ${1-default} }'
alias dmh='function () { docker-machine stop ${1-default} }'
alias dmr='function () { docker-machine restart ${1-default} }'
alias dmk='function () { docker-machine kill ${1-default} }'

# Docker build and push aliases
alias db='docker build'
alias dp='docker push'

# Docker CLI completions (compinit handled by Prezto completion module)
fpath=(/Users/ianderson/.docker/completions $fpath)
