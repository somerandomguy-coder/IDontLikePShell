# nlsh: English to PowerShell, at the prompt

```
PS> ai where did i put docker-compose.yml                  <- press Enter
PS> ai where did i put docker-compose.yml   ⠋ thinking 0.1s <- spinner while it runs
PS> fd '^docker-compose\.yml$'                              <- review/edit, Enter runs it
```

- `ai <english>` + **Enter** replaces the line with a PowerShell command (using `fd`/`rg` instead of
  `Get-ChildItem -Recurse`/`Select-String`). Nothing runs until you press Enter a second time.
- Don't like the answer? Press **Up** twice to get your `ai ...` line back and Enter again: asking the same thing
  twice in a row gives a different answer.
- Quotes, pipes and apostrophes in your English are fine (`ai ps aux | grep node`, `ai what's my ip`):
  the line is never parsed by PowerShell.
- If Ollama isn't running you get a beep, your line stays, and the window title says why.
- In scripts (no interactive prompt), `ai find big logs` just prints the command.

## What it knows

fd, rg and PowerShell built-ins, plus about 40 CLIs: git, gh, docker, kubectl, uv, npm/pnpm, cargo, go, ollama, gcloud,
yt-dlp, pandoc, jq, and more. The full list, with known weak spots, is in [SUPPORTED_TOOLS.md](SUPPORTED_TOOLS.md).
Held-out benchmark: **27/36 exact matches, 87 ms average**.

To teach it your own tools, see the [fine-tuning guide](docs/index.html). If you're an AI agent, see [AGENTS.md](AGENTS.md).

## How it works

- `nlsh/nlsh.psm1` wraps PSReadLine's Enter key. Lines starting with `ai ` are sent to Ollama on
  `127.0.0.1:11434` over a reused HttpClient, with a spinner drawn in the buffer while it waits; the reply
  replaces the line. Every other line is accepted as normal. There's no extra process and no Python at runtime.
  Use `Enable-Nlsh -Trigger '??'` to change the prefix word.
- The model is **Qwen2.5-Coder-1.5B**, LoRA fine-tuned on this repo's data and served by Ollama as `nlsh`
  (q8_0, about 1.6 GB). It stays loaded (`keep_alive = -1`), so each request only pays for generation.
- If the `nlsh` model isn't present, the module falls back to `qwen3.5:2b` with the few-shot prompt in `prompt/`.

## Install

The trained weights (1.6 GB) aren't in git, so you build them once on your own GPU (about 20 minutes):

```powershell
winget install sharkdp.fd   # the model's file-finding commands use fd
.\retrain.ps1               # training env + fine-tune + GGUF + `ollama create nlsh`
.\install.ps1               # adds one line to $PROFILE; open a new terminal and type `ai ...`
```

No NVIDIA GPU? Run just `.\install.ps1`: the module then falls back to `qwen3.5:2b` with a few-shot prompt.
That fallback is slower and much less accurate (`ollama pull qwen3.5:2b` first).

## Teach it your own tools

1. Add `{"q": "...", "cmd": "..."}` lines to a new file in `data/hand/`, following [data/STYLE.md](data/STYLE.md).
   20-40 examples per tool is enough. An AI assistant can write them: point it at [AGENTS.md](AGENTS.md).
2. `.\retrain.ps1`. It rebuilds the dataset, fine-tunes, exports, re-registers the model, and prints the benchmark.

The full walkthrough is in [docs/index.html](docs/index.html).

## Layout

```
nlsh/nlsh.psm1            runtime: Enter hook, spinner, HTTP client to Ollama
data/STYLE.md             the canonical command style every example follows
data/hand/*.jsonl         ~2,150 hand-written pairs (fd/rg, pipelines, Windows, ~40 CLIs)
data/gen/templates.jsonl  ~1,300 generated pairs that vary names, sizes, times and paths
data/eval*.jsonl          held-out benchmark (never trained on)
scripts/                  data generation, dataset build, probes
train/train.py            LoRA fine-tune + merge; train/requirements.txt pins the stack
ollama/Modelfile          prompt template for the served model
retrain.ps1, install.ps1  one-command train and install
docs/index.html           fine-tuning guide (humans);  AGENTS.md (AI agents)
```
