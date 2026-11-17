"""LoRA fine-tune a small coder model on English -> PowerShell pairs, then merge to ./out/merged.
Usage: .venv\Scripts\python.exe train.py [--base Qwen/Qwen2.5-Coder-1.5B-Instruct] [--epochs 3]
Prompt format (must match ../ollama/Modelfile): plain ChatML, no system prompt."""
import argparse, json, math, pathlib, random, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, get_cosine_schedule_with_warmup
from peft import LoraConfig, get_peft_model

ROOT = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--base", default="Qwen/Qwen2.5-Coder-1.5B-Instruct")
ap.add_argument("--epochs", type=int, default=3)
ap.add_argument("--lr", type=float, default=2e-4)
ap.add_argument("--bs", type=int, default=16)
ap.add_argument("--rank", type=int, default=32)
ap.add_argument("--out", default=str(ROOT / "train" / "out"))
args = ap.parse_args()


def prompt(q):
    return f"<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n"


def load(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


R = random.Random(0)
train = load(ROOT / "data" / "train.jsonl")
dev = load(ROOT / "data" / "dev.jsonl")
R.shuffle(train)
print(f"train {len(train)}  dev {len(dev)}")

tok = AutoTokenizer.from_pretrained(args.base)
model = AutoModelForCausalLM.from_pretrained(args.base, dtype=torch.bfloat16, device_map="cuda")
model.gradient_checkpointing_enable()
model.enable_input_require_grads()
model = get_peft_model(model, LoraConfig(
    r=args.rank, lora_alpha=args.rank * 2, lora_dropout=0.05, task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
model.print_trainable_parameters()


def encode(ex):
    p = tok(prompt(ex["q"]), add_special_tokens=False)["input_ids"]
    a = tok(ex["cmd"] + "<|im_end|>\n", add_special_tokens=False)["input_ids"]
    return p + a, [-100] * len(p) + a


def batches(data, bs):
    for i in range(0, len(data), bs):
        enc = [encode(x) for x in data[i:i + bs]]
        L = max(len(e[0]) for e in enc)
        ids = torch.full((len(enc), L), tok.pad_token_id)
        lab = torch.full((len(enc), L), -100)
        att = torch.zeros((len(enc), L), dtype=torch.long)
        for j, (x, y) in enumerate(enc):
            ids[j, :len(x)] = torch.tensor(x); lab[j, :len(y)] = torch.tensor(y); att[j, :len(x)] = 1
        yield ids.cuda(), lab.cuda(), att.cuda()


@torch.no_grad()
def exact_match(data, n=120):
    model.eval(); hits = 0
    for ex in data[:n]:
        ids = tok(prompt(ex["q"]), return_tensors="pt", add_special_tokens=False).input_ids.cuda()
        out = model.generate(ids, max_new_tokens=120, do_sample=False, pad_token_id=tok.pad_token_id,
                             eos_token_id=tok.convert_tokens_to_ids("<|im_end|>"))
        got = tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True).strip()
        hits += got in (ex["accept"] if "accept" in ex else [ex["cmd"]])
    model.train()
    return hits / min(n, len(data))


opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr, weight_decay=0.0)
steps = args.epochs * math.ceil(len(train) / args.bs)
sched = get_cosine_schedule_with_warmup(opt, int(0.05 * steps), steps)
model.train(); step = 0; t0 = time.time()
for ep in range(args.epochs):
    R.shuffle(train)
    for ids, lab, att in batches(train, args.bs):
        loss = model(input_ids=ids, attention_mask=att, labels=lab).loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sched.step(); opt.zero_grad(); step += 1
        if step % 25 == 0:
            print(f"ep {ep} step {step}/{steps} loss {loss.item():.4f} {time.time() - t0:.0f}s", flush=True)
    print(f"== epoch {ep}: dev exact-match {exact_match(dev):.3f}", flush=True)

out = pathlib.Path(args.out)
merged = model.merge_and_unload()
merged.save_pretrained(out / "merged", safe_serialization=True)
tok.save_pretrained(out / "merged")
print("saved", out / "merged")
