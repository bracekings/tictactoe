"""Generate SFT training data from ratings.jsonl using persona_examples.txt.

Produces: train/train_from_ratings.jsonl where each line is {"prompt":..., "completion":...}
We include persona_examples.txt at the top of each prompt as a system-like block to teach voice.
By default, we select completions with rating >= 9 (configurable).
"""
from pathlib import Path
import json

RATINGS = Path('ratings.jsonl')
PERSONA = Path('persona_examples.txt')
OUT = Path('train/train_from_ratings.jsonl')
MIN_RATING = 9

persona_text = PERSONA.read_text(encoding='utf-8').strip() if PERSONA.exists() else ''

if not RATINGS.exists():
    print(f"No ratings file found at {RATINGS}; collect ratings first.")
    raise SystemExit(1)

records = []
for line in RATINGS.read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    obj = json.loads(line)
    r = int(obj.get('rating',0))
    if r >= MIN_RATING:
        prompt = obj.get('prompt','')
        completion = obj.get('completion','')
        if persona_text:
            augmented_prompt = f"SYSTEM: Follow this style exactly:\n{persona_text}\n\nUSER: {prompt}"
        else:
            augmented_prompt = prompt
        records.append({'prompt': augmented_prompt, 'completion': completion})

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open('w', encoding='utf-8') as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

print(f"Wrote {len(records)} SFT records to {OUT}")
