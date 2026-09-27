#!/usr/bin/env python3
"""clean_anonymize.py

Conservative anonymizer for JSONL training data. Replaces emails, phones, SSNs, long numbers,
and any names listed in `anonymize_names.txt` with placeholders.

Usage:
    python train/clean_anonymize.py --input train/dataset_example.jsonl --output train/cleaned_train.jsonl

If `--names` is provided, it's a file with one name per line to replace with <NAME>.
"""
import argparse
import re
import json
from pathlib import Path

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{6,}\d")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
LONG_NUM_RE = re.compile(r"\b\d{6,}\b")


def load_names(path: Path):
    if not path or not path.exists():
        return []
    return [l.strip() for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]


def anonymize_text(s: str, names):
    if not s:
        return s
    t = s
    t = EMAIL_RE.sub('<EMAIL>', t)
    t = SSN_RE.sub('<REDACTED_SSN>', t)
    t = PHONE_RE.sub('<PHONE>', t)
    t = LONG_NUM_RE.sub('<NUMBER>', t)
    # Replace listed names (case-insensitive)
    for name in names:
        if not name:
            continue
        # word-boundary replace, preserve case by replacing exact matches only
        t = re.sub(rf"\b{re.escape(name)}\b", '<NAME>', t)
        t = re.sub(rf"\b{re.escape(name.capitalize())}\b", '<NAME>', t)
        t = re.sub(rf"\b{re.escape(name.upper())}\b", '<NAME>', t)
    return t


def process(in_path: Path, out_path: Path, names_path: Path | None = None):
    names = load_names(names_path) if names_path else []
    count = 0
    with in_path.open('r', encoding='utf-8') as inf, out_path.open('w', encoding='utf-8') as outf:
        for line in inf:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                # if line not JSON, write as-is
                outf.write(line)
                continue
            # anonymize known string fields
            for k in ('prompt', 'completion', 'text', 'content'):
                if k in obj and isinstance(obj[k], str):
                    obj[k] = anonymize_text(obj[k], names)
            outf.write(json.dumps(obj, ensure_ascii=False) + '\n')
            count += 1
    print(f'Wrote {count} cleaned records to {out_path}')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--names', default='train/anonymize_names.txt', help='Optional names file (one per line)')
    args = p.parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output)
    names_path = Path(args.names)
    if not in_path.exists():
        raise SystemExit(f'Input not found: {in_path}')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    process(in_path, out_path, names_path)
