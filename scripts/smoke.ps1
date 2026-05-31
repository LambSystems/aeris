param(
    [switch]$WithUi,
    [string]$Python = "",
    [string]$CondaEnv = "aeris-backend",
    [string]$ApiUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Set-Location $RepoRoot
$env:PYTHONPATH = "backend"

function Invoke-AerisPython {
    param([string[]]$Arguments)

    if ($Python -and (Get-Command $Python -ErrorAction SilentlyContinue)) {
        & $Python @Arguments
        return
    }

    if (($env:VIRTUAL_ENV -or $env:CONDA_PREFIX) -and (Get-Command python -ErrorAction SilentlyContinue)) {
        & python @Arguments
        return
    }

    if (Get-Command conda -ErrorAction SilentlyContinue) {
        & conda run -n $CondaEnv python @Arguments
        return
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python @Arguments
        return
    }

    throw "Python was not found. Activate a Python environment or install/create the Conda env '$CondaEnv'."
}

Write-Host "Running backend unit tests..."
Invoke-AerisPython @("-m", "unittest", "discover", "-s", "tests")

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Checking optional live API smoke path at $ApiUrl ..."
$apiIsRunning = $false
try {
    Invoke-RestMethod -Uri "$ApiUrl/health" -TimeoutSec 3 | Out-Null
    $apiIsRunning = $true
}
catch {
    Write-Host "API is not running; skipping HTTP smoke. Start it with .\scripts\dev.ps1 to include live endpoint checks."
}

if ($apiIsRunning) {
    $env:AERIS_API_URL = $ApiUrl
    Invoke-AerisPython @("scripts\smoke_backend.py")
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if ($WithUi) {
    Write-Host ""
    Write-Host "Running UI tests and build..."
    Push-Location (Join-Path $RepoRoot "ui")
    try {
        npm run test
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }

        npm run build
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "Smoke checks passed."
