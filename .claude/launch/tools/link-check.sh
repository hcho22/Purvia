#!/usr/bin/env bash
# Link-check for the launch package.
# 1) Every local href/src in the given HTML files resolves on disk (relative to the file).
# 2) Every repo path cited in launch/evidence/claims.md (backtick-quoted, path-shaped) exists.
# Exit 0 = all resolve; 1 = failures listed.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"   # repo root
fail=0

echo "== HTML local links =="
for f in "$@"; do
  dir=$(dirname "$f")
  # extract href/src values, skip http(s), mailto, #, data:
  for link in $(grep -oE '(href|src)="[^"]+"' "$f" | sed -E 's/^(href|src)="//; s/"$//' | grep -vE '^(https?:|mailto:|#|data:)'); do
    path="${link%%#*}"
    [ -z "$path" ] && continue
    if [ ! -e "$dir/$path" ]; then
      echo "MISSING: $f -> $link"
      fail=1
    fi
  done
done

echo "== claims.md repo paths =="
# backtick-quoted tokens that look like repo paths (contain / and an extension or end with /)
# Paths the ledger cites BECAUSE they are absent (J6 documents the missing weekly history).
DOCUMENTED_ABSENT="docs/escalation-weekly/"
grep -oE '`[A-Za-z0-9_./-]+`' "$ROOT/launch/evidence/claims.md" | tr -d '`' | sort -u | while read -r p; do
  case "$p" in
    */*) ;;
    *) continue ;;
  esac
  case " $DOCUMENTED_ABSENT " in *" $p "*) continue ;; esac
  # strip :line suffixes
  base="${p%%:*}"
  if [ ! -e "$ROOT/$base" ]; then
    echo "MISSING claims path: $p"
    echo "$p" >> /tmp/claims-missing.txt
  fi
done
if [ -s /tmp/claims-missing.txt ] 2>/dev/null; then fail=1; rm -f /tmp/claims-missing.txt; fi

[ $fail -eq 0 ] && echo "ALL LINKS RESOLVE"
exit $fail
