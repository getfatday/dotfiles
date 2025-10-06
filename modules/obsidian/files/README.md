# Obsidian Module

This module provides [Obsidian](https://obsidian.md), the powerful note-taking and knowledge management app, along with the [Obsidian Web Clipper](https://apps.apple.com/us/app/obsidian-web-clipper/id6720708363) for saving web content to your personal knowledge base.

## Features

- **Obsidian application** - Note-taking and knowledge management
- **Web Clipper** - Save web content to your vault
- **Custom templates** - Structured note templates for different content types
- **CSS snippets** - Custom styling and themes
- **Vault management** - Tools for creating and managing vaults
- **Knowledge workflows** - Templates for organizing information

## What Gets Installed

### Homebrew Casks
- `obsidian` - Note-taking and knowledge management app

### Mac App Store Apps
- **Obsidian Web Clipper** (ID: 6720708363) - Save web content to your vault

### Configuration Files
- `.config/obsidian/templates/` - Note templates
- `.config/obsidian/snippets/` - CSS styling snippets
- `.config/obsidian/plugins/` - Plugin configurations

## Templates

### Daily Note Template
- **Purpose**: Daily planning and reflection
- **Features**: Focus areas, tasks, meetings, ideas, reflection
- **Usage**: Perfect for daily journaling and planning

### Meeting Note Template
- **Purpose**: Structured meeting documentation
- **Features**: Agenda, discussion points, decisions, action items
- **Usage**: Capture meeting outcomes and follow-ups

### Web Clip Template
- **Purpose**: Save and organize web content
- **Features**: Source tracking, key points, personal notes, related links
- **Usage**: Perfect for research and content curation

### Project Note Template
- **Purpose**: Project management and tracking
- **Features**: Status tracking, goals, tasks, resources, progress
- **Usage**: Organize and track project work

## Usage

### Basic Commands
```bash
obsidian                    # Open Obsidian
obsidian-vault new "My Vault"  # Create new vault
obsidian-vault open ~/Documents/Obsidian/MyVault  # Open existing vault
obsidian-vault list        # List available vaults
```

### Template Management
```bash
obsidian-templates ~/Documents/Obsidian/MyVault  # Install templates to vault
```

### Setup Script
```bash
~/.config/obsidian/scripts/setup-obsidian.sh
```

## Web Clipper Integration

### Features
- **Clip anything** - Articles, recipes, product pages, research papers
- **Smart extraction** - Automatically extract main content
- **Custom templates** - Structured templates for different content types
- **Smart triggers** - Auto-apply templates based on website
- **Privacy focused** - All content stored locally in your vault

### Setup
1. Install the Web Clipper from Mac App Store
2. Configure it to work with your Obsidian vault
3. Use the web-clip template for consistent formatting
4. Set up smart triggers for automatic template selection

## Knowledge Management Workflows

### Daily Workflow
1. **Morning**: Create daily note with focus areas
2. **Throughout day**: Capture ideas, tasks, and web content
3. **Evening**: Review and reflect on the day

### Research Workflow
1. **Web clipping**: Save articles and resources with templates
2. **Note linking**: Connect related ideas and concepts
3. **Synthesis**: Create summary notes and insights

### Project Workflow
1. **Project setup**: Create project note with goals and tasks
2. **Progress tracking**: Update status and milestones
3. **Resource management**: Link to relevant documents and notes

## Configuration

### Vault Structure
```
MyVault/
├── .obsidian/
│   ├── templates/          # Note templates
│   ├── snippets/           # CSS styling
│   └── plugins/            # Plugin configurations
├── Daily Notes/           # Daily planning
├── Projects/              # Project management
├── Resources/             # Web clips and references
└── Archive/               # Completed items
```

### Templates
- **Daily Note** - `daily-note.md`
- **Meeting Note** - `meeting-note.md`
- **Web Clip** - `web-clip.md`
- **Project Note** - `project-note.md`

### CSS Snippets
- **Custom callouts** - Important, tip, warning styles
- **Web clip styling** - Consistent formatting for web content
- **Task styling** - Enhanced task list appearance
- **Link styling** - Improved internal link appearance

## Advanced Features

### Vault Management
```bash
# Create new vault
obsidian-vault new "Research Vault" ~/Documents/Obsidian/Research

# Open existing vault
obsidian-vault open ~/Documents/Obsidian/Personal

# List all vaults
obsidian-vault list
```

### Template Installation
```bash
# Install templates to specific vault
obsidian-templates ~/Documents/Obsidian/MyVault
```

### Custom Styling
- Import CSS snippets for custom themes
- Create consistent visual styling
- Enhance readability and organization

## Integration

### With Other Tools
- **Alfred** - Quick vault access and note creation
- **iTerm2** - Terminal-based vault management
- **Git** - Version control for your knowledge base
- **Node.js** - Custom scripts and automation

### Web Clipper Workflow
1. **Browse web** - Find interesting content
2. **Clip content** - Use Web Clipper to save
3. **Auto-template** - Smart triggers apply appropriate template
4. **Organize** - Content flows into your vault structure
5. **Connect** - Link to related notes and ideas

## Troubleshooting

### Obsidian Not Opening
```bash
# Check if Obsidian is installed
ls -la /Applications/Obsidian.app

# Reinstall if needed
brew install --cask obsidian
```

### Web Clipper Not Working
1. Ensure Web Clipper is installed from Mac App Store
2. Check vault path configuration in Web Clipper settings
3. Verify vault is accessible and writable

### Templates Not Loading
```bash
# Check template directory
ls -la ~/.config/obsidian/templates/

# Reinstall templates
obsidian-templates <vault-path>
```

### Vault Access Issues
```bash
# Check vault permissions
ls -la ~/Documents/Obsidian/

# Create default vault if missing
mkdir -p ~/Documents/Obsidian/Personal
```

## Learn More

- [Obsidian Documentation](https://help.obsidian.md/)
- [Obsidian Community](https://forum.obsidian.md/)
- [Obsidian Plugins](https://obsidian.md/plugins)
- [Web Clipper Guide](https://help.obsidian.md/How+to/Add+content+to+Obsidian)
- [Knowledge Management Best Practices](https://obsidian.md/learn)
