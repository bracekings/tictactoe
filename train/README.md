# Dataset & Training Scaffold

This folder helps you prepare a dataset of your personal conversations and start training or fine-tuning a model that behaves like you.

Contents
- `dataset_example.jsonl` — small JSONL sample of prompt/completion pairs.
- `prepare_dataset.py` — utility script to convert common chat exports into JSONL pairs.

Quick guidance

1) Collect data
- Export your chat logs (DMs, emails, chat transcripts). JSON with `role`/`content` pairs, or plain text where user/assistant lines are identifiable, works best.
- Aim for quality over quantity. 500–5k high-quality assistant replies is a good start for LoRA; 1k–10k+ for full SFT.

2) Clean & anonymize
- Remove personal identifiers (SSNs, full names, phone numbers, private keys).
- Normalize whitespace and punctuation.

3) Format rules
- OpenAI fine-tune: JSONL where each line is {"prompt":"<your input>","completion":"<your reply>"}
  - `completion` should end with a newline and a stop token if you use them (e.g. "\n").
- Hugging Face / transformers: typical sequence-to-sequence pairs or instruction tuning format depending on model.

4) Example workflows

OpenAI fine-tune (example):

- Convert to `train.jsonl` as above.
- Run:

```bash
openai api fine_tunes.create -t train.jsonl -m <base-model>
```

Hugging Face + LoRA (sketch):

- Dependencies: `transformers datasets accelerate peft bitsandbytes sentence-transformers`
- Use a LoRA training script with `peft` and `accelerate` to produce an adapter that you can load on top of a base model.

5) RAG (optional)
- Build embeddings for your longer memories using `sentence-transformers` or an API, store in FAISS, and at runtime retrieve top-K passages to prepend to model context.

Security & Ethics
- Keep this dataset private. Treat it like sensitive personal data.
- Provide a way to remove or redact entries later.

Next steps
- Run `prepare_dataset.py` on your export to produce `train.jsonl`.
- Decide whether to use OpenAI fine-tuning, HF LoRA, or RAG + prompting.

If you want, I can:
- Run `prepare_dataset.py` on a sample export you provide.
- Scaffold a LoRA training script next.