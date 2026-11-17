"""Quick accuracy/latency probe of candidate models against eval set via Ollama."""
import json, sys, time, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SYSTEM = (ROOT / "prompt" / "system.txt").read_text(encoding="utf-8")
SHOTS = [json.loads(l) for l in (ROOT / "prompt" / "fewshot.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
EVAL = [json.loads(l) for f in ("eval.jsonl", "eval_tools.jsonl")
        for l in (ROOT / "data" / f).read_text(encoding="utf-8").splitlines() if l.strip()]


def ask(model, q):
    if model.startswith("nlsh"):  # fine-tuned: template lives in the Modelfile
        body = json.dumps({"model": model, "prompt": q, "stream": False, "keep_alive": "30m",
                           "options": {"temperature": 0}}).encode()
        t = time.perf_counter()
        r = json.load(urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:11434/api/generate", body, {"Content-Type": "application/json"})))
        return r["response"].strip(), time.perf_counter() - t
    msgs = [{"role": "system", "content": SYSTEM}]
    for s in SHOTS:
        msgs += [{"role": "user", "content": s["q"]}, {"role": "assistant", "content": s["cmd"]}]
    msgs.append({"role": "user", "content": q})
    body = json.dumps({"model": model, "messages": msgs, "stream": False, "think": False,
                       "keep_alive": "30m",
                       "options": {"temperature": 0, "num_predict": 120, "num_ctx": 4096}}).encode()
    t = time.perf_counter()
    for attempt in range(3):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:11434/api/chat", body, {"Content-Type": "application/json"})))
            break
        except Exception as e:
            if attempt == 2:
                return f"<error {e}>", time.perf_counter() - t
            time.sleep(1)
    return r["message"]["content"].strip(), time.perf_counter() - t


for model in sys.argv[1:]:
    ask(model, "list files")  # warm up
    hits, total_t = 0, 0.0
    for ex in EVAL:
        out, dt = ask(model, ex["q"])
        total_t += dt
        ok = out in ex["accept"]
        hits += ok
        print(f"{'OK ' if ok else 'XX '} {dt*1000:5.0f}ms | {ex['q']}\n      -> {out}" + ("" if ok else f"\n      want {ex['accept'][0]}"))
    print(f"== {model}: {hits}/{len(EVAL)} exact, avg {total_t/len(EVAL)*1000:.0f} ms\n")
