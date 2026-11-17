# Registers the fine-tuned model with Ollama and hooks nlsh into your PowerShell profile.
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

if (Test-Path "$root\train\out\nlsh-q8_0.gguf") {
    Push-Location "$root\ollama"
    ollama create nlsh -f Modelfile   # GGUF is already q8_0, so no --quantize
    Pop-Location
} else {
    Write-Warning 'No fine-tuned model yet (train\out\nlsh-q8_0.gguf missing): nlsh will use the few-shot fallback model.'
}

if (-not (Get-Command fd -ErrorAction SilentlyContinue)) {
    Write-Warning 'fd is not installed. Install it with: winget install sharkdp.fd'
}

$line = "Import-Module '$root\nlsh\nlsh.psm1'; Enable-Nlsh"
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Force $PROFILE | Out-Null }
if (-not (Select-String -Path $PROFILE -SimpleMatch "$root\nlsh\nlsh.psm1" -Quiet)) {
    Add-Content -Path $PROFILE -Value "`n$line"
    Write-Host "Added to $PROFILE. Open a new terminal and try: ai find big log files"
} else {
    Write-Host 'Already in your profile.'
}
