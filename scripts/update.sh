#!/usr/bin/env bash
# update.sh — refresh starter-kit skills/recipes against the current ref.
# Thin wrapper around `install.sh`. Skips the Goose Desktop install step
# (already handled at first install); user-modified files are preserved.

set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/install.sh" --no-desktop --update "$@"
