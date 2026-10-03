param(
    [string]$Replay = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root ".venv-am1\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    if (Get-Command py -ErrorAction SilentlyContinue) { $Python = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $Python = "python" }
    else { throw "Python is required." }
}

if (-not $Replay) {
    $Candidates = Get-ChildItem -Path (Join-Path $Root "_am1_local") -Filter "replay.json" -Recurse -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending
    if ($Candidates -and $Candidates.Count -gt 0) {
        $Replay = $Candidates[0].FullName
    }
}

if ($Replay) {
    Write-Host ("Using Decision-2 replay: " + $Replay)
    & $Python -m experiments.decision3_readiness --d2-replay $Replay --output ".decision3_readiness.json"
} else {
    Write-Host "No Decision-2 replay found. This is expected before AM1 is run."
    & $Python -m experiments.decision3_readiness --output ".decision3_readiness.json"
}
Write-Host ""
Write-Host "No sealed Decision-3 dataset was opened."
