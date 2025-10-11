# Spec-kit Module

This module provides [GitHub Spec Kit](https://github.com/github/spec-kit), a toolkit for Spec-Driven Development that helps build high-quality software faster by focusing on specifications rather than undifferentiated code.

## What is Spec-Driven Development?

Spec-Driven Development flips the traditional development process: **specifications become executable**, directly generating working implementations rather than just guiding them. This approach helps organizations focus on product scenarios while AI handles the implementation details.

## Features

- **Structured Workflow** - Clear phases from constitution to implementation
- **AI-Powered** - Works with Cursor, Claude Code, GitHub Copilot, and more
- **Quality First** - Built-in checklists, analysis, and validation
- **Template-Driven** - Consistent specifications and plans
- **Modular** - Support for multiple features and projects

## What Gets Installed

### Tools
- **UV** - Fast Python package installer and manager (via Homebrew)
- **Spec-kit CLI** - `specify` command for project management

### Cursor Integration
- **Custom Slash Commands** - 8 commands in `.cursor/commands/`
  - `/speckit.constitution` - Define project principles
  - `/speckit.specify` - Create feature specifications
  - `/speckit.clarify` - Interactive clarification workflow
  - `/speckit.plan` - Create technical implementation plans
  - `/speckit.tasks` - Break down into actionable tasks
  - `/speckit.implement` - Execute implementation
  - `/speckit.analyze` - Cross-artifact consistency analysis
  - `/speckit.checklist` - Quality validation checklists

### Project Structure
- `.specify/memory/` - Project constitution and memory
- `.specify/scripts/` - Helper scripts for workflow automation
- `.specify/templates/` - Templates for specs, plans, and tasks
- `.cursor/commands/` - Cursor slash command definitions

## Installation

### Initial Setup
The UV package manager is installed via Homebrew. After deployment, install the spec-kit CLI:

```bash
# Install spec-kit CLI tool
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# Verify installation
specify check
```

### Update Spec-kit
To get the latest version:

```bash
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git
```

## Usage

### Spec-Driven Development Workflow

The recommended workflow follows these phases:

#### 1. Establish Constitution
Define your project's governing principles:

```
/speckit.constitution Create principles focused on modularity, testing standards, 
Ansible best practices, and idempotent deployments
```

#### 2. Create Specification
Describe what you want to build (focus on WHAT and WHY, not HOW):

```
/speckit.specify Add a module for installing and configuring PostgreSQL with 
automated backups and performance monitoring
```

#### 3. Optional: Clarify Requirements
Ask structured questions to de-risk ambiguous areas:

```
/speckit.clarify
```

#### 4. Create Technical Plan
Provide tech stack and architecture decisions:

```
/speckit.plan Use Homebrew to install PostgreSQL 15, configure with Ansible 
templates, set up daily backups to S3, integrate with Datadog for monitoring
```

#### 5. Break Down into Tasks
Generate actionable task list:

```
/speckit.tasks
```

#### 6. Execute Implementation
Run the implementation based on the plan:

```
/speckit.implement
```

### Quality Enhancement Commands

#### Consistency Analysis
Check alignment across specifications, plans, and tasks:

```
/speckit.analyze
```

#### Quality Checklists
Validate requirements completeness and clarity:

```
/speckit.checklist
```

## CLI Commands

### Initialize New Projects
```bash
# Initialize in new directory
specify init my-project --ai cursor-agent

# Initialize in current directory
specify init --here --ai cursor-agent

# Force merge into existing directory
specify init --here --ai cursor-agent --force
```

### Check Installation
```bash
# Verify spec-kit and AI tools are installed
specify check
```

## Project Structure

After initialization, your project will have:

```
dotfiles/
├── .cursor/
│   └── commands/           # Cursor slash commands
│       ├── speckit.constitution.md
│       ├── speckit.specify.md
│       ├── speckit.clarify.md
│       ├── speckit.plan.md
│       ├── speckit.tasks.md
│       ├── speckit.implement.md
│       ├── speckit.analyze.md
│       └── speckit.checklist.md
├── .specify/
│   ├── memory/
│   │   └── constitution.md    # Project principles
│   ├── scripts/               # Helper automation scripts
│   │   └── bash/
│   └── templates/             # Reusable templates
└── specs/                     # Feature specifications (created as needed)
    └── 001-feature-name/
        ├── spec.md
        ├── plan.md
        ├── tasks.md
        └── research.md
```

## Integration

### With Dotfiles Workflow
Spec-kit helps you:
- **Document module purposes** - Clear specifications for each module
- **Plan configurations** - Structured approach to new modules
- **Track changes** - Constitution for dotfiles principles
- **Automate testing** - Tasks for validation and verification

### With Development Tools
- **Cursor** - Custom slash commands for AI-assisted development
- **Git** - Version-controlled specifications and plans
- **Ansible** - Structured planning for automation
- **GitHub** - Spec-driven pull requests and reviews

## Best Practices

### Constitution First
Always start by establishing your dotfiles constitution:
- Modularity principles
- Idempotency requirements
- Testing standards
- Documentation expectations
- Deployment policies

### Spec Before Code
For new modules:
1. Write specification
2. Get approval/clarification
3. Create technical plan
4. Break into tasks
5. Implement with AI

### Quality Gates
Use analysis and checklists to ensure:
- Specifications are complete
- Plans align with constitution
- Tasks cover all requirements
- Implementation matches spec

## Example: Adding a New Module

```bash
# 1. Define what you want
/speckit.specify Add a module for Visual Studio Code with extensions,
settings sync, and keybindings

# 2. Clarify details (optional)
/speckit.clarify

# 3. Plan the implementation
/speckit.plan Install VS Code via Homebrew Cask, use Stow for settings,
include extension list in config.yml, create setup script for extensions

# 4. Generate tasks
/speckit.tasks

# 5. Implement
/speckit.implement
```

## Configuration

### UV Tool Management
```bash
# List installed tools
uv tool list

# Upgrade spec-kit
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git

# Uninstall if needed
uv tool uninstall specify-cli
```

### Shell Integration
Add to your `.zshrc` or `.bashrc`:

```bash
# Add UV-installed tools to PATH
export PATH="$HOME/.local/bin:$PATH"
```

## Supported AI Agents

- ✅ Cursor (cursor-agent)
- ✅ Claude Code
- ✅ GitHub Copilot  
- ✅ Gemini CLI
- ✅ Qwen Code
- ✅ Windsurf
- ✅ And many more!

## Learn More

- [Spec-kit Documentation](https://github.github.io/spec-kit/)
- [GitHub Repository](https://github.com/github/spec-kit)
- [Quick Start Guide](https://github.github.io/spec-kit/quickstart.html)
- [Video Overview](https://www.youtube.com/watch?v=a9eR1xsfvHg)
- [Spec-Driven Development Guide](https://github.com/github/spec-kit/blob/main/spec-driven.md)

## Troubleshooting

### PATH Not Set
If `specify` command not found:

```bash
export PATH="$HOME/.local/bin:$PATH"
# Or permanently add to your shell config
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

### Update UV
```bash
brew upgrade uv
```

### Reinstall Spec-kit
```bash
uv tool uninstall specify-cli
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

## Notes

- Spec-kit is a Python CLI tool managed by UV
- Custom slash commands are automatically available in Cursor after initialization
- Templates and scripts are stored in `.specify/` directory
- Constitution and specifications are version-controlled
- Each feature gets its own directory under `specs/`

