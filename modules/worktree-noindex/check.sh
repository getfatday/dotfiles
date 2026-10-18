#!/usr/bin/env bash
# worktree-noindex check: read-only. Exit 0 when every worktree parent dir and scratch root that
# exists carries .metadata_never_index; exit 1 and list the ones that do not.
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/noindex.sh" --check
