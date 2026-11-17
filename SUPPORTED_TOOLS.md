# Supported tools

What the shipped `nlsh` model (Qwen2.5-Coder-1.5B + LoRA, trained 2026-11-18 on ~2,150 hand-written and
~1,300 generated examples) was trained on, and how well it does. Status comes from `scripts/tool_probe.py`
(2-3 unseen questions per tool) and the held-out benchmark (`scripts/probe.py`: **27/36 exact, 87 ms average**).

- **Good:** every probe answer was correct.
- **Mostly:** usually right, with a known weak spot (listed).
- **Not trained:** anything else. The model may still guess a reasonable command, or it may invent one.

Want a tool added or a weak spot fixed? See [AGENTS.md](AGENTS.md) or [docs/index.html](docs/index.html).

## Files and text (the core)

| Tool | Status | Notes |
| --- | --- | --- |
| `fd` | Good | by name, extension, type, size, time, depth; "starts with" `'^x'`, "ends with" `'x$'`, "this folder only" `-d 1`. Requires `winget install sharkdp.fd`. |
| `rg` (ripgrep) | Good | case/word/literal, file names only, counts, context, globs/types, `-d 1`, replace, multiline |
| PowerShell built-ins | Good | processes, services, ports, network, env vars/PATH, clipboard, archives (zip), hashes, file ops, sizes |
| Multi-step pipelines | Mostly | count-then-search, fd → rg, rg → cmdlets, `$var` reuse, `if ($?)`. Long 3+ step chains are less reliable. |

## Dev tools

| Tool | Status | Notes |
| --- | --- | --- |
| `git` | Good | reset/stash/rebase/cherry-pick/bisect/worktree/tags/blame/reflog, log filters |
| `gh` | Good | PRs, issues, repos, runs, checks |
| `docker`, `docker compose` | Good | ps/prune/exec/logs -f/build/up -d/down -v |
| `kubectl` | Good | pods, logs, describe, exec, port-forward, apply, rollout, contexts |
| `podman` | Good | |
| `uv` / `uvx` | Good | default for Python envs and dependencies (venv, add, sync, run, pip install -r, python install, tool run) |
| `pip` | Good | only when you say "pip" |
| `pyenv` | Mostly | weak spot: mixes up `versions` / `install --list` and `local` / `shell` |
| `node`, `npm`, `npx`, `pnpm` | Good | |
| `cargo`, `rustup` | Good | |
| `go` | Good | |
| `make` | Mostly | weak spot: "list targets" (there is no built-in flag; it answers `make -n`) |
| `cmake`, `ctest` | Good | |
| `forge`, `cast`, `anvil` (Foundry) | Good | |
| `hf` (Hugging Face CLI) | Good | download, auth, upload, cache |
| `ollama` | Good | list, ps, pull, run, rm, show, create |
| `nvidia-smi` | Mostly | weak spot: "watch every N seconds" (should be `-l N`) |
| `code`, `zed` | Good | sometimes invents a folder for a file you didn't give a path for |

## Cloud and network

| Tool | Status | Notes |
| --- | --- | --- |
| `gcloud`, `gsutil`, `bq` | Good | |
| `fly` | Good | |
| `firebase` | Good | |
| `tailscale` | Good | |
| `curl.exe` | Good | GET/POST JSON/headers. A plain "download URL" gives `Invoke-WebRequest -OutFile`. |
| `openssl` | Good | rand, view a site's certificate, x509 |
| `mkcert` | Mostly | making certs is fine; weak spot: "install the root CA" (should be `mkcert -install`) |
| `winget`, `wsl` | Good | |

## Documents and data

| Tool | Status | Notes |
| --- | --- | --- |
| `jq` | Mostly | field/filter/select is fine; weak spot: "pretty print file.json" |
| `yt-dlp` | Good | |
| `pandoc` | Good | |
| `pdftotext`, `pdfunite`, `pdfseparate`, `pdfinfo`, `pdftoppm` (poppler) | Good | |
| `latexmk`, `pdflatex`, `xelatex` | Good | |
| `sqlite-utils` | Good | |
| `tar`, `xz`, `bzip2` | Mostly | extracting is fine; weak spot: creating `.tar.gz` (it answers `Compress-Archive`, which makes a zip) |
| `zoxide` | Mostly | answers `zoxide query x` instead of `z x`. `z` also needs `zoxide init powershell` in your profile. |

## Installed but not trained

Everything else on this machine, for example `astro`, `arx`, `gitk`/`tig`, `scalar`, `usbipd`, `unsloth`, `chroma`,
CUDA tools beyond `nvcc --version`, Nsight, and the MiKTeX utilities other than `latexmk`/`pdflatex`/`xelatex`.
Add examples to `data/hand/` to teach any of them.
