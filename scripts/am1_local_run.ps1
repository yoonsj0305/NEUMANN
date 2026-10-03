param()

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root ".venv-am1\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Missing .venv-am1. Run AM1_LOCAL_SETUP.cmd first."
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Base = Join-Path $Root "_am1_local"
New-Item -ItemType Directory -Force -Path $Base | Out-Null
$Preflight = Join-Path $Base ("preflight_" + $Stamp + ".json")

Write-Host "=== NEUMANN AM1 local run ==="
Write-Host "Preflight: CUDA + >=14 GiB VRAM + BF16, no CPU fallback"
& $Python experiments/general_multiplier_local_preflight.py --output $Preflight
if ($LASTEXITCODE -ne 0) {
    throw "Preflight is not READY. No model inference was attempted."
}

$Head = "LOCAL_PACKAGE_NO_GIT_HEAD"
if (Get-Command git -ErrorAction SilentlyContinue) {
    try {
        $Tracked = (& git status --porcelain --untracked-files=no)
        if ($Tracked) {
            throw "Tracked files are modified. Use a clean checkout before the one-shot evidence run."
        }
        $Head = (& git rev-parse HEAD).Trim()
    } catch {
        throw $_
    }
}

$ResultDir = Join-Path $Base ("am1_" + $Stamp)
Write-Host "Evidence directory: $ResultDir"
if (-not $env:HF_TOKEN) {
    Write-Host "HF_TOKEN is not set. Cached/public access may still work; a gated download will fail closed."
}

$env:CUDA_VISIBLE_DEVICES = "0"
$env:PYTHONUTF8 = "1"

& $Python -m experiments.general_multiplier_first --directory $ResultDir --frozen-head $Head
$RunExit = $LASTEXITCODE

$ReplayPath = Join-Path $ResultDir "replay.json"
if ($RunExit -eq 0) {
    & $Python -m experiments.general_multiplier_evidence_replay --directory $ResultDir --output $ReplayPath
    $ReplayExit = $LASTEXITCODE
} else {
    $ReplayExit = 2
}

$Zip = $ResultDir + ".zip"
if (Test-Path $Zip) { Remove-Item $Zip -Force }
Compress-Archive -Path (Join-Path $ResultDir "*") -DestinationPath $Zip -CompressionLevel Optimal

$ReportPath = Join-Path $ResultDir "report.json"
if (Test-Path $ReportPath) {
    $Report = Get-Content $ReportPath -Raw | ConvertFrom-Json
    Write-Host ""
    Write-Host ("STATUS: " + $Report.status)
    Write-Host ("DECISION 2: " + $Report.decision_2.verdict)
    Write-Host ("NEXT: " + $Report.next)
}
Write-Host ("EVIDENCE ZIP: " + $Zip)

if ($RunExit -ne 0) {
    throw "AM1 ended INCOMPLETE. Preserve this evidence; only environment/measurement repair is allowed."
}
if ($ReplayExit -ne 0) {
    throw "AM1 completed but model-free evidence replay failed integrity validation."
}
