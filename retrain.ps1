# One command: data -> fine-tune -> GGUF -> Ollama model `nlsh`.
#   .\retrain.ps1                       # defaults
#   .\retrain.ps1 -Base Qwen/Qwen2.5-Coder-0.5B-Instruct -Epochs 3 -Name nlsh-small
param(
    [string]$Base = 'Qwen/Qwen2.5-Coder-1.5B-Instruct',
    [int]$Epochs = 3,
    [string]$Name = 'nlsh',
    [string]$OutType = 'q8_0',         # q8_0 (best), f16, or bf16
    [int]$BatchSize = 16               # lower to 8 if CUDA runs out of memory
)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$py = "$root\train\.venv\Scripts\python.exe"
$env:PYTHONUTF8 = '1'

function Step($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }
function Check { if ($LASTEXITCODE) { throw "step failed (exit $LASTEXITCODE)" } }

if (-not (Test-Path $py)) {
    Step 'creating training venv (one time, ~3 GB download)'
    uv venv --python 3.12 "$root\train\.venv"; Check
    uv pip install --python $py torch --index-url https://download.pytorch.org/whl/cu128; Check
    uv pip install --python $py -r "$root\train\requirements.txt"; Check
}
if (-not (Test-Path "$root\train\llama.cpp\convert_hf_to_gguf.py")) {
    Step 'fetching llama.cpp (only its GGUF converter is used)'
    git clone --depth 1 https://github.com/ggml-org/llama.cpp "$root\train\llama.cpp"; Check
}

Step 'building dataset'
python "$root\scripts\gen_templates.py"; Check
python "$root\scripts\build_dataset.py"; Check

Step "fine-tuning $Base"
& $py "$root\train\train.py" --base $Base --epochs $Epochs --bs $BatchSize; Check

Step 'converting to GGUF'
# The converter expects the original tokenizer files; fine-tuning doesn't change them.
$snap = & $py -c "from huggingface_hub import snapshot_download as s; print(s('$Base', allow_patterns=['tokenizer*','vocab.json','merges.txt']))"
foreach ($f in 'tokenizer_config.json', 'tokenizer.json', 'vocab.json', 'merges.txt') {
    if (Test-Path "$snap\$f") { Copy-Item "$snap\$f" "$root\train\out\merged\$f" -Force }
}
& $py "$root\train\llama.cpp\convert_hf_to_gguf.py" "$root\train\out\merged" --outtype $OutType --outfile "$root\train\out\nlsh-q8_0.gguf"; Check

Step "registering Ollama model '$Name'"
Push-Location "$root\ollama"; ollama create $Name -f Modelfile; Pop-Location; Check

Step 'benchmark'
python "$root\scripts\probe.py" $Name
