# worktree-noindex

Keeps Spotlight (`mds_stores`) out of the directories that churn constantly. On 2026-10-18 `mds_stores`
ran at 110-135% CPU for 2 d 15 h re-indexing every merge-gate scratch clone and every card worktree, and
the lander's load gate queued merges and aborted two on `HOST_STALL` (card t_c2bf9cee, fitness F-HOST-2).

`noindex.sh` creates an empty `.metadata_never_index` in each existing:

- `~/src/*/.worktrees`, `~/src/*__worktrees`, `~/src/*/.claude/worktrees`
- `$TMPDIR`, `~/.hermes/profiles/*/cache/scratch`, and the per-user temp dir `/private/var/folders/*/*/T`

It runs from the `post_tasks` block of `playbooks/deploy.yml` on every `dotm sync`. It never creates the
directories, never deletes anything, never runs `mdutil` (that needs admin), and an existing marker is left
alone. A worktree parent created after a sync is marked at the next one. The merge gate itself also marks
its own scratch dir (hyp-hermes `tools/merge/merge_done.sh`).

```
bash modules/worktree-noindex/check.sh          # read-only; exit 0 when every such dir has the marker
bash modules/worktree-noindex/noindex.sh        # apply now, without waiting for dotm sync
```

Tests: `modules/dotm/src/tests/test_worktree_noindex.py` (fixture HOME, never the real `~/src`).

Revert: delete the `.metadata_never_index` files
(`find ~/src -maxdepth 4 -name .metadata_never_index -path '*worktrees*' -delete`) and remove
`worktree-noindex` from `base_modules` in `playbooks/profiles.yml`.

Caveat: `.metadata_never_index` is long established on volume roots; whether Spotlight honours it on a plain
directory is not something Apple guarantees. Validate with the live measure, not the marker: `top -l 1 -stats pid,command,cpu | grep mds_stores`
under 20% for an hour while cards run. If it stays high, the fallback is the `.noindex` directory-name
suffix or a Spotlight Privacy exclusion (System Settings; needs the owner).
