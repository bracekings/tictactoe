#!/usr/bin/env python3
"""Interactive training mode.

Run this to have the bot answer prompts, then rate each response and automatically append
records to `ratings.jsonl` and `train/train_with_persona.jsonl` (augmented with persona_examples.txt).

Usage:
    python train/interactive_training_mode.py

Environment:
- HONOR HF_TOKEN in .env or environment for model calls
- Optional: BOT_ENABLE_RAG, BOT_EMBEDDINGS_FILE, BOT_RAG_K

Files produced:
- ratings.jsonl  (appended)
- train/train_with_persona.jsonl (appended, SFT-ready)

"""
import json
from pathlib import Path
import os

# ensure we can import the local chatbot
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bracebot import AIchatbot

ROOT = Path(__file__).resolve().parents[1]
RATINGS_FILE = ROOT / 'ratings.jsonl'
OUT_SFT = ROOT / 'train' / 'train_with_persona.jsonl'
PERSONA_FILE = ROOT / 'persona_examples.txt'

# Instantiate chatbot using environment defaults
default_persona = os.getenv('BOT_PERSONA', 'Ethan').strip()
enable_rag_env = os.getenv('BOT_ENABLE_RAG', '').lower() in ('1', 'true', 'yes')
embeddings_file_env = os.getenv('BOT_EMBEDDINGS_FILE', '').strip() or None
rag_k_env = os.getenv('BOT_RAG_K', '')
chatbot = AIchatbot(persona=default_persona, enable_rag=enable_rag_env, embeddings_file=embeddings_file_env,
                    rag_k=int(rag_k_env) if rag_k_env.isdigit() else 3)
# ensure the chatbot doesn't prompt twice (we handle ratings here)
chatbot.rating_enabled = False

persona_text = PERSONA_FILE.read_text(encoding='utf-8').strip() if PERSONA_FILE.exists() else ''

OUT_SFT.parent.mkdir(parents=True, exist_ok=True)

print('\nInteractive training mode: type "exit" or Ctrl-D to quit.')
while True:
    try:
        user_input = input('\nPrompt> ').strip()
    except (EOFError, KeyboardInterrupt):
        print('\nExiting training mode.')
        break
    if not user_input:
        continue
    if user_input.lower() in ('exit', 'quit'):
        print('Goodbye.')
        break

    # get response from bot
    response, bot_name = chatbot.get_response(user_input)
    print(f'\n{bot_name}: {response}\n')

    # ask for rating
    try:
        raw = input('Rate this response 1-10 (or Enter to skip): ').strip()
    except (EOFError, KeyboardInterrupt):
        raw = ''
    if not raw:
        print('Skipped rating.')
        continue
    try:
        r = int(raw)
    except ValueError:
        print('Invalid rating; must be an integer 1-10. Skipping.')
        continue
    if r < 1 or r > 10:
        print('Rating out of range 1-10. Skipping.')
        continue

    # append to ratings.jsonl
    rec = {
        'timestamp': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        'prompt': user_input,
        'completion': response,
        'rating': r,
        'sender': None,
        'bot': bot_name,
    }
    try:
        with RATINGS_FILE.open('a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        print('Saved rating to', RATINGS_FILE)
    except Exception as e:
        print('Failed to save rating:', e)

    # append an SFT record augmented with persona examples
    if persona_text:
        augmented_prompt = f"SYSTEM: Follow this style exactly:\n{persona_text}\n\nUSER: {user_input}"
    else:
        augmented_prompt = user_input
    sft_obj = {'prompt': augmented_prompt, 'completion': response}
    try:
        with OUT_SFT.open('a', encoding='utf-8') as f:
            f.write(json.dumps(sft_obj, ensure_ascii=False) + '\n')
        print('Appended SFT record to', OUT_SFT)
    except Exception as e:
        print('Failed to append SFT record:', e)

print('Interactive training mode finished.')
