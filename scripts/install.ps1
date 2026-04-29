<#
.SYNOPSIS
  Hermes Starter Kit installer (Windows / PowerShell).

.DESCRIPTION
  Installs the kit's skills and recipes into the user's Goose config
  directory. The installer deliberately does NOT touch config.yaml,
  the model provider, or extension/connector setup — Goose's first-run
  flow handles provider/API-key entry, and the kit ships an
  interactive recipe (`set-up-notion`) that walks the user through
  adding a connector when they want one.

  Mirrors scripts/install.sh step-for-step. Keep them in sync.

.PARAMETER NonInteractive
  Fail on any required prompt (e.g. install Goose).

.PARAMETER Prefix
  Override the Goose config dir (testing).

.PARAMETER Ref
  Starter-kit git ref to check out.

.PARAMETER KitSource
  Use a local checkout instead of cloning (testing).

.EXAMPLE
  irm https://.../install.ps1 | iex

.EXAMPLE
  .\install.ps1
#>
[CmdletBinding()]
param(
    [switch]$Update,                  # accepted for back-compat; no-op
    [switch]$NonInteractive,
    [string]$Provider     = "",       # accepted for back-compat; no-op
    [string]$Connectors   = "",       # accepted for back-compat; no-op
    [string]$Prefix       = "",
    [string]$Ref          = "stable",
    [string]$KitSource    = ""
)

$ErrorActionPreference = "Stop"

$KitRepo = if ($env:KIT_REPO) { $env:KIT_REPO } else { "https://github.com/cultivarium/hermes-starter-kit.git" }

# ---- helpers ------------------------------------------------------------
function Log  ([string]$msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Warn ([string]$msg) { Write-Host "!!  $msg" -ForegroundColor Yellow }
function Die  ([string]$msg) { Write-Host "xx  $msg" -ForegroundColor Red; exit 1 }

function Require-Tool ([string]$name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Die "missing required tool: $name"
    }
}

function Semver-Lt ([string]$a, [string]$b) {
    try {
        $va = [version]$a
        $vb = [version]$b
        return $va -lt $vb
    } catch {
        return $false
    }
}

# ---- 1. preflight -------------------------------------------------------
Log "Preflight"
Require-Tool git
Require-Tool python

$GooseConfigDir = if ($Prefix) { $Prefix } else { Join-Path $env:APPDATA "Block\goose\config" }
New-Item -ItemType Directory -Force -Path $GooseConfigDir | Out-Null
Log "Config dir: $GooseConfigDir"

# ---- 2. ensure goose ----------------------------------------------------
Log "Checking for Goose"
$GooseInstalledVersion = ""
if (Get-Command goose -ErrorAction SilentlyContinue) {
    $verLine = (& goose --version 2>$null) -join " "
    if ($verLine -match '(\d+\.\d+\.\d+)') {
        $GooseInstalledVersion = $matches[1]
    }
    Log "Found goose $GooseInstalledVersion"
} else {
    Warn "Goose is not installed."
    if ($NonInteractive) {
        Die "Goose missing and -NonInteractive set; install Goose first."
    }
    $ans = Read-Host "Install Goose now from the official AAIF release? [Y/n]"
    if (-not $ans) { $ans = "Y" }
    if ($ans -match '^[Yy]') {
        Warn "Automated Goose install on Windows is not yet wired up here."
        Warn "Please install Goose from https://goose-docs.ai/docs/getting-started/installation"
        Warn "and re-run this script."
        exit 1
    } else {
        Die "Aborting; install Goose and re-run."
    }
}

# ---- 3. fetch starter kit ----------------------------------------------
$StarterDir = Join-Path $GooseConfigDir ".starter-kit"

if ($KitSource) {
    Log "Using local kit source: $KitSource"
    $StarterDir = $KitSource
} elseif (Test-Path (Join-Path $StarterDir ".git")) {
    Log "Updating starter kit at $StarterDir"
    git -C $StarterDir fetch --quiet --depth 1 origin $Ref
    # Detach to FETCH_HEAD rather than `git checkout $Ref`. The latter
    # checks out the *local* branch named $Ref, which fetch does not
    # fast-forward — leaving the working tree at the old commit even
    # after a successful fetch. The .starter-kit/ dir is install-managed,
    # so detached HEAD is fine and works for both branches and tags.
    git -C $StarterDir checkout --quiet --detach FETCH_HEAD
} else {
    Log "Cloning starter kit ($Ref) into $StarterDir"
    git clone --quiet --depth 1 --branch $Ref $KitRepo $StarterDir
}

$Manifest = Join-Path $StarterDir "manifest.yaml"
if (-not (Test-Path $Manifest)) { Die "manifest.yaml not found at $Manifest" }

$ManifestText = Get-Content $Manifest -Raw
$MinGooseVersion = if ($ManifestText -match 'min_goose_version:\s*"([^"]+)"') { $matches[1] } else { "0.0.0" }
$KitVersion      = if ($ManifestText -match 'kit_version:\s*"?([^\s"]+)"?')   { $matches[1] } else { "0.0.0" }
Log "Kit version $KitVersion (min Goose $MinGooseVersion)"

if ($GooseInstalledVersion -and (Semver-Lt $GooseInstalledVersion $MinGooseVersion)) {
    Warn "Installed Goose ($GooseInstalledVersion) is older than recommended ($MinGooseVersion)."
    Warn "Continuing anyway; some skills/recipes may not work."
}

# ---- 4. install skills/recipes (sha256-tracked) ------------------------
$StateFile = Join-Path $GooseConfigDir ".starter-kit-state.json"
Log "Installing skills and recipes (state: $StateFile)"
New-Item -ItemType Directory -Force -Path (Join-Path $GooseConfigDir "skills"),(Join-Path $GooseConfigDir "recipes") | Out-Null

$SkillPaths  = (& python (Join-Path $StarterDir "scripts\lib\extract-paths.py") $Manifest "skills")  -split "`n" | Where-Object { $_ }
$RecipePaths = (& python (Join-Path $StarterDir "scripts\lib\extract-paths.py") $Manifest "recipes") -split "`n" | Where-Object { $_ }

$InstallArgs = @($StarterDir, $GooseConfigDir, $StateFile, ($SkillPaths -join ' '), ($RecipePaths -join ' '))
& python (Join-Path $StarterDir "scripts\lib\install-files.py") @InstallArgs

# ---- 5. verify ---------------------------------------------------------
$VerifyScript = Join-Path $StarterDir "scripts\lib\verify.ps1"
if (Test-Path $VerifyScript) {
    Log "Running verify.ps1"
    $env:GOOSE_CONFIG_DIR = $GooseConfigDir
    $env:STARTER_DIR = $StarterDir
    & $VerifyScript
}

# ---- 6. summary --------------------------------------------------------
$Advertise = & python (Join-Path $StarterDir "scripts\lib\extract-paths.py") $Manifest "starter_recipes_to_advertise"

Write-Host ""
Write-Host "──────────────────────────────────────────────────────────────"
Write-Host "Hermes Starter Kit $KitVersion installed."
Write-Host ""
Write-Host "Config dir : $GooseConfigDir"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Open Goose (Desktop or CLI). On first run it'll prompt you for a"
Write-Host "     model provider (Anthropic, OpenAI, Ollama). Pick whichever you"
Write-Host "     have a key for; Goose stores the key in your OS keyring."
Write-Host ""
Write-Host "  2. Try the onboarding recipe to confirm everything loaded:"
Write-Host "       goose recipe run onboarding"
Write-Host ""
Write-Host "  3. Want to wire up an external data source? Walk through the"
Write-Host "     guided setup recipe:"
$Advertise -split "`n" | Where-Object { $_ } | ForEach-Object { Write-Host "       goose recipe run $_" }
Write-Host ""
Write-Host "Re-run this script any time to refresh skills and recipes:"
Write-Host "  .\install.ps1"
Write-Host "──────────────────────────────────────────────────────────────"
