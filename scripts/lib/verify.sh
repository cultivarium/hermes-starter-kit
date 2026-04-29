#!/usr/bin/env bash
# Hermes Starter Kit — post-install verifier.
#
# Acceptance checks (per the v1 plan):
#   1. goose binary present and version printable
#   2. $GOOSE_CONFIG_DIR/config.yaml exists with GOOSE_PROVIDER set
#   3. each manifest.skill has SKILL.md with parseable YAML frontmatter
#   4. each manifest.recipe is valid YAML with title + (instructions|prompt)
#   5. each enabled connector's npm package can be fetched
#      (`npx -y <pkg> --help` exits 0 within 30s)
#   6. (optional) end-to-end recipe run; gated on RUN_E2E=1
#
# Env:
#   GOOSE_CONFIG_DIR   default: ${XDG_CONFIG_HOME:-$HOME/.config}/goose
#   STARTER_DIR        default: $GOOSE_CONFIG_DIR/.starter-kit
#   RUN_E2E            set to 1 to exercise check 6 (needs provider creds)
#
# Exit codes:
#   0  all checks passed
#   1  one or more checks failed
#   2  setup error (missing binaries, missing manifest, etc.)

set -uo pipefail

GOOSE_CONFIG_DIR="${GOOSE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/goose}"
STARTER_DIR="${STARTER_DIR:-$GOOSE_CONFIG_DIR/.starter-kit}"
MANIFEST="$STARTER_DIR/manifest.yaml"

PASS=0; FAIL=0
ok()   { printf '  \033[1;32m✓\033[0m %s\n' "$*"; PASS=$((PASS+1)); }
bad()  { printf '  \033[1;31m✗\033[0m %s\n' "$*"; FAIL=$((FAIL+1)); }
skip() { printf '  \033[1;33m-\033[0m %s\n' "$*"; }
hdr()  { printf '\n\033[1m%s\033[0m\n' "$*"; }

[[ -f "$MANIFEST" ]] || {
  echo "verify.sh: manifest not found at $MANIFEST" >&2
  exit 2
}

# 1. goose binary
hdr "1. Goose binary"
# Honor GOOSE_BIN if install.sh exported one; otherwise probe PATH and
# the canonical ~/.local/bin/goose location (macOS GUI-launched shells
# have a sparse PATH that omits ~/.local/bin/).
if [[ -z "${GOOSE_BIN:-}" ]]; then
  if command -v goose >/dev/null 2>&1; then
    GOOSE_BIN="goose"
  elif [[ -x "$HOME/.local/bin/goose" ]]; then
    GOOSE_BIN="$HOME/.local/bin/goose"
  fi
fi

if [[ -n "${GOOSE_BIN:-}" ]]; then
  ver="$("$GOOSE_BIN" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
  ok "goose found (version ${ver:-unknown}) at $GOOSE_BIN"
else
  bad "goose binary not found (checked PATH and ~/.local/bin/goose)"
fi

# 2. config.yaml (informational; the installer no longer manages this file)
hdr "2. config.yaml"
CFG="$GOOSE_CONFIG_DIR/config.yaml"
if [[ -f "$CFG" ]]; then
  ok "$CFG exists"
  if grep -qE '^GOOSE_PROVIDER:\s*"?\S+' "$CFG"; then
    ok "GOOSE_PROVIDER is set (Goose first-run completed)"
  else
    skip "GOOSE_PROVIDER not set yet — Goose's first-run flow handles this"
  fi
else
  skip "$CFG does not exist yet — Goose's first-run flow will create it"
fi

# 3. skills
hdr "3. Skills"
SKILL_PATHS=$(python3 "$STARTER_DIR/scripts/lib/extract-paths.py" "$MANIFEST" skills)
for sp in $SKILL_PATHS; do
  name="$(basename "$sp")"
  skill_md="$GOOSE_CONFIG_DIR/skills/$name/SKILL.md"
  if [[ ! -f "$skill_md" ]]; then
    bad "$name: SKILL.md missing at $skill_md"
    continue
  fi
  # Frontmatter parse: lines between leading '---' delimiters.
  if python3 - "$skill_md" <<'PY' 2>/dev/null; then
import sys, re
text = open(sys.argv[1]).read()
m = re.match(r"---\s*\n(.*?)\n---\s*\n", text, re.S)
if not m:
    sys.exit(1)
fm = m.group(1)
# Minimal validity: at least one key: value pair, and `name:` present.
if not re.search(r"^name:\s+\S+", fm, re.M):
    sys.exit(1)
PY
    ok "$name: SKILL.md frontmatter parses"
  else
    bad "$name: SKILL.md frontmatter missing or malformed"
  fi
done

# 4. recipes
hdr "4. Recipes"
RECIPE_PATHS=$(python3 "$STARTER_DIR/scripts/lib/extract-paths.py" "$MANIFEST" recipes)
for rp in $RECIPE_PATHS; do
  name="$(basename "$rp")"
  rfile="$GOOSE_CONFIG_DIR/recipes/$name"
  if [[ ! -f "$rfile" ]]; then
    bad "$name: missing"
    continue
  fi
  # Prefer `goose recipe validate` if available; else best-effort YAML check.
  if [[ -n "${GOOSE_BIN:-}" ]] && "$GOOSE_BIN" recipe validate "$rfile" >/dev/null 2>&1; then
    ok "$name: goose recipe validate ok"
  elif python3 - "$rfile" <<'PY' 2>/dev/null; then
import sys
try:
    import yaml
except ImportError:
    sys.exit(2)  # treated as skip below
data = yaml.safe_load(open(sys.argv[1]))
if not isinstance(data, dict): sys.exit(1)
if "title" not in data: sys.exit(1)
if not (data.get("instructions") or data.get("prompt")): sys.exit(1)
PY
    ok "$name: title + (instructions|prompt) present"
  else
    rc=$?
    if (( rc == 2 )); then
      skip "$name: PyYAML not installed; cannot validate recipe schema"
    else
      bad "$name: invalid"
    fi
  fi
done

# 5. connector endpoints
# Connectors are remote `streamable_http` MCP servers; we ping each
# enabled connector's URI to confirm DNS resolves and the host responds
# (any HTTP status, including 401/403 from "no auth yet"). A real OAuth
# handshake happens at first agent use, not here.
hdr "5. Connector endpoints"
ENABLED_CONNECTORS=$(python3 - "$CFG" <<'PY' 2>/dev/null
import sys
try:
    import yaml
except ImportError:
    sys.exit(0)
try:
    cfg = yaml.safe_load(open(sys.argv[1])) or {}
except Exception:
    sys.exit(0)
exts = (cfg.get("extensions") or {})
for name, body in exts.items():
    if not isinstance(body, dict):
        continue
    if not body.get("enabled", True):
        continue
    if body.get("type") != "streamable_http":
        continue
    uri = body.get("uri")
    if uri:
        print(f"{name}\t{uri}")
PY
)

# Pick a portable timeout wrapper for the curl probe.
if command -v timeout >/dev/null 2>&1; then
  TIMEOUT="timeout 10"
elif command -v gtimeout >/dev/null 2>&1; then
  TIMEOUT="gtimeout 10"
else
  TIMEOUT=""
fi

if [[ -z "$ENABLED_CONNECTORS" ]]; then
  skip "no remote connectors enabled (or PyYAML missing)"
elif ! command -v curl >/dev/null 2>&1; then
  skip "curl not on PATH; cannot probe connector endpoints"
else
  while IFS=$'\t' read -r name uri; do
    [[ -z "$name" ]] && continue
    # --connect-timeout 5 fails fast on DNS/TCP issues; -o /dev/null -s
    # discards body; -w prints the http_code. Any 2xx/3xx/4xx is fine
    # (it means we reached the server); only network errors fail the check.
    code=$($TIMEOUT curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$uri" 2>/dev/null || echo "000")
    if [[ "$code" =~ ^[2-4][0-9][0-9]$ ]]; then
      ok "$name: $uri reachable (HTTP $code)"
    else
      bad "$name: $uri unreachable (HTTP $code)"
    fi
  done <<< "$ENABLED_CONNECTORS"
fi

# 6. end-to-end (optional)
hdr "6. End-to-end recipe run"
if [[ "${RUN_E2E:-0}" != "1" ]]; then
  skip "skipped (set RUN_E2E=1 to run; requires provider creds)"
else
  if [[ -n "${GOOSE_BIN:-}" ]] && "$GOOSE_BIN" session --no-interactive --recipe onboarding --max-turns 1 >/dev/null 2>&1; then
    ok "onboarding recipe ran one turn"
  else
    bad "onboarding recipe failed (auth? missing provider?)"
  fi
fi

# ---- summary ------------------------------------------------------------
echo
echo "──────────────────────────────"
echo "  passed: $PASS"
echo "  failed: $FAIL"
echo "──────────────────────────────"
(( FAIL == 0 ))
