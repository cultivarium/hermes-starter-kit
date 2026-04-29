#!/usr/bin/env bash
# Hermes Starter Kit installer.
#
# Installs the kit's skills and recipes into the user's Goose config
# directory. The installer deliberately does NOT touch config.yaml,
# the model provider, or extension/connector setup — Goose's first-run
# flow handles provider/API-key entry, and the kit ships an
# interactive recipe (`set-up-notion`) that walks the user through
# adding a connector when they want one.
#
# Usage:
#   curl -fsSL <repo>/scripts/install.sh | bash
#   ./install.sh --update
#
# Flags:
#   --update                 same install path as default; kept for backward
#                            compatibility with users who scripted around it
#   --non-interactive        fail on any required prompt (e.g. install Goose)
#   --prefix <path>          override $GOOSE_CONFIG_DIR (testing)
#   --ref <git-ref>          starter-kit ref to check out
#   --kit-source <path>      use a local checkout instead of cloning (testing)
#
# This script's behaviour mirrors install.ps1 step-for-step. Keep them in sync.

set -euo pipefail

# ---- defaults ------------------------------------------------------------
KIT_REPO="${KIT_REPO:-https://github.com/cultivarium/hermes-starter-kit.git}"
KIT_REF="stable"
NON_INTERACTIVE=0
PREFIX=""
KIT_SOURCE=""

# ---- arg parsing ---------------------------------------------------------
while (( $# > 0 )); do
  case "$1" in
    --update)            shift ;;                # accepted for back-compat; no-op
    --non-interactive)   NON_INTERACTIVE=1; shift ;;
    --prefix)            PREFIX="$2"; shift 2 ;;
    --ref)               KIT_REF="$2"; shift 2 ;;
    --kit-source)        KIT_SOURCE="$2"; shift 2 ;;
    -h|--help)           sed -n '1,28p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    # Quiet legacy flags from <0.4.0; ignored with a hint so old scripts don't break loud.
    --provider)          shift 2 ;;
    --connectors)        shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# ---- helpers -------------------------------------------------------------
log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!! \033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mxx \033[0m %s\n' "$*" >&2; exit 1; }

require() {
  command -v "$1" >/dev/null 2>&1 \
    || die "missing required tool: $1"
}

semver_lt() {
  [[ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -1)" == "$1" && "$1" != "$2" ]]
}

# ---- 1. preflight --------------------------------------------------------
log "Preflight"
require curl
require git
require python3

OS="$(uname -s)"
case "$OS" in
  Darwin|Linux) ;;
  *) die "unsupported OS: $OS (use install.ps1 on Windows)" ;;
esac

GOOSE_CONFIG_DIR="${PREFIX:-${XDG_CONFIG_HOME:-$HOME/.config}/goose}"
mkdir -p "$GOOSE_CONFIG_DIR"
log "Config dir: $GOOSE_CONFIG_DIR"

# ---- 2. ensure goose -----------------------------------------------------
log "Checking for Goose"
GOOSE_INSTALLED_VERSION=""
if command -v goose >/dev/null 2>&1; then
  GOOSE_INSTALLED_VERSION="$(goose --version 2>/dev/null \
    | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
  log "Found goose $GOOSE_INSTALLED_VERSION"
else
  warn "Goose is not installed."
  if (( NON_INTERACTIVE )); then
    die "Goose missing and --non-interactive set; install Goose first."
  fi
  read -r -p "Install Goose now from the official AAIF release? [Y/n]: " ans
  ans="${ans:-Y}"
  if [[ "$ans" =~ ^[Yy]$ ]]; then
    log "Running official Goose installer"
    curl -fsSL https://github.com/aaif-goose/goose/releases/download/stable/download_cli.sh \
      | CONFIGURE=false bash
  else
    die "Aborting; install Goose and re-run."
  fi
fi

# ---- 3. fetch starter kit ------------------------------------------------
STARTER_DIR="$GOOSE_CONFIG_DIR/.starter-kit"

if [[ -n "$KIT_SOURCE" ]]; then
  log "Using local kit source: $KIT_SOURCE"
  STARTER_DIR="$KIT_SOURCE"
elif [[ -d "$STARTER_DIR/.git" ]]; then
  log "Updating starter kit at $STARTER_DIR"
  git -C "$STARTER_DIR" fetch --quiet --depth 1 origin "$KIT_REF"
  git -C "$STARTER_DIR" checkout --quiet "$KIT_REF"
else
  log "Cloning starter kit ($KIT_REF) into $STARTER_DIR"
  git clone --quiet --depth 1 --branch "$KIT_REF" "$KIT_REPO" "$STARTER_DIR"
fi

MANIFEST="$STARTER_DIR/manifest.yaml"
[[ -f "$MANIFEST" ]] || die "manifest.yaml not found at $MANIFEST"

MIN_GOOSE_VERSION="$(grep -E '^min_goose_version:' "$MANIFEST" \
  | sed -E 's/.*"([^"]+)".*/\1/')"
KIT_VERSION="$(grep -E '^kit_version:' "$MANIFEST" \
  | sed -E 's/.*: *"?([^"]+)"?.*/\1/')"
log "Kit version $KIT_VERSION (min Goose $MIN_GOOSE_VERSION)"

if [[ -n "$GOOSE_INSTALLED_VERSION" ]] \
  && semver_lt "$GOOSE_INSTALLED_VERSION" "$MIN_GOOSE_VERSION"; then
  warn "Installed Goose ($GOOSE_INSTALLED_VERSION) is older than recommended ($MIN_GOOSE_VERSION)."
  warn "Continuing anyway; some skills/recipes may not work."
fi

# ---- 4. install skills/recipes (sha256-tracked for idempotency) --------
# State file: maps every relative path the installer has ever written to
# the sha256 of what we wrote there. On re-run, files whose on-disk hash
# still matches the recorded sha are pristine and safe to overwrite;
# files whose hash differs have been hand-edited and we leave alone.
STATE_FILE="$GOOSE_CONFIG_DIR/.starter-kit-state.json"
log "Installing skills and recipes (state: $STATE_FILE)"
mkdir -p "$GOOSE_CONFIG_DIR/skills" "$GOOSE_CONFIG_DIR/recipes"

SKILL_PATHS=$(python3 "$STARTER_DIR/scripts/lib/extract-paths.py" "$MANIFEST" skills)
RECIPE_PATHS=$(python3 "$STARTER_DIR/scripts/lib/extract-paths.py" "$MANIFEST" recipes)

python3 "$STARTER_DIR/scripts/lib/install-files.py" \
  "$STARTER_DIR" "$GOOSE_CONFIG_DIR" "$STATE_FILE" \
  "$SKILL_PATHS" "$RECIPE_PATHS"

# ---- 5. verify ----------------------------------------------------------
if [[ -x "$STARTER_DIR/scripts/lib/verify.sh" ]]; then
  log "Running verify.sh"
  GOOSE_CONFIG_DIR="$GOOSE_CONFIG_DIR" STARTER_DIR="$STARTER_DIR" \
    "$STARTER_DIR/scripts/lib/verify.sh" || \
    warn "verify.sh reported issues; see output above."
fi

# ---- 6. summary ---------------------------------------------------------
ADVERTISE=$(python3 "$STARTER_DIR/scripts/lib/extract-paths.py" \
  "$MANIFEST" starter_recipes_to_advertise)

cat <<EOF

──────────────────────────────────────────────────────────────
Hermes Starter Kit $KIT_VERSION installed.

Config dir : $GOOSE_CONFIG_DIR

Next steps:
  1. Open Goose (Desktop or CLI). On first run it'll prompt you for a
     model provider (Anthropic, OpenAI, Ollama). Pick whichever you
     have a key for; Goose stores the key in your OS keyring.

  2. Try the onboarding recipe to confirm everything loaded:
       goose recipe run onboarding

  3. Want to wire up an external data source? Walk through the
     guided setup recipe:
$(echo "$ADVERTISE" | sed 's/^/       goose recipe run /')

Re-run this script any time to refresh skills and recipes:
  bash $0
──────────────────────────────────────────────────────────────
EOF
