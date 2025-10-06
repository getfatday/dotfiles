# Node.js Development Module

This module provides a complete Node.js development environment using `asdf` for version management and `pnpm` for package management.

## Features

- **asdf version manager** - Manage multiple Node.js versions
- **pnpm package manager** - Fast, disk space efficient package manager
- **Global development tools** - TypeScript, ESLint, Prettier, etc.
- **Automatic setup** - One-command environment setup

## What Gets Installed

### Homebrew Packages
- `asdf` - Version manager for multiple languages
- `node` - Node.js (fallback)
- `pnpm` - Fast package manager

### Configuration Files
- `.tool-versions` - asdf tool versions (Node.js 20.11.0)
- `.asdfrc` - asdf configuration
- `.npmrc` - npm configuration for pnpm
- `.config/pnpm/config.yml` - pnpm configuration

### Setup Script
- `.local/bin/setup-node.sh` - Automated setup script

## Usage

### Manual Setup
1. Install asdf: `brew install asdf`
2. Add to shell: `echo '. $(brew --prefix asdf)/libexec/asdf.sh' >> ~/.zshrc`
3. Install Node.js plugin: `asdf plugin add nodejs https://github.com/asdf-vm/asdf-nodejs.git`
4. Install Node.js: `asdf install`
5. Install pnpm: `npm install -g pnpm`

### Automated Setup
Run the setup script after deployment:
```bash
~/.local/bin/setup-node.sh
```

## Commands

### asdf Commands
```bash
asdf list nodejs                    # List installed Node.js versions
asdf install nodejs 20.11.0        # Install specific Node.js version
asdf global nodejs 20.11.0          # Set global Node.js version
asdf local nodejs 18.19.0           # Set local Node.js version
```

### pnpm Commands
```bash
pnpm --version                      # Check pnpm version
pnpm add <package>                  # Add package
pnpm add -D <package>               # Add dev dependency
pnpm install                       # Install dependencies
pnpm run <script>                  # Run script
```

### Node.js Commands
```bash
node --version                      # Check Node.js version
npm --version                       # Check npm version
```

## Configuration

### .tool-versions
Specifies which Node.js version to use:
```
nodejs 20.11.0
```

### .npmrc
Configures npm to use pnpm:
```
package-manager=pnpm
save-exact=true
auto-install-peers=true
```

### pnpm config
Located at `~/.config/pnpm/config.yml`:
- Store directory: `~/.local/share/pnpm`
- Global bin directory: `~/.local/bin`
- Auto install peer dependencies: `true`

## Global Packages

The setup script installs these global packages:
- `typescript` - TypeScript compiler
- `ts-node` - TypeScript execution
- `nodemon` - Development server
- `eslint` - JavaScript linter
- `prettier` - Code formatter

## Troubleshooting

### asdf not found
Add to your shell configuration:
```bash
echo '. $(brew --prefix asdf)/libexec/asdf.sh' >> ~/.zshrc
source ~/.zshrc
```

### Node.js version not found
Install the version:
```bash
asdf install nodejs 20.11.0
```

### pnpm not found
Install globally:
```bash
npm install -g pnpm
```

## Learn More

- [asdf Documentation](https://asdf-vm.com/guide/getting-started.html)
- [pnpm Documentation](https://pnpm.io/)
- [Node.js Documentation](https://nodejs.org/docs/)
