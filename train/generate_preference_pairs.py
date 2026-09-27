"""Generate preference pairs from `ratings.jsonl`.

Reads: ratings.jsonl lines of {timestamp,prompt,completion,rating,sender,bot}
Writes: train/preference_pairs.jsonl lines of {prompt,better,worse}

For each unique prompt, pairs all higher-rated completions against lower-rated completions.
"""
from pathlib import Path
import json
from collections import defaultdict

IN_FILE = Path('ratings.jsonl')
OUT_FILE = Path('train/preference_pairs.jsonl')

if not IN_FILE.exists():
    print(f"No ratings file found at {IN_FILE}; run the bot with ratings enabled to collect data.")
    raise SystemExit(1)

groups = defaultdict(list)
for line in IN_FILE.read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    obj = json.loads(line)
    prompt = obj.get('prompt','')
    groups[prompt].append(obj)

pairs = []
for prompt, items in groups.items():
    # sort by rating desc
    items_sorted = sorted(items, key=lambda x: x.get('rating',0), reverse=True)
    # create pairs
    for i in range(len(items_sorted)):
        for j in range(i+1, len(items_sorted)):
            hi = items_sorted[i]
            lo = items_sorted[j]
            if hi.get('rating',0) == lo.get('rating',0):
                continue
            pairs.append({
                'prompt': prompt,
                'better': hi.get('completion',''),
                'worse': lo.get('completion','')
            })

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with OUT_FILE.open('w', encoding='utf-8') as f:
    for p in pairs:
        f.write(json.dumps(p, ensure_ascii=False) + '\n')

print(f"Wrote {len(pairs)} preference pairs to {OUT_FILE}")
