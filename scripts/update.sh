#!/usr/bin/env bash
# update.sh — refresh starter-kit skills/recipes against the current ref.
# Thin wrapper around `install.sh --update`. Provider/connector prompts
# are skipped; user-modified files are preserved.

set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/install.sh" --update "$@"
