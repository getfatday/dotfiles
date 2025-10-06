# Quick Start Guide

## Prerequisites

1. **macOS** (required for Homebrew integration)
2. **Ansible** 2.9+ installed
3. **GNU Stow** installed (`brew install stow`)
4. **Homebrew** installed

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/dotfiles.git
   cd dotfiles
   ```

2. **Install dependencies:**
   ```bash
   ansible-galaxy install -r requirements.yml
   ```

3. **Deploy dotfiles:**
   ```bash
   cd playbooks
   # Normal run (recommended)
   ansible-playbook -i inventory deploy.yml

   # If any tasks require privilege escalation (sudo)
   ansible-playbook -i inventory deploy.yml -K
   ```

## What Gets Installed

The deployment will install:

- **Shell tools**: zsh, bash, starship, fzf, bat, exa, ripgrep
- **Git tools**: git, git-delta, gh, git-flow  
- **Dev tools**: node, python, go, rust, jq, yq, httpie
- **Editors**: neovim, vim, emacs
- **Language tools**: pipenv, poetry, yarn, pnpm, goreleaser
- **Applications**: Visual Studio Code, iTerm2, Docker

## Customization

### Adding Modules

1. Create a new module directory:
   ```bash
   mkdir modules/my-module
   ```

2. Add configuration:
   ```bash
   # modules/my-module/config.yml
   homebrew_packages:
     - my-tool
   stow_dirs:
       - my-module
   ```

3. Add dotfiles:
   ```bash
   mkdir modules/my-module/files
   # Add your dotfiles here
   ```

4. Update the playbook:
   ```yaml
   install:
     - shell
     - git
     - my-module  # Add your module here
   ```

### Removing Modules

Simply remove the module from the `install` list in your playbook.

## Troubleshooting

### Check Mode
Run in check mode to see what would be installed:
```bash
ansible-playbook -i inventory deploy.yml --check
```

### Verbose Output
Get detailed output:
```bash
ansible-playbook -i inventory deploy.yml -v
```

### Common Issues

1. **Missing dependencies**: Install required Ansible roles
2. **Stow conflicts**: Check for existing dotfiles
3. **Homebrew issues**: Ensure Homebrew is working

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the `modules/` directory to see available configurations
- Customize modules to fit your needs
- Contribute back to the repository
