#!/usr/bin/env bash
# Put an empty .metadata_never_index in every git-worktree parent dir and scratch root so Spotlight
# (mds_stores) stops indexing them. See config.yml in this directory.
#
#   noindex.sh            create missing markers; prints `worktree-noindex: dirs=N created=M missing=K`
#   noindex.sh --check    create nothing; exit 1 when any directory lacks the marker
#
# Never creates the directories themselves, never deletes anything, never runs mdutil.
set -u

mode=apply
case "${1:-}" in
    "") ;;
    --check) mode=check ;;
    -h|--help) sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
esac

SRC=${NOINDEX_SRC_ROOT:-$HOME/src}
PROFILES=${NOINDEX_PROFILES_DIR:-$HOME/.hermes/profiles}

targets=()
add() { if [ -d "$1" ] && [ -w "$1" ]; then targets+=("$1"); fi; return 0; }

shopt -s nullglob
for d in "$SRC"/*/.worktrees "$SRC"/*__worktrees "$SRC"/*/.claude/worktrees; do add "$d"; done
for d in "$PROFILES"/*/cache/scratch; do add "$d"; done

if [ -n "${NOINDEX_TMP_ROOTS:-}" ]; then
    IFS=: read -r -a roots <<<"$NOINDEX_TMP_ROOTS"
    for d in "${roots[@]}"; do add "${d%/}"; done
else
    if [ -n "${TMPDIR:-}" ]; then add "${TMPDIR%/}"; fi
    # The per-user temp dir: only our own (owner check), never another user's.
    for d in /private/var/folders/*/*/T; do
        if [ -O "$d" ]; then add "$d"; fi
    done
fi
shopt -u nullglob

dirs=0 created=0 missing=0
seen=$'\n'
for d in "${targets[@]+"${targets[@]}"}"; do
    real=$(cd "$d" 2>/dev/null && pwd -P) || continue
    case "$seen" in *$'\n'"$real"$'\n'*) continue ;; esac
    seen+="$real"$'\n'
    dirs=$((dirs + 1))
    marker="$real/.metadata_never_index"
    [ -e "$marker" ] && continue
    if [ "$mode" = check ]; then
        echo "MISSING $marker"
        missing=$((missing + 1))
    elif : >"$marker" 2>/dev/null; then
        echo "created $marker"
        created=$((created + 1))
    else
        echo "FAILED  $marker" >&2
        missing=$((missing + 1))
    fi
done

echo "worktree-noindex: dirs=$dirs created=$created missing=$missing"
[ "$missing" -eq 0 ]
