param(
    [switch]$WithUi,
    [int]$ApiPort = 8000,
    [int]$StreamlitPort = 8507,
    [int]$UiPort = 5173,
    [string]$Python = "",
    [string]$CondaEnv = "aeris-backend"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendRoot = Join-Path $RepoRoot "backend"
$UiRoot = Join-Path $RepoRoot "ui"
$RootEnv = Join-Path $RepoRoot ".env"
$RootEnvExample = Join-Path $RepoRoot ".env.example"
$ModelPath = Join-Path $BackendRoot "models\trash-quick-v4-best.pt"

if (-not (Test-Path $RootEnv) -and (Test-Path $RootEnvExample)) {
    Copy-Item $RootEnvExample $RootEnv
    Write-Host "Created .env from .env.example"
}

if (-not $env:YOLO_MODEL_PATH -and (Test-Path $ModelPath)) {
    $env:YOLO_MODEL_PATH = (Resolve-Path $ModelPath).Path
}

$env:PYTHONPATH = "backend"
$env:AERIS_PUBLIC_STREAMLIT_URL = "http://127.0.0.1:$StreamlitPort"

$jobs = @()

function Resolve-PythonCommand {
    if ($Python -and (Get-Command $Python -ErrorAction SilentlyContinue)) {
        return $Python
    }

    if (($env:VIRTUAL_ENV -or $env:CONDA_PREFIX) -and (Get-Command python -ErrorAction SilentlyContinue)) {
        return "python"
    }

    if (Get-Command conda -ErrorAction SilentlyContinue) {
        return "conda run -n $CondaEnv python"
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }

    throw "Python was not found. Activate a Python environment or install/create the Conda env '$CondaEnv'."
}

function Start-AerisJob {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Command
    )

    Write-Host "Starting $Name..."
    Start-Job -Name $Name -InitializationScript {
        $ErrorActionPreference = "Stop"
    } -ScriptBlock {
        param($WorkingDirectory, $CommandText)
        Set-Location $WorkingDirectory
        Invoke-Expression $CommandText
    } -ArgumentList $WorkingDirectory, $Command
}

$PythonCommand = Resolve-PythonCommand
$ApiCommand = "$PythonCommand -m uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port $ApiPort"
$StreamlitCommand = "$PythonCommand -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port $StreamlitPort"
$UiCommand = "npm run dev -- --host 0.0.0.0 --port $UiPort"

$jobs += Start-AerisJob `
    -Name "aeris-api" `
    -WorkingDirectory $RepoRoot `
    -Command $ApiCommand

$jobs += Start-AerisJob `
    -Name "aeris-streamlit" `
    -WorkingDirectory $BackendRoot `
    -Command $StreamlitCommand

if ($WithUi) {
    $env:VITE_VISION_PROVIDER = "streamlit-embed"
    $env:VITE_STREAMLIT_URL = "http://127.0.0.1:$StreamlitPort?embed=true"

    $jobs += Start-AerisJob `
        -Name "aeris-ui" `
        -WorkingDirectory $UiRoot `
        -Command $UiCommand
}

Write-Host ""
Write-Host "Aeris local services are starting:"
Write-Host "  FastAPI:   http://127.0.0.1:$ApiPort/docs"
Write-Host "  Streamlit: http://127.0.0.1:$StreamlitPort"
if ($WithUi) {
    Write-Host "  React UI:  http://127.0.0.1:$UiPort"
}
Write-Host ""
Write-Host "Press Ctrl+C to stop services. Recent logs will stream below."
Write-Host ""

try {
    while ($true) {
        foreach ($job in $jobs) {
            Receive-Job $job
        }
        Start-Sleep -Seconds 2
    }
}
finally {
    Write-Host ""
    Write-Host "Stopping Aeris local services..."
    $jobs | Stop-Job -ErrorAction SilentlyContinue
    $jobs | Remove-Job -Force -ErrorAction SilentlyContinue
}
