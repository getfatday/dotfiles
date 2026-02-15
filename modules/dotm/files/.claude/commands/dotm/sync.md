---
description: Sync dotfiles with AI monitoring
---

Run a dotfiles sync with monitoring and reporting.

1. Run `dotm sync` to pull latest changes and apply modules

2. Check the results:
   - Run `git -C ~/src/dotfiles log --oneline -5` to see what changed
   - Run `dotm verify` to confirm everything is correct

3. Report:
   - What commits were pulled (if any)
   - Whether the apply succeeded
   - Any verification failures after sync
   - Any issues that need attention

If the sync fails, investigate and suggest fixes.
