---
description: Analyze drift and suggest module organization
---

Run a comprehensive drift analysis and provide AI-assisted recommendations.

1. Run `dotm analyze --all` to detect unmanaged packages, casks, MAS apps, and orphan dotfiles

2. For each category of unmanaged items, suggest:
   - Which existing module they might belong to (read existing module configs to check)
   - Which items should be grouped into new modules (group by purpose/category)
   - Suggested module names for new groups
   - Which items can be safely ignored (system dependencies, transitive deps)

3. For each suggested new module, provide the config.yml content that would be needed

4. Prioritize recommendations:
   - High: Frequently used tools that should be reproducible
   - Medium: Nice-to-have tools
   - Low: System dependencies or rarely used utilities

Present results as actionable recommendations the user can approve or reject.
