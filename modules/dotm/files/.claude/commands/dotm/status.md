---
description: Show dotfiles system status with AI interpretation
---

Run the dotm status and analyze commands, then provide a summary of what needs attention.

1. Run `dotm status` to get the system overview
2. Run `dotm analyze --all` to detect drift
3. Run `dotm verify` to check installed modules

Summarize the results:
- How many modules are installed vs available
- Any modules that are excluded
- Any unmanaged brew packages, casks, or MAS apps (drift)
- Any verification failures
- Recommendations for what to address first

Format the output clearly with sections. Flag anything that needs immediate attention.
