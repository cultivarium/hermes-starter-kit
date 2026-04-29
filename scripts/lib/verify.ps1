<#
.SYNOPSIS
  Hermes Starter Kit post-install verifier (Windows).

.DESCRIPTION
  Mirrors scripts/lib/verify.sh check-for-check. Keep them in sync.

.NOTES
  Env vars:
    GOOSE_CONFIG_DIR  default: %APPDATA%\Block\goose\config
    STARTER_DIR       default: $GOOSE_CONFIG_DIR\.starter-kit
    RUN_E2E           set to 1 for the optional end-to-end recipe run

  Exit codes: 0 all passed; 1 some failed; 2 setup error.
#>
$ErrorActionPreference = "Continue"

$GooseConfigDir = if ($env:GOOSE_CONFIG_DIR) { $env:GOOSE_CONFIG_DIR } else { Join-Path $env:APPDATA "Block\goose\config" }
$StarterDir    = if ($env:STARTER_DIR)      { $env:STARTER_DIR }      else { Join-Path $GooseConfigDir ".starter-kit" }
$Manifest      = Join-Path $StarterDir "manifest.yaml"

if (-not (Test-Path $Manifest)) {
    Write-Error "verify.ps1: manifest not found at $Manifest"
    exit 2
}

$script:Pass = 0; $script:Fail = 0
function Hdr  ([string]$msg) { Write-Host "`n$msg" -ForegroundColor White }
function OK   ([string]$msg) { Write-Host "  [+] $msg" -ForegroundColor Green; $script:Pass++ }
function Bad  ([string]$msg) { Write-Host "  [-] $msg" -ForegroundColor Red;   $script:Fail++ }
function Skip ([string]$msg) { Write-Host "  [~] $msg" -ForegroundColor Yellow }

# 1. goose binary
Hdr "1. Goose binary"
if (Get-Command goose -ErrorAction SilentlyContinue) {
    $verLine = (& goose --version 2>$null) -join " "
    $ver = if ($verLine -match '(\d+\.\d+\.\d+)') { $matches[1] } else { "unknown" }
    OK "goose found (version $ver)"
} else {
    Bad "goose binary not on PATH"
}

# 2. config.yaml (informational; the installer no longer manages this file)
Hdr "2. config.yaml"
$Cfg = Join-Path $GooseConfigDir "config.yaml"
if (Test-Path $Cfg) {
    OK "$Cfg exists"
    if ((Get-Content $Cfg -Raw) -match '(?m)^GOOSE_PROVIDER:\s*"?\S+') {
        OK "GOOSE_PROVIDER is set (Goose first-run completed)"
    } else {
        Skip "GOOSE_PROVIDER not set yet -- Goose's first-run flow handles this"
    }
} else {
    Skip "$Cfg does not exist yet -- Goose's first-run flow will create it"
}

# 3. skills
Hdr "3. Skills"
$SkillPaths = (& python (Join-Path $StarterDir "scripts\lib\extract-paths.py") $Manifest skills) -split "`n" | Where-Object { $_ }
foreach ($sp in $SkillPaths) {
    $name = Split-Path -Leaf $sp
    $skillMd = Join-Path $GooseConfigDir "skills\$name\SKILL.md"
    if (-not (Test-Path $skillMd)) { Bad "${name}: SKILL.md missing"; continue }
    $text = Get-Content $skillMd -Raw
    if ($text -match '(?s)^---\s*\r?\n(.*?)\r?\n---\s*\r?\n' -and $matches[1] -match '(?m)^name:\s+\S+') {
        OK "${name}: SKILL.md frontmatter parses"
    } else {
        Bad "${name}: SKILL.md frontmatter missing or malformed"
    }
}

# 4. recipes
Hdr "4. Recipes"
$RecipePaths = (& python (Join-Path $StarterDir "scripts\lib\extract-paths.py") $Manifest recipes) -split "`n" | Where-Object { $_ }
foreach ($rp in $RecipePaths) {
    $name = Split-Path -Leaf $rp
    $rfile = Join-Path $GooseConfigDir "recipes\$name"
    if (-not (Test-Path $rfile)) { Bad "${name}: missing"; continue }
    & goose recipe validate $rfile 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        OK "${name}: goose recipe validate ok"
    } else {
        # Best-effort YAML check via Python.
        $rc = 0
        & python -c "import sys, yaml; d = yaml.safe_load(open(sys.argv[1])); sys.exit(0 if isinstance(d, dict) and 'title' in d and (d.get('instructions') or d.get('prompt')) else 1)" $rfile 2>$null
        $rc = $LASTEXITCODE
        if ($rc -eq 0) { OK "${name}: title + (instructions|prompt) present" }
        else { Bad "${name}: invalid (or PyYAML missing)" }
    }
}

# 5. connector endpoints
# Connectors are remote `streamable_http` MCP servers; we probe each
# enabled connector's URI via HTTP HEAD/GET to confirm DNS resolves and
# the host responds. Any 2xx/3xx/4xx is a pass (means we reached the
# server). Real OAuth handshake happens at first agent use, not here.
Hdr "5. Connector endpoints"
$pyExtract = @"
import sys
try:
    import yaml
except ImportError:
    sys.exit(0)
try:
    cfg = yaml.safe_load(open(sys.argv[1])) or {}
except Exception:
    sys.exit(0)
exts = (cfg.get('extensions') or {})
for name, body in exts.items():
    if not isinstance(body, dict):
        continue
    if not body.get('enabled', True):
        continue
    if body.get('type') != 'streamable_http':
        continue
    uri = body.get('uri')
    if uri:
        print(name + '\t' + uri)
"@
$enabled = & python -c $pyExtract $Cfg
if (-not $enabled) {
    Skip "no remote connectors enabled (or PyYAML missing)"
} else {
    foreach ($line in $enabled) {
        if (-not $line) { continue }
        $parts = $line -split "`t"
        $cn = $parts[0]; $uri = $parts[1]
        try {
            $resp = Invoke-WebRequest -Uri $uri -Method Head -TimeoutSec 10 `
                -UseBasicParsing -SkipHttpErrorCheck -ErrorAction Stop
            $code = [int]$resp.StatusCode
            if ($code -ge 200 -and $code -lt 500) {
                OK "${cn}: $uri reachable (HTTP $code)"
            } else {
                Bad "${cn}: $uri returned HTTP $code"
            }
        } catch {
            Bad "${cn}: $uri unreachable ($($_.Exception.Message))"
        }
    }
}

# 6. end-to-end (optional)
Hdr "6. End-to-end recipe run"
if ($env:RUN_E2E -ne "1") {
    Skip "skipped (set RUN_E2E=1 to run; requires provider creds)"
} else {
    & goose session --no-interactive --recipe onboarding --max-turns 1 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        OK "onboarding recipe ran one turn"
    } else {
        Bad "onboarding recipe failed (auth? missing provider?)"
    }
}

Write-Host ""
Write-Host "------------------------------"
Write-Host "  passed: $script:Pass"
Write-Host "  failed: $script:Fail"
Write-Host "------------------------------"
if ($script:Fail -ne 0) { exit 1 }
exit 0
