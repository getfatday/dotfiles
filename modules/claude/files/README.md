# Claude Module

This module provides the [Claude desktop application](https://apps.apple.com/us/app/claude/id6734057884) for AI-powered conversations and assistance.

## Features

- **AI Conversations** - Natural language interactions with Claude models
- **Code Generation** - Generate, debug, and explain code
- **Content Creation** - Writing, editing, and brainstorming assistance
- **Research Help** - Information gathering and analysis
- **Learning Support** - Explanations, tutorials, and Q&A

## What Gets Installed

### Configuration Files
- `.config/claude/` - Configuration and settings

### Platform Support
- **Apple Silicon (ARM64)**: Desktop app available via Homebrew Cask
- **Intel Macs (x86_64)**: Use web version at https://claude.ai/

### Installation Notes
- Requires native ARM64 Homebrew (`/opt/homebrew/bin/brew`)
- Install with: `arch -arm64 /opt/homebrew/bin/brew install --cask claude`

## Usage

### Basic Commands
```bash
# Open Claude
open -a Claude

# Launch from command line
open -a "Claude"
```

### Features
- **Desktop App** - Native macOS application
- **Conversation History** - Persistent chat history
- **File Uploads** - Upload documents, images, and code
- **Code Execution** - Run and test code snippets
- **Custom Instructions** - Personalized AI behavior
- **Safety-First Design** - Built with AI safety principles

## Integration

### With Development Tools
- **Cursor** - AI-powered code editor
- **VS Code** - Code generation and debugging
- **Terminal** - Command line assistance

### With Productivity Apps
- **Obsidian** - Note-taking and knowledge management
- **Alfred** - Quick access and workflows
- **iTerm2** - Terminal integration

## Configuration

### Settings Location
- Application preferences (accessible through the app)
- User data directory (managed by the app)

### Customization
- **Model Selection** - Choose between Claude models
- **Custom Instructions** - Set up personalized AI behavior
- **Conversation Settings** - Manage chat history and preferences
- **Safety Settings** - Configure AI safety parameters

## Learn More

- [Claude Website](https://claude.ai/)
- [Anthropic Documentation](https://docs.anthropic.com/)
- [Claude Desktop App](https://apps.apple.com/us/app/claude/id6734057884)
