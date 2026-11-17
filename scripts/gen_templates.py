"""Programmatic augmentation: many slot-filled fd/rg/count examples so the model learns
to copy names, extensions, paths, sizes and time windows verbatim (argument grounding).
Hand-written data in data/hand/ carries the phrasing variety; this file carries value variety."""
import json, random, pathlib

R = random.Random(7)
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "gen" / "templates.jsonl"

EXTS = ["py", "js", "ts", "tsx", "go", "rs", "cs", "java", "md", "json", "yaml", "yml", "toml", "log",
        "txt", "csv", "sql", "html", "css", "ps1", "sh", "cpp", "h", "pdf", "png", "jpg", "mp4", "zip", "xml", "ipynb"]
EXT_WORD = {"py": ["python", "py"], "js": ["javascript", "js"], "ts": ["typescript", "ts"], "rs": ["rust", "rs"],
            "cs": ["c#", "cs"], "go": ["go"], "md": ["markdown", "md"], "ps1": ["powershell", "ps1"],
            "cpp": ["c++", "cpp"], "ipynb": ["notebook", "jupyter notebook"]}
DIRS = ["src", "lib", "app", "tests", "docs", "scripts", "config", "build", "dist", "logs", "data", "api",
        "components", "utils", "packages", "server", "client", "infra", "notebooks", "assets", "bin", "migrations"]
NAMES = ["config", "utils", "main", "index", "README", "Dockerfile", "settings", "helpers", "auth", "models",
         "routes", "schema", "backup", "invoice", "report", "notes", "todo", "server", "client", "test", "cache",
         "temp", "old", "draft", "env", "secrets", "package", "Makefile", "docker-compose", "requirements"]
WORDS = ["TODO", "FIXME", "password", "api_key", "localhost", "console.log", "print(", "import torch", "useState",
         "deprecated", "async def", "SELECT", "http://", "Exception", "panic!", "unwrap()", "TODO(nam)", "debugger",
         "connectionString", "DATABASE_URL", "error", "warning", "fetch(", "assert", "lambda", "XXX", "HACK",
         "version", "localhost:8080", "secret", "token", "retry"]
SIZES = [("1m", "1mb", "1 MB"), ("10m", "10mb", "10 megs"), ("50m", "50MB", "50 mb"), ("100m", "100mb", "100 megabytes"),
         ("500m", "500mb", "half a gig"), ("1g", "1gb", "1 gig"), ("5g", "5GB", "5 gigs"), ("100k", "100kb", "100 KB")]
TIMES = [("1h", ["last hour", "past hour", "the last 1h"]), ("2h", ["last 2 hours", "past two hours"]),
         ("1d", ["today", "last 24 hours", "past day"]), ("2d", ["last 2 days", "since yesterday"]),
         ("1w", ["this week", "last week", "past 7 days"]), ("30d", ["last month", "past 30 days"]),
         ("10min", ["last 10 minutes", "past 10 min"])]


def q(s):
    return "'" + s.replace("'", "''") + "'"


def regex_lit(s):
    import re
    return re.escape(s).replace("\\ ", " ").replace("\\-", "-")


def ew(e):
    return R.choice(EXT_WORD.get(e, [e, "." + e]))


def path_suffix():
    if R.random() < 0.45:
        d = R.choice(DIRS)
        return d, R.choice([f" in {d}", f" under {d}", f" inside {d}", f" in the {d} folder", f" from {d}"])
    return None, R.choice(["", "", " here", " in this folder", " recursively"])


ex = []


def add(query, cmd):
    if R.random() < 0.3:
        query = query.lower()
    ex.append({"q": query, "cmd": cmd})


for _ in range(260):  # files by extension
    e = R.choice(EXTS); d, ps = path_suffix()
    add(R.choice([f"find all {ew(e)} files{ps}", f"list {ew(e)} files{ps}", f"where are the .{e} files{ps}",
                  f"show me every {ew(e)} file{ps}", f"all *.{e}{ps}", f"find -name '*.{e}'{ps}"]),
        f"fd -t f -e {e}" + (f" . {d}" if d else ""))

for _ in range(200):  # by name
    n = R.choice(NAMES); d, ps = path_suffix(); kind = R.choice(["f", "d"])
    noun = "file" if kind == "f" else R.choice(["folder", "directory", "dir"])
    exact = R.random() < 0.5
    pat = f"^{regex_lit(n)}$" if exact else regex_lit(n)
    phr = ([f"find the {noun} named {n}{ps}", f"where is the {n} {noun}{ps}", f"locate {noun} called {n}{ps}"] if exact
           else [f"{noun}s with {n} in the name{ps}", f"find {noun}s containing {n}{ps}", f"any {noun} matching {n}{ps}"])
    add(R.choice(phr), f"fd -t {kind} {q(pat)}" + (f" {d}" if d else ""))

for _ in range(120):  # size
    s, w1, w2 = R.choice(SIZES); big = R.random() < 0.7; e = R.choice([None, None] + EXTS[:12])
    what = f"{ew(e)} files" if e else "files"
    add(R.choice([f"{what} {'bigger' if big else 'smaller'} than {w1}", f"{what} {'over' if big else 'under'} {w2}",
                  f"find {'large' if big else 'small'} {what} > {w1}" if big else f"{what} less than {w1}"]),
        f"fd -t f{' -e ' + e if e else ''} -S {'+' if big else '-'}{s}")

for _ in range(140):  # time
    t, words = R.choice(TIMES); e = R.choice([None, None] + EXTS[:14]); d, ps = path_suffix()
    what = f"{ew(e)} files" if e else "files"
    add(R.choice([f"{what} modified {R.choice(words)}{ps}", f"{what} changed {R.choice(words)}{ps}",
                  f"what {what} did i touch {R.choice(words)}{ps}", f"recently edited {what} ({R.choice(words)}){ps}"]),
        f"fd -t f{' -e ' + e if e else ''} --changed-within {t}" + (f" . {d}" if d else ""))

for _ in range(320):  # rg search
    w = R.choice(WORDS); e = R.choice([None, None, None] + EXTS[:16]); d, ps = path_suffix()
    flags = []
    mode = R.choice(["plain", "plain", "i", "l", "c", "w", "F"])
    if any(c in w for c in "().*+?[]{}|\\^$") and mode != "F":
        mode = "F"
    phrase = {"plain": [f"search for {w}", f"grep {w}", f"find {w}", f"where is {w} used", f"look for '{w}'"],
              "i": [f"search {w} case insensitive", f"grep -i {w}", f"find {w} ignoring case"],
              "l": [f"which files contain {w}", f"files that mention {w}", f"just the filenames with {w}", f"grep -l {w}"],
              "c": [f"count {w} per file", f"how many times does {w} appear in each file", f"grep -c {w}"],
              "w": [f"search whole word {w}", f"find {w} as a whole word", f"grep -w {w}"],
              "F": [f"search literal {w}", f"find the exact text {w}", f"grep -F '{w}'", f"search for {w}"]}[mode]
    if mode != "plain":
        flags.append("-" + mode)
    tail = f" in {ew(e)} files" if e else ""
    if e:
        flags.append(R.choice([f"-t {e}" if e in ("py", "js", "ts", "go", "rust", "cs", "java", "md", "json", "yaml", "toml", "sql", "html", "css", "cpp", "h") else f"-g '*.{e}'", f"-g '*.{e}'"]))
    add(R.choice(phrase) + tail + ps,
        "rg " + " ".join(f for f in flags if f) + (" " if flags else "") + q(w) + (f" {d}" if d else ""))

for _ in range(160):  # counting
    e = R.choice(EXTS); d, ps = path_suffix(); w = R.choice(WORDS)
    choice = R.randrange(3)
    if choice == 0:
        add(R.choice([f"how many {ew(e)} files are there{ps}", f"count {ew(e)} files{ps}", f"number of .{e} files{ps}"]),
            f"(fd -t f -e {e}" + (f" . {d}" if d else "") + " | Measure-Object).Count")
    elif choice == 1:
        n = R.choice(NAMES)
        add(R.choice([f"how many folders named {n}{ps}", f"count dirs called {n}{ps}"]),
            f"(fd -t d {q('^' + regex_lit(n) + '$')}" + (f" {d}" if d else "") + " | Measure-Object).Count")
    else:
        add(R.choice([f"how many files contain {w}{ps}", f"count files mentioning {w}{ps}", f"grep -l {w} | wc -l{ps}"]),
            f"(rg -l -F {q(w)}" + (f" {d}" if d else "") + " | Measure-Object).Count")

for _ in range(120):  # count then reuse
    n = R.choice(NAMES); d2 = R.choice(DIRS); kind = R.choice(["f", "d"])
    noun = "files" if kind == "f" else R.choice(["folders", "dirs", "directories"])
    add(R.choice([f"count {noun} with {n} in the name then search that number in {d2}",
                  f"get the number of {noun} matching {n} and grep it inside {d2}",
                  f"how many {noun} match {n}? then find that count in the {d2} folder"]),
        f"$n = (fd -t {kind} {q(regex_lit(n))} | Measure-Object).Count; rg -F \"$n\" {d2}")

seen, uniq = set(), []
for x in ex:
    if x["q"] not in seen:
        seen.add(x["q"]); uniq.append(x)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in uniq) + "\n", encoding="utf-8")
print(len(uniq), "examples ->", OUT)
