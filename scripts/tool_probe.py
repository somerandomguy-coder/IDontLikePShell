"""Ask the served nlsh model 2 questions per tool and print answers, to judge tool coverage by eye.
Usage: python scripts/tool_probe.py [model]  ->  writes data/tool_probe_<model>.txt"""
import json, sys, time, urllib.request, pathlib

MODEL = sys.argv[1] if len(sys.argv) > 1 else "nlsh"
Q = {
    "git": ["undo my last commit but keep the changes", "show which files changed in the last 3 commits"],
    "gh": ["list my open pull requests", "create a PR from this branch with title fix login"],
    "docker": ["list running containers", "remove all stopped containers"],
    "docker compose": ["start the compose stack in the background", "show logs of the api service and follow"],
    "kubectl": ["list pods in all namespaces", "get logs of pod web-1"],
    "podman": ["list podman images", "run alpine interactively with podman"],
    "uv": ["create a venv with uv", "add requests to my uv project", "run main.py with uv"],
    "pip": ["install packages from requirements.txt", "list outdated pip packages"],
    "pyenv": ["list python versions installed with pyenv", "set python 3.12 for this folder with pyenv"],
    "node/npm": ["install deps with npm", "run the dev script", "list global npm packages"],
    "pnpm": ["install deps with pnpm", "add zod with pnpm"],
    "cargo": ["build rust project in release mode", "run clippy on all targets"],
    "rustup": ["update rust toolchain", "add wasm target to rust"],
    "go": ["run all go tests verbosely", "tidy go modules"],
    "make": ["run the build target with make", "list make targets"],
    "cmake": ["configure cmake build in build folder release", "build the cmake project"],
    "jq": ["pretty print package.json", "get the version field from package.json with jq"],
    "curl": ["download https://example.com/a.zip", "send a POST with json body {\"a\":1} to localhost:8000/api"],
    "tar/xz": ["extract archive.tar.gz", "compress the logs folder into logs.tar.gz"],
    "openssl": ["generate a random 32 byte hex string with openssl", "show the certificate of google.com"],
    "ollama": ["list my ollama models", "pull llama3.2 with ollama", "which ollama models are loaded right now"],
    "winget": ["search winget for ffmpeg", "upgrade all winget packages"],
    "wsl": ["list wsl distros", "shut down wsl"],
    "code/zed": ["open this folder in vscode", "open notes.md in zed"],
    "gcloud": ["list gcloud projects", "copy file.csv to gs://my-bucket"],
    "fly": ["deploy with fly", "show fly app logs"],
    "firebase": ["deploy firebase hosting only", "start firebase emulators"],
    "tailscale": ["show tailscale status", "what's my tailscale ip"],
    "zoxide": ["jump to my projects folder with zoxide", "list zoxide entries"],
    "yt-dlp": ["download this youtube video as mp3 https://youtu.be/abc", "download best quality video from https://youtu.be/abc"],
    "pandoc": ["convert README.md to pdf with pandoc", "convert notes.docx to markdown"],
    "pdf (poppler)": ["extract text from report.pdf", "merge a.pdf and b.pdf into out.pdf"],
    "latexmk": ["compile main.tex to pdf", "clean latex build files"],
    "nvidia-smi": ["show gpu usage", "watch gpu memory every second"],
    "hf": ["download Qwen/Qwen2.5-0.5B from huggingface", "log in to huggingface"],
    "foundry": ["run forge tests", "get the eth balance of 0xabc with cast"],
    "mkcert": ["make a local https cert for localhost", "install mkcert root ca"],
    "sqlite-utils": ["list tables in data.db", "insert data.json into data.db table items"],
    "rg/fd misc": ["find files starting with gelato in this folder only", "files ending with _test.go", "search TODO only in the current folder not subfolders"],
}
out = []
for tool, qs in Q.items():
    out.append(f"## {tool}")
    for q in qs:
        body = json.dumps({"model": MODEL, "prompt": q, "stream": False, "options": {"temperature": 0}}).encode()
        t = time.perf_counter()
        r = json.load(urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:11434/api/generate", body, {"Content-Type": "application/json"})))
        out.append(f"  {q}\n    -> {r['response'].strip()}   ({(time.perf_counter()-t)*1000:.0f}ms)")
p = pathlib.Path(__file__).resolve().parent.parent / "data" / f"tool_probe_{MODEL.replace(':', '_')}.txt"
p.write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
