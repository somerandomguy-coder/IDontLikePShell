# Training data style guide (canonical command style)

Each example is one JSON line: `{"q": "<English request>", "cmd": "<one PowerShell 5.1 command line>"}`.
The model learns ONE consistent style, so follow these rules exactly.

## Target shell
- Windows PowerShell 5.1. No `&&` / `||` (use `;` or `if ($?) { ... }`), no ternary, no `??`.
- One line. Multiple statements are joined with `; `.
- `curl` is an alias for Invoke-WebRequest in 5.1: write `curl.exe` when the user means curl.
- Never output explanations, markdown or backticks.

## Tools to prefer
- Finding files/folders by NAME: `fd`. Never `Get-ChildItem -Recurse` / `dir /s`.
  - order: `fd [flags] 'pattern' [path...]`; with no name pattern but a path: `fd [flags] . path`
  - `-t f` files, `-t d` dirs, `-t e` empty, `-e py` extension (repeatable), `-H` hidden, `-I` include gitignored,
    `-d 2` max depth, `-g '*.log'` glob instead of regex, `-p` match full path, `-i` ignore case, `-s` case-sensitive,
    `--changed-within 2h` / `--changed-before 30d`, `-S +100m` / `-S -1k` size, `-E node_modules` exclude,
    `-x cmd` run per result, `-X cmd` run once with all results (real executables only, never cmdlets: pipe to cmdlets instead), `-a` absolute paths, `-1` first result only, `--max-results 5`.
  - exact name: `'^name$'`. "contains X": `'X'`.
- Searching TEXT inside files: `rg`. Never `Select-String` / `findstr`.
  - order: `rg [flags] 'pattern' [path...]`
  - `-i` ignore case, `-w` whole word, `-F` literal, `-l` file names only, `-L`... (don't use), `-c` count per file,
    `--count-matches`, `-v` invert, `-n` (default, don't add), `-C 3` context, `-A 2`/`-B 2`, `-g '*.ts'` glob,
    `-g '!*.min.js'` exclude, `-t py` type, `-T js` exclude type, `--hidden`, `-uu` no ignore, `-o` only matching,
    `-r 'repl'` replace in output, `--files` list files rg would search, `-m 1` max per file, `-U` multiline, `--sort path`.
- Counting anything: `(X | Measure-Object).Count`. Lines in files: `(Get-Content f | Measure-Object -Line).Lines`.
- Reusing values: assign to a short variable `$n = ...; next $n`.
- Everything else uses idiomatic PowerShell cmdlets with full names (Get-ChildItem not gci, Where-Object not ?, ForEach-Object not %, Select-Object not select).
  Exception: in `ForEach-Object { ... }` use `$_`.
- git commands are plain `git ...`.

## Named tools and installed CLIs
- If the user names a tool ("with jq", "using uv", "via gh"), the command MUST use that tool.
- Ecosystem defaults when the request implies them: GitHub PRs/issues/repos -> `gh`; Python envs/deps -> `uv`
  (only use pip/python -m venv if the user says pip/venv); k8s -> `kubectl`; YouTube/video download -> `yt-dlp`;
  doc conversion -> `pandoc`; PDF text/merge/split -> poppler (`pdftotext`, `pdfunite`, `pdfseparate`, `pdfinfo`);
  LaTeX build -> `latexmk`; GPU -> `nvidia-smi`; HF models -> `hf`; local TLS certs -> `mkcert`; jump to dir -> `z` (zoxide).
- curl means `curl.exe`; a plain "download URL" may use `Invoke-WebRequest URL -OutFile name`.
- fd name anchors: "starts with X" -> `'^X'`, "ends with X" -> `'X$'` (escape dots: `'_test\.go$'`), "this folder only / not subfolders" -> `-d 1`
  (flags first: `fd -t f -d 1 '^gelato'`)
  (rg: `-d 1` too, i.e. `--max-depth 1`).

## Quoting
- Patterns/regex/globs: single quotes. `rg 'foo bar'`, `fd -g '*.log'`.
- Strings needing variable expansion: double quotes `"$n"`.
- Paths: bare unless they contain spaces, then single quotes. Use the path words the user said; default to current dir (no path).
- Use the user's literal names/values exactly.

## Safety
- Never add `-Force`, `-Recurse` deletion, or `Remove-Item` unless the user asks to delete/remove.
- If the user asks to delete, do it plainly (`fd -t f -e tmp | Remove-Item` or `Remove-Item ...`) — the human reviews the line before Enter.

## Phrasing variety (for `q`)
Write like a tired developer typing fast: lowercase, typos sometimes, terse ("py files with todo"), casual ("where did i put that config.yaml"),
Linux-brained ("grep -r foo but only in ts", "ls -la", "du -sh", "which node", "tail -f log", "ps aux | grep node", "kill -9 1234", "cat file | wc -l", "touch x", "export FOO=bar").
Linux-style requests must be translated to the PowerShell/fd/rg equivalent.
