#!/usr/bin/env python3
"""prepare_dataset.py

Simple utility to convert common chat export formats into a JSONL file of prompt/completion pairs.

Usage:
    python prepare_dataset.py --input export.json --output train.jsonl

Supported input formats:
- JSON list of {"role":"user"|"assistant", "content":"..."}
- Plain text with alternating lines starting with "User:" and "Assistant:"

This script is intentionally conservative: it pairs each assistant reply with the immediately preceding user message.
"""
import argparse
import json
from pathlib import Path
import re


def load_json_messages(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Expect either list of messages or an object with 'messages'
    if isinstance(data, dict) and "messages" in data:
        messages = data["messages"]
    elif isinstance(data, list):
        messages = data
    else:
        raise ValueError("Unsupported JSON structure; expected list or {messages: [...]}.")
    # Normalize: each message should have 'role' and 'content'
    norm = []
    for m in messages:
        role = m.get("role") or m.get("sender") or m.get("from")
        content = m.get("content") or m.get("text")
        if role and content:
            norm.append({"role": role.lower(), "content": content})
    return norm


def load_text_messages(path):
    lines = [l.strip() for l in open(path, encoding="utf-8").read().splitlines() if l.strip()]
    messages = []
    for line in lines:
        if line.lower().startswith("user:"):
            messages.append({"role":"user","content": line.split(":",1)[1].strip()})
        elif line.lower().startswith("assistant:") or line.lower().startswith("bot:"):
            messages.append({"role":"assistant","content": line.split(":",1)[1].strip()})
        else:
            # try alternating: if last is assistant, treat as user, else assistant
            if not messages or messages[-1]["role"]=="assistant":
                messages.append({"role":"user","content": line})
            else:
                messages.append({"role":"assistant","content": line})
    return messages


def to_jsonl_pairs(messages, out_path):
    """Pair each assistant reply with the immediately preceding user message."""
    pairs = []
    for i, m in enumerate(messages):
        if m["role"] in ("assistant", "bot"):
            # find preceding user message
            j = i-1
            while j>=0 and messages[j]["role"]!="user":
                j -= 1
            if j>=0:
                prompt = f"User: {messages[j]['content']}\n"
                completion = f"Assistant: {m['content']}\n"
                pairs.append({"prompt": prompt, "completion": completion})
    # write JSONL
    out_path = Path(out_path)
    with out_path.open("w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    return len(pairs)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Path to exported chat (json or txt)")
    p.add_argument("--output", required=True, help="Path to output train.jsonl")
    args = p.parse_args()
    inp = Path(args.input)
    if not inp.exists():
        raise SystemExit(f"Input not found: {inp}")
    if inp.suffix.lower() in (".json", ".jsonl"):
        messages = load_json_messages(inp)
    else:
        messages = load_text_messages(inp)
    count = to_jsonl_pairs(messages, args.output)
    print(f"Wrote {count} prompt/completion pairs to {args.output}")


if __name__ == '__main__':
    main()
