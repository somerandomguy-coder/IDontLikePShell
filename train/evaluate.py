"""Run the merged model on data/eval.jsonl (+ optional extra queries) with transformers and print outputs."""
import json, pathlib, sys, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = pathlib.Path(__file__).resolve().parent.parent
M = ROOT / "train" / "out" / "merged"
tok = AutoTokenizer.from_pretrained(M)
model = AutoModelForCausalLM.from_pretrained(M, dtype=torch.bfloat16, device_map="cuda").eval()
end = tok.convert_tokens_to_ids("<|im_end|>")

rows = [json.loads(l) for l in (ROOT / "data" / "eval.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
rows += [{"q": q, "accept": []} for q in sys.argv[1:]]
hits = 0
for r in rows:
    ids = tok(f"<|im_start|>user\n{r['q']}<|im_end|>\n<|im_start|>assistant\n", return_tensors="pt").input_ids.cuda()
    t = time.perf_counter()
    with torch.no_grad():
        out = model.generate(ids, max_new_tokens=120, do_sample=False, eos_token_id=end, pad_token_id=tok.pad_token_id)
    got = tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True).strip()
    ok = got in r["accept"]; hits += ok
    tag = "OK " if ok else ("?? " if not r["accept"] else "XX ")
    print(f"{tag}{(time.perf_counter()-t)*1000:5.0f}ms | {r['q']}\n      -> {got}")
print(f"exact {hits}/{sum(1 for r in rows if r['accept'])}")
