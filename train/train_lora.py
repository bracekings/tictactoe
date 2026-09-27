#!/usr/bin/env python3
"""train_lora.py

Minimal LoRA training scaffold using Hugging Face Transformers + PEFT.
Trains a causal LM with LoRA adapters on `train_with_persona.jsonl` produced earlier.

This script is a starting point — test with a small dataset and reduce batch sizes for local runs.

Usage (example):
accelerate launch train/train_lora.py --model-or-path facebook/opt-1.3b --train-file train/train_with_persona.jsonl --output-dir outputs/lora

"""
import argparse
import json
from pathlib import Path
import math

import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from transformers import DataCollatorForLanguageModeling
from peft import get_peft_model, LoraConfig, TaskType


def build_dataset(tokenizer, dataset, max_length=1024, prompt_key='prompt', completion_key='completion'):
    # For causal LM fine-tuning: concatenate prompt+completion, and mask prompt tokens in labels
    def map_fn(example):
        prompt = example.get(prompt_key, '')
        completion = example.get(completion_key, '')
        full = prompt + completion
        enc = tokenizer(full, truncation=True, max_length=max_length)
        prompt_enc = tokenizer(prompt, truncation=True, max_length=max_length)
        input_ids = enc['input_ids']
        labels = input_ids.copy()
        prompt_len = len(prompt_enc['input_ids'])
        # mask prompt tokens
        for i in range(min(prompt_len, len(labels))):
            labels[i] = -100
        return {'input_ids': input_ids, 'attention_mask': enc['attention_mask'], 'labels': labels}

    return dataset.map(map_fn, remove_columns=dataset.column_names, batched=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model-or-path', required=True)
    p.add_argument('--train-file', default='train/train_with_persona.jsonl')
    p.add_argument('--output-dir', default='outputs/lora')
    p.add_argument('--per-device-train-batch-size', type=int, default=1)
    p.add_argument('--epochs', type=int, default=3)
    p.add_argument('--lr', type=float, default=2e-5)
    p.add_argument('--lora-r', type=int, default=8)
    p.add_argument('--lora-alpha', type=int, default=16)
    p.add_argument('--max-length', type=int, default=1024)
    args = p.parse_args()

    train_file = Path(args.train_file)
    if not train_file.exists():
        raise SystemExit(f"Train file not found: {train_file}")

    print('Loading dataset...')
    ds = load_dataset('json', data_files=str(train_file))['train']

    print('Loading tokenizer and model...')
    tokenizer = AutoTokenizer.from_pretrained(args.model_or_path, use_fast=True)
    # ensure padding side for causal LM
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(args.model_or_path, torch_dtype=torch.float16, device_map='auto')

    # Prepare dataset
    train_ds = build_dataset(tokenizer, ds, max_length=args.max_length)

    # PEFT LoRA config
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=['q_proj','v_proj'] if 'gpt' in args.model_or_path or 'opt' in args.model_or_path else None,
        lora_dropout=0.05,
    )
    model = get_peft_model(model, peft_config)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.per_device_train_batch_size,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        fp16=True,
        logging_steps=10,
        save_total_limit=3,
        gradient_accumulation_steps=1,
        optim='adamw_torch',
        remove_unused_columns=False,
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        data_collator=data_collator,
    )

    print('Starting training...')
    trainer.train()
    trainer.save_model(args.output_dir)
    print('Training complete. LoRA adapter saved to', args.output_dir)


if __name__ == '__main__':
    main()
