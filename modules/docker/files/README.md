# Docker Module

This module provides a complete Docker development environment with management tools and CLI completions.

## Features

- **Docker Development Environment** - Complete Docker toolchain
- **Docker Machine Management** - Easy machine lifecycle management
- **Docker CLI Completions** - Enhanced command completion
- **Docker Aliases** - Productivity shortcuts for common operations

## What Gets Installed

### Homebrew Packages
- `docker` - Docker container runtime
- `docker-compose` - Multi-container Docker applications
- `docker-machine` - Docker machine management

### Configuration Files
- `.local/bin/docker-*` - Custom Docker utilities (if any)
- `.zshrc` - Docker aliases and completions (merged)

## Docker Aliases

### Docker Machine Management
- `dm` - docker-machine
- `dme` - Set up docker-machine environment
- `dms` - Start docker-machine
- `dmh` - Stop docker-machine
- `dmr` - Restart docker-machine
- `dmk` - Kill docker-machine

### Docker Operations
- `db` - docker build
- `dp` - docker push

## Usage

### Basic Docker Operations
```bash
# Build and run containers
db -t myapp .
docker run -p 3000:3000 myapp

# Push to registry
dp myapp:latest
```

### Docker Machine Workflow
```bash
# Start and configure machine
dms default
dme default

# Build and run
db -t myapp .
docker run myapp
```

## Configuration

The module automatically configures:
- Docker CLI completions
- Docker machine aliases
- Docker build/push shortcuts
- Environment setup for Docker development

## Learn More

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Docker Machine](https://docs.docker.com/machine/)
