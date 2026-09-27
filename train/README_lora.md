LoRA Training README

Recommended approach
- Hybrid: Prompt engineering + RAG for factual consistency + LoRA adapters to teach your voice from your examples and ratings.

Quick rationale
- Prompt engineering is immediate and low-cost.
- RAG lets the model access personal facts without embedding everything into weights.
- LoRA is efficient for style adaptation and works with large base models without full fine-tuning.

Setup
1) Create a Python venv and install dependencies:

```bash
python -m venv .venv
. .venv/bin/activate   # or .venv\Scripts\Activate.ps1 on Windows PowerShell
pip install -r train/requirements.txt
```

2) Prepare training data
- Use `train/interactive_training_mode.py` to collect rated examples to `train/train_with_persona.jsonl`.
- Optionally run `train/clean_anonymize.py` on any raw exports before augmentation.

3) Run LoRA training (example):

```bash
accelerate launch train/train_lora.py --model-or-path facebook/opt-1.3b --train-file train/train_with_persona.jsonl --output-dir outputs/lora --per-device-train-batch-size 1 --epochs 3
```

Notes
- Pick a base model that fits your GPU/CPU resources. `opt-1.3b` is an example; use smaller models if you lack VRAM.
- Adjust `--per-device-train-batch-size` and `--max-length` to your environment.
- For better results, clean and curate data: prefer high-rated (9-10) SFT examples and diverse prompts.

Using the adapter
- Load the base model and apply the LoRA adapter with `peft`'s `PeftModel`/`get_peft_model` when running inference.

Safety & privacy
- Remove PII before sending data off-host. The scripts include an anonymizer to help.
- Keep `ratings.jsonl` and `train_with_persona.jsonl` private.

Next steps
- I can scaffold an `adapter_load_example.py` to show how to load the LoRA adapter at runtime.
- Or I can start the reward-model / preference training pipeline that turns `ratings.jsonl` into a reward model for PPO-style fine-tuning.
