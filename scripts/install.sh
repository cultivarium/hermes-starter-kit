#!/usr/bin/env bash
# Hermes Starter Kit installer (CLI path).
#
# Minimal install for sophisticated users on macOS / Linux:
#   1. checks deps (curl, git, python3)
#   2. installs Goose CLI (if missing)
#   3. installs Goose Desktop (if missing)
#   4. installs the kit's skills and recipes into ~/.config/goose/
#
# Does NOT touch ~/.config/goose/config.yaml, choose a model provider, or
# wire up extensions. Goose's first-run flow handles provider/API-key
# entry; the kit ships a `set-up-notion` recipe for connector wiring.
#
# Windows users: use the Hermes GUI installer; this script does not
# support Windows.
#
# Usage:
#   curl -fsSL <repo>/scripts/install.sh | bash
#   ./install.sh
#
# Flags:
#   --non-interactive        fail on any required prompt (CI/automation)
#   --no-desktop             skip Goose Desktop install (CLI-only setup)
#   --prefix <path>          override $GOOSE_CONFIG_DIR (testing)
#   --ref <git-ref>          starter-kit ref to check out
#   --kit-source <path>      use a local checkout instead of cloning (testing)
#   --update                 accepted for back-compat; re-running is idempotent

set -euo pipefail

# ---- defaults ------------------------------------------------------------
KIT_REPO="${KIT_REPO:-https://github.com/cultivarium/hermes-starter-kit.git}"
KIT_REF="stable"
NON_INTERACTIVE=0
INSTALL_DESKTOP=1
PREFIX=""
KIT_SOURCE=""

# ---- arg parsing ---------------------------------------------------------
while (( $# > 0 )); do
  case "$1" in
    --update)            shift ;;                # accepted for back-compat; no-op
    --non-interactive)   NON_INTERACTIVE=1; shift ;;
    --no-desktop)        INSTALL_DESKTOP=0; shift ;;
    --prefix)            PREFIX="$2"; shift 2 ;;
    --ref)               KIT_REF="$2"; shift 2 ;;
    --kit-source)        KIT_SOURCE="$2"; shift 2 ;;
    -h|--help)           sed -n '1,27p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
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
ARCH="$(uname -m)"
case "$OS" in
  Darwin|Linux) ;;
  *) die "unsupported OS: $OS — Windows users should run the Hermes GUI installer." ;;
esac

GOOSE_CONFIG_DIR="${PREFIX:-${XDG_CONFIG_HOME:-$HOME/.config}/goose}"
mkdir -p "$GOOSE_CONFIG_DIR"
log "Config dir: $GOOSE_CONFIG_DIR"

# ---- 2. ensure goose CLI -------------------------------------------------
log "Checking for Goose CLI"
GOOSE_BIN=""
GOOSE_INSTALLED_VERSION=""
if command -v goose >/dev/null 2>&1; then
  GOOSE_BIN="goose"
elif [[ -x "$HOME/.local/bin/goose" ]]; then
  # macOS GUI apps launched via `open` inherit a minimal PATH that does
  # not include ~/.local/bin/, so `command -v goose` misses Goose even
  # when it was just placed there by the official AAIF installer. Probe
  # the canonical install location directly so the kit is self-sufficient
  # under non-PATH-aware callers (CI, Docker, Tauri-spawned shells).
  GOOSE_BIN="$HOME/.local/bin/goose"
fi

if [[ -n "$GOOSE_BIN" ]]; then
  GOOSE_INSTALLED_VERSION="$("$GOOSE_BIN" --version 2>/dev/null \
    | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
  log "Found goose $GOOSE_INSTALLED_VERSION ($GOOSE_BIN)"
  export GOOSE_BIN
else
  warn "Goose CLI is not installed."
  if (( NON_INTERACTIVE )); then
    die "Goose missing and --non-interactive set; install Goose first."
  fi
  read -r -p "Install Goose CLI now from the official AAIF release? [Y/n]: " ans
  ans="${ans:-Y}"
  if [[ "$ans" =~ ^[Yy]$ ]]; then
    log "Running official Goose installer"
    curl -fsSL https://github.com/aaif-goose/goose/releases/download/stable/download_cli.sh \
      | CONFIGURE=false bash
    # The AAIF installer drops the binary at ~/.local/bin/goose. Pick it
    # up directly so the rest of this script (and verify.sh) can use it
    # without relying on the user's PATH being refreshed.
    if [[ -x "$HOME/.local/bin/goose" ]]; then
      GOOSE_BIN="$HOME/.local/bin/goose"
      export GOOSE_BIN
    fi
  else
    die "Aborting; install Goose and re-run."
  fi
fi

# ---- 3. ensure goose Desktop --------------------------------------------
install_desktop_macos() {
  # AAIF doesn't publish a .dmg for Desktop; macOS bundles ship as zips:
  #   Goose.zip            (Apple Silicon)
  #   Goose_intel_mac.zip  (Intel)
  # Both unzip to a top-level Goose.app we copy into /Applications via ditto.
  local zip_name
  case "$ARCH" in
    arm64|aarch64) zip_name="Goose.zip" ;;
    x86_64)        zip_name="Goose_intel_mac.zip" ;;
    *) warn "unsupported macOS arch: $ARCH — skipping Desktop install."; return 0 ;;
  esac
  local url="https://github.com/aaif-goose/goose/releases/latest/download/$zip_name"
  local tmp
  tmp="$(mktemp -d)"
  log "Downloading $url"
  curl -fL --progress-bar -o "$tmp/$zip_name" "$url"
  log "Unzipping Goose.app"
  (cd "$tmp" && unzip -q -o "$zip_name")
  if [[ ! -d "$tmp/Goose.app" ]]; then
    rm -rf "$tmp"
    warn "Goose.app missing from zip; skipping."
    return 0
  fi
  if [[ -d "/Applications/Goose.app" ]]; then
    log "Removing previous /Applications/Goose.app"
    rm -rf "/Applications/Goose.app"
  fi
  log "Copying Goose.app to /Applications"
  ditto --rsrc "$tmp/Goose.app" "/Applications/Goose.app"
  rm -rf "$tmp"
}

install_desktop_linux() {
  # AAIF Linux Desktop ships only as .deb / .rpm / .flatpak — installing
  # any of these needs sudo or flatpak setup, and the asset filenames
  # carry a version, so we resolve the asset URL via the GitHub API.
  local url="" kind=""
  if command -v apt >/dev/null 2>&1 || command -v apt-get >/dev/null 2>&1; then
    kind="deb"
    url="$(curl -fsSL https://api.github.com/repos/aaif-goose/goose/releases/latest \
      | grep -oE '"browser_download_url": *"[^"]*\.deb"' \
      | head -1 | sed -E 's/.*"([^"]+)"$/\1/')"
  elif command -v dnf >/dev/null 2>&1 || command -v yum >/dev/null 2>&1 || command -v rpm >/dev/null 2>&1; then
    kind="rpm"
    url="$(curl -fsSL https://api.github.com/repos/aaif-goose/goose/releases/latest \
      | grep -oE '"browser_download_url": *"[^"]*\.rpm"' \
      | head -1 | sed -E 's/.*"([^"]+)"$/\1/')"
  elif command -v flatpak >/dev/null 2>&1; then
    kind="flatpak"
    url="$(curl -fsSL https://api.github.com/repos/aaif-goose/goose/releases/latest \
      | grep -oE '"browser_download_url": *"[^"]*\.flatpak"' \
      | head -1 | sed -E 's/.*"([^"]+)"$/\1/')"
  fi

  if [[ -z "$url" ]]; then
    warn "Could not detect a supported package manager (apt/dnf/flatpak)."
    warn "Goose Desktop binaries: https://github.com/aaif-goose/goose/releases/latest"
    return 0
  fi

  if (( NON_INTERACTIVE )); then
    log "Goose Desktop available at: $url"
    log "Skipping Desktop install in --non-interactive mode."
    return 0
  fi

  read -r -p "Install Goose Desktop ($kind, requires sudo)? [Y/n]: " ans
  ans="${ans:-Y}"
  if [[ ! "$ans" =~ ^[Yy]$ ]]; then
    log "Skipped Goose Desktop install. Get it later from: $url"
    return 0
  fi

  local tmp pkg
  tmp="$(mktemp -d)"
  pkg="$tmp/$(basename "$url")"
  log "Downloading $url"
  curl -fL --progress-bar -o "$pkg" "$url"
  case "$kind" in
    deb)
      if command -v apt >/dev/null 2>&1; then sudo apt install -y "$pkg"
      else sudo dpkg -i "$pkg"
      fi
      ;;
    rpm)
      if command -v dnf >/dev/null 2>&1; then sudo dnf install -y "$pkg"
      elif command -v yum >/dev/null 2>&1; then sudo yum install -y "$pkg"
      else sudo rpm -i --replacepkgs "$pkg"
      fi
      ;;
    flatpak) flatpak install -y --user "$pkg" ;;
  esac
  rm -rf "$tmp"
}

desktop_installed_macos() { [[ -d "/Applications/Goose.app" ]]; }
desktop_installed_linux() {
  command -v goose-desktop >/dev/null 2>&1 \
    || (command -v dpkg >/dev/null 2>&1 && dpkg -s goose >/dev/null 2>&1) \
    || (command -v rpm  >/dev/null 2>&1 && rpm  -q goose >/dev/null 2>&1) \
    || (command -v flatpak >/dev/null 2>&1 && flatpak list --app 2>/dev/null | grep -qi goose)
}

if (( INSTALL_DESKTOP )); then
  log "Checking for Goose Desktop"
  case "$OS" in
    Darwin)
      if desktop_installed_macos; then
        log "Goose Desktop already at /Applications/Goose.app"
      else
        install_desktop_macos
      fi
      ;;
    Linux)
      if desktop_installed_linux; then
        log "Goose Desktop already installed"
      else
        install_desktop_linux
      fi
      ;;
  esac
else
  log "Skipping Goose Desktop (--no-desktop)"
fi

# ---- 4. fetch starter kit -----------------------------------------------
STARTER_DIR="$GOOSE_CONFIG_DIR/.starter-kit"

if [[ -n "$KIT_SOURCE" ]]; then
  log "Using local kit source: $KIT_SOURCE"
  STARTER_DIR="$KIT_SOURCE"
elif [[ -d "$STARTER_DIR/.git" ]]; then
  log "Updating starter kit at $STARTER_DIR"
  git -C "$STARTER_DIR" fetch --quiet --depth 1 origin "$KIT_REF"
  # Detach to FETCH_HEAD rather than `git checkout "$KIT_REF"`. The latter
  # checks out the *local* branch named $KIT_REF, which fetch does not
  # fast-forward — leaving the working tree at the old commit even after
  # a successful fetch. The .starter-kit/ dir is an install-managed
  # asset, so detached HEAD is fine and works for both branches and tags.
  git -C "$STARTER_DIR" checkout --quiet --detach FETCH_HEAD
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

# ---- 5. install skills/recipes (sha256-tracked for idempotency) --------
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

# ---- 6. verify ----------------------------------------------------------
if [[ -x "$STARTER_DIR/scripts/lib/verify.sh" ]]; then
  log "Running verify.sh"
  GOOSE_CONFIG_DIR="$GOOSE_CONFIG_DIR" STARTER_DIR="$STARTER_DIR" \
    "$STARTER_DIR/scripts/lib/verify.sh" || \
    warn "verify.sh reported issues; see output above."
fi

# ---- 7. summary ---------------------------------------------------------
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
