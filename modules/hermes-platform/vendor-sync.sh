#!/usr/bin/env bash
# hermes-platform vendor sync: keep vendor/ a faithful copy of the lab's local-patches ledger and the patch files
# it names, so CI (and any machine without the lab repo) can restore the patched install from this repo alone.
#
#   vendor-sync.sh [--check] [LAB_REPO]
#
#   (default)  copy LAB_REPO/ledger/local-patches.jsonl to vendor/ledger/ and, for every ledger row that is not
#              retired, its patch_file to vendor/<patch_file> (same relative path, so the ledger needs no edit);
#              drop vendored patch files no live row names.
#   --check    change nothing; exit 1 when vendor/ differs from the lab (or the lab no longer has a patch file).
#   LAB_REPO   default $HERMES_PLATFORM_LAB, else ~/src/hyp-hermes
#
# Sync rule: run this whenever the lab's ledger changes (a patch added, retired or rebased onto a new pin), and commit
# the result together with the pin.txt bump if there is one. check.sh --dry-run and the CI job both read vendor/,
# so a stale copy shows up as a red CI run, not as a silently unpatched install.
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
CHECK=0
LAB=${HERMES_PLATFORM_LAB:-$HOME/src/hyp-hermes}
for a in "$@"; do
    case "$a" in
        --check) CHECK=1 ;;
        -h|--help) sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        -*) echo "unknown option: $a" >&2; exit 2 ;;
        *) LAB=$a ;;
    esac
done
command -v jq >/dev/null 2>&1 || { echo "vendor-sync: jq not found" >&2; exit 2; }
SRC="$LAB/ledger/local-patches.jsonl"
DST="$HERE/vendor"
[ -f "$SRC" ] || { echo "vendor-sync: no ledger at $SRC" >&2; exit 2; }

drift=0
note() { printf '%s\n' "$*"; }
sync_file() { # src dst-relative-to-vendor
    local s=$1 d="$DST/$2"
    if [ ! -f "$s" ]; then note "MISSING in the lab: $s"; drift=1; return; fi
    if [ -f "$d" ] && cmp -s "$s" "$d"; then note "same     $2"; return; fi
    drift=1
    if [ "$CHECK" = 1 ]; then note "DIFFERS  $2"; return; fi
    mkdir -p "$(dirname "$d")" && cp "$s" "$d" && note "copied   $2"
}

sync_file "$SRC" ledger/local-patches.jsonl
live=$(jq -r 'select(.status != "retired") | .patch_file' "$SRC") || { echo "vendor-sync: ledger is not valid JSON lines" >&2; exit 2; }
for pf in $live; do sync_file "$LAB/$pf" "$pf"; done

# vendored patch files that no live ledger row names are stale
if [ -d "$DST/experiments" ] || [ -d "$DST" ]; then
    while IFS= read -r f; do
        rel=${f#"$DST/"}
        case "$rel" in ledger/*) continue ;; esac
        printf '%s\n' "$live" | grep -qxF "$rel" && continue
        drift=1
        if [ "$CHECK" = 1 ]; then note "STALE    $rel"; else rm -f "$f" && note "removed  $rel"; fi
    done < <(find "$DST" -type f -name '*.patch')
fi
[ "$CHECK" = 1 ] && { [ "$drift" = 0 ] && note "vendor/ matches the lab" || note "vendor/ is out of sync with the lab"; exit "$drift"; }
exit 0
