param(
    [ValidateSet("cu126","cu130","cu132")]
    [string]$CudaWheel = "cu126"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Venv = Join-Path $Root ".venv-am1"
$VenvPython = Join-Path $Venv "Scripts\python.exe"

function Invoke-BootstrapPython {
    param([string[]]$Arguments)
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 @Arguments
        return
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python @Arguments
        return
    }
    throw "Python 3.12 is required. Install Python, then run this script again."
}

Write-Host "=== NEUMANN AM1 local zero-cost setup ==="
Write-Host "1/4 Hardware-only preflight"
Invoke-BootstrapPython @(
    "experiments/general_multiplier_local_preflight.py",
    "--allow-runtime-missing"
)
if ($LASTEXITCODE -ne 0) {
    throw "Hardware preflight failed. No model download or inference was attempted."
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "2/4 Creating isolated .venv-am1"
    Invoke-BootstrapPython @("-m","venv",$Venv)
    if ($LASTEXITCODE -ne 0) { throw "venv creation failed" }
} else {
    Write-Host "2/4 Reusing existing .venv-am1"
}

Write-Host "3/4 Installing frozen AM1 runtime"
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }

$TorchIndex = "https://download.pytorch.org/whl/$CudaWheel"
& $VenvPython -m pip install "torch==2.14.0" "torchvision==0.29.0" --index-url $TorchIndex
if ($LASTEXITCODE -ne 0) {
    throw "CUDA PyTorch install failed. Try a different -CudaWheel only as an environment repair; do not change AM1 model/tasks/gate."
}

& $VenvPython -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "NEUMANN editable install failed" }

& $VenvPython -m pip install "transformers==5.10.1" "huggingface_hub>=0.35" "safetensors>=0.4" "pillow>=10"
if ($LASTEXITCODE -ne 0) { throw "AM1 model dependency install failed" }

Write-Host "4/4 Full CUDA/BF16 preflight"
& $VenvPython experiments/general_multiplier_local_preflight.py --output ".am1_local_preflight.json"
if ($LASTEXITCODE -ne 0) {
    throw "Runtime preflight failed. No AM1 inference was attempted."
}

Write-Host ""
Write-Host "READY. Setup changed no scientific threshold, task, model revision, or precision."
Write-Host "Next: run AM1_LOCAL_RUN.cmd"
