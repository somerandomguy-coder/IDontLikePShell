"""Merge hand-written + generated data into data/train.jsonl and data/dev.jsonl.
Hand data is upsampled x2 (it carries the phrasing variety); 8% of it is held out for dev,
plus the fixed benchmark in data/eval.jsonl."""
import json, pathlib, random

D = pathlib.Path(__file__).resolve().parent.parent / "data"
R = random.Random(1)


def load(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


bench = load(D / "eval.jsonl") + load(D / "eval_tools.jsonl")
banned = {b["q"].lower() for b in bench}
hand = [x for p in sorted((D / "hand").glob("*.jsonl")) for x in load(p)]
gen = [x for p in sorted((D / "gen").glob("*.jsonl")) for x in load(p)]


def clean(xs):
    seen, out = set(), []
    for x in xs:
        k = x["q"].strip().lower()
        if k in seen or k in banned or not x["cmd"].strip() or "\n" in x["cmd"]:
            continue
        seen.add(k); out.append({"q": x["q"].strip(), "cmd": x["cmd"].strip()})
    return out


hand, gen = clean(hand), clean(gen)
R.shuffle(hand)
k = max(20, int(0.08 * len(hand)))
dev_hand, train_hand = hand[:k], hand[k:]
gen = [g for g in gen if g["q"].lower() not in {h["q"].lower() for h in dev_hand}]
train = train_hand * 2 + gen
R.shuffle(train)
dev = bench + dev_hand
(D / "train.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in train) + "\n", encoding="utf-8")
(D / "dev.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in dev) + "\n", encoding="utf-8")
print(f"hand {len(hand)} (train {len(train_hand)} x2, dev {len(dev_hand)}), gen {len(gen)} -> train {len(train)}, dev {len(dev)}")
