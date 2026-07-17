#!/usr/bin/env bash
# Purvia voice linter (mission brief §4). A hit is a failure, not a suggestion.
# Usage: voice-lint.sh FILE [FILE...]
# Exit 0 = clean, 1 = violations found.
# Verbatim third-party quotes (evidence files) are out of scope by convention; lint deliverables.

set -u
fail=0

# Banned vocabulary and cadence tics. Word-boundary, case-insensitive.
WORDS='revolutioniz|revolutionis|unlock|supercharge|seamless|effortless|game.changing|cutting.edge|\brobust\b|\bpowerful\b|blazing.fast|next.generation|next-gen\b'
CADENCE="Here's the thing|Here is the thing|Let that sink in"

# Lines containing the literal marker "voice-lint:allow" are exempt (used for the
# ban-list line in GUIDELINES.md, which necessarily names the banned words).
filter_allow() { grep -v 'voice-lint:allow' || true; }

for f in "$@"; do
  [ -f "$f" ] || { echo "SKIP (not a file): $f"; continue; }
  hits=""

  h=$(grep -inE "$WORDS" "$f" | filter_allow)
  [ -n "$h" ] && hits="$hits
BANNED WORD:
$h"

  h=$(grep -inE "$CADENCE" "$f" | filter_allow)
  [ -n "$h" ] && hits="$hits
BANNED CADENCE:
$h"

  # em dash (U+2014)
  h=$(grep -in $'—' "$f" | filter_allow)
  [ -n "$h" ] && hits="$hits
EM DASH:
$h"

  # exclamation marks in prose (!=, ![, !(, <!DOCTYPE, and <!-- comments are excluded; review remaining hits manually)
  h=$(grep -n '![^=[(]' "$f" | grep -vE '<!DOCTYPE|<!--' | filter_allow)
  [ -n "$h" ] && hits="$hits
EXCLAMATION (review; != and ![ are excluded):
$h"

  # "agentic" - REPORT ONLY, never a failure: allowed as architecture description
  # or in the technical namespace (agentic-rag); banned only as a value claim.
  w=$(grep -inE '\bagentic\b' "$f" | filter_allow)
  [ -n "$w" ] && echo "note ($f) AGENTIC mentions for manual review:
$w"

  if [ -n "$hits" ]; then
    echo "== FAIL: $f$hits"
    echo
    fail=1
  else
    echo "OK: $f"
  fi
done
exit $fail
