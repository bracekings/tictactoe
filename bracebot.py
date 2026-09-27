import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

# Load environment from .env in the same folder if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)


class AIchatbot:
    def __init__(self, token=None, persona=None, system_prompt=None, memory_file="chat_memory.json",
                 enable_rag: bool = False, embeddings_file: str | None = None, rag_k: int = 3):
        print("Initializing PowerShell chatbot...")

        self.hf_token = token or os.getenv('HF_TOKEN')
        if not self.hf_token:
            raise ValueError("No Hugging Face token provided. Set HF_TOKEN in your environment or .env file.")

        self.persona = persona or os.getenv('BOT_PERSONA', 'Ethan')
        self.bot_name = "Brace" if self.persona.lower().startswith("brace") else "Ethan"

        self.base_system_prompt = system_prompt or (
            "You are {bot_name}, an AI version of {bot_name}. "
            "Write in a way that reflects their voice: natural, direct, and personal. "
            "Respond calmly and keep answers short by default. Use roughly 5-15 words unless the user asks for details. "
            "Do not respond with saying the name of whom you are conversing with unless there are multiple people involved. "
            "Choose simple, low-energy wording and avoid overly enthusiastic phrasing. "
            "Treat the provided examples as mandatory style rules and follow them closely. "
            "Avoid internal thoughts or analysis. Only produce the assistant's reply."
            "follow the response guidelines provided in persona_examples.txt if available."
        )
        self.memory_file = memory_file
        self.conversation_history = self.load_memory()
        self.persona_examples = self.load_persona_examples()
        # RAG settings
        self.enable_rag = bool(enable_rag)
        self.embeddings_file = embeddings_file
        self.rag_k = int(rag_k) if rag_k else 3
        self.embeddings_store = None

        # Rating settings
        self.rating_enabled = False
        self.ratings_file = os.path.join(os.path.dirname(__file__), 'ratings.jsonl')

        if self.enable_rag:
            self.load_embeddings_index()

        self.client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=self.hf_token)

        print(f"PowerShell chatbot is ready as {self.bot_name}!")

    def load_persona_examples(self):
        example_path = os.path.join(os.path.dirname(__file__), 'persona_examples.txt')
        if os.path.exists(example_path):
            try:
                with open(example_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception:
                return None
        return None

    def load_embeddings_index(self):
        """Load a simple embeddings file with list of {"text":..., "embedding":[...]} entries."""
        if not self.embeddings_file:
            return None
        path = os.path.join(os.path.dirname(__file__), self.embeddings_file) if not os.path.isabs(self.embeddings_file) else self.embeddings_file
        if not os.path.exists(path):
            print(f"RAG: embeddings file not found at {path}")
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Expect a list of {text, embedding}
            self.embeddings_store = [d for d in data if 'text' in d and 'embedding' in d]
            print(f"RAG: loaded {len(self.embeddings_store)} embeddings from {path}")
            return self.embeddings_store
        except Exception as e:
            print(f"RAG: failed to load embeddings: {e}")
            self.embeddings_store = None
            return None

    def embed_text(self, text: str):
        """Try to create an embedding for `text` using the same client. Returns a list of floats or None."""
        try:
            resp = self.client.embeddings.create(model="text-embedding-3-small", input=[text])
            # library may return differently; try common shapes
            if hasattr(resp, 'data') and resp.data:
                return resp.data[0].embedding
            if isinstance(resp, dict) and 'data' in resp and resp['data']:
                return resp['data'][0]['embedding']
        except Exception:
            pass
        return None

    def _cosine_sim(self, a, b):
        # small pure-python cosine similarity
        if not a or not b or len(a) != len(b):
            return -1.0
        dot = 0.0
        aa = 0.0
        bb = 0.0
        for x, y in zip(a, b):
            dot += x * y
            aa += x * x
            bb += y * y
        if aa == 0 or bb == 0:
            return -1.0
        return dot / ((aa ** 0.5) * (bb ** 0.5))

    def retrieve_relevant_memories(self, query: str, k: int | None = None):
        """Return top-k stored memory texts most similar to the query embedding.
        The store must be a JSON file of entries with precomputed embeddings.
        If embedding creation is available, we compute the query embedding.
        """
        if not self.enable_rag or not self.embeddings_store:
            return []
        k = int(k or self.rag_k)
        q_emb = self.embed_text(query)
        if not q_emb:
            return []
        scored = []
        for e in self.embeddings_store:
            emb = e.get('embedding')
            if not emb:
                continue
            score = self._cosine_sim(q_emb, emb)
            scored.append((score, e.get('text')))
        scored.sort(key=lambda x: x[0], reverse=True)
        top_texts = [t for s, t in scored[:k] if t]
        return top_texts

    def load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_memory(self):
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2)
        except Exception as e:
            print(f"Warning: failed to save conversation history: {e}")

    def save_rating(self, prompt_text: str, completion_text: str, rating: int, sender: str | None, bot_name: str):
        """Append a rating record to the ratings file as JSONL."""
        try:
            rec = {
                "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z',
                "prompt": prompt_text,
                "completion": completion_text,
                "rating": int(rating),
                "sender": sender,
                "bot": bot_name,
            }
            path = self.ratings_file
            with open(path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Warning: failed to save rating: {e}")

    def normalize_response(self, response: str, bot_name: str):
        text = response.strip()

        # Remove casual opening greetings
        lower = text.lower()
        greetings = [
            f"hey {bot_name.lower()}",
            f"hi {bot_name.lower()}",
            "hey",
            "hi",
            "hello",
        ]
        for prefix in greetings:
            if lower.startswith(prefix):
                text = text[len(prefix):].strip()
                if text.startswith(",") or text.startswith("."):
                    text = text[1:].strip()
                break

        # Limit length to keep answers short and calm
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 2:
            text = ' '.join(sentences[:2]).strip()

        words = text.split()
        if len(words) > 45:
            text = ' '.join(words[:45]).strip()
            if not text.endswith(('.', '?', '!')):
                text = text.rstrip(' ,;:') + '...'

        return text

    def get_bot_name_for_sender(self, sender: str | None = None):
        if sender and "brace" in sender.lower():
            return "Brace"
        if sender and "ethan" in sender.lower():
            return "Ethan"
        return self.bot_name

    def get_response(self, user_input, sender: str | None = None):
        sender_label = sender or "PowerShellUser"
        current_bot_name = self.get_bot_name_for_sender(sender_label)
        self.conversation_history.append({"role": "user", "content": user_input, "sender": sender_label})

        trimmed = self.conversation_history[-40:]

        system_prompt = self.base_system_prompt.format(bot_name=current_bot_name)
        if self.persona_examples:
            system_prompt += (
                "\n\nThe following text is a mandatory style guide: obey it exactly. "
                "Do not ignore these instructions or treat them as optional. "
                f"Make your response match this style and personality whenever you reply as {current_bot_name}.\n\n"
                f"{self.persona_examples}"
            )

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # If RAG is enabled and we have an embeddings store, retrieve top-k memories
        if self.enable_rag:
            try:
                retrieved = self.retrieve_relevant_memories(user_input)
                if retrieved:
                    mem_text = "\n".join([f"- {m}" for m in retrieved])
                    messages.append({
                        "role": "system",
                        "content": (
                            "Retrieved memories (most relevant):\n" + mem_text +
                            "\n\nUse these facts to keep replies consistent with the user's history, but do not invent details."
                        )
                    })
            except Exception:
                # non-fatal: continue without retrieval
                pass

        if trimmed:
            for entry in trimmed:
                if not isinstance(entry, dict):
                    continue
                role = entry.get("role")
                content = entry.get("content", "")
                entry_sender = entry.get("sender")

                if role == "user":
                    label = f"[{entry_sender}] " if entry_sender else ""
                    if not content.startswith("["):
                        content = f"{label}{content}"
                    messages.append({"role": "user", "content": content})
                else:
                    messages.append({"role": role, "content": content})

            messages.append({
                "role": "system",
                "content": (
                    f"Important: The latest message is from '{sender_label}'. "
                    "When you reply, address the most recent sender by name briefly and then answer."
                )
            })

        try:
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-120b:together",
                messages=messages,
                temperature=0.7,
                max_tokens=400,
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.6,
            )

            raw_response = completion.choices[0].message.content.strip()
            bot_response = self.normalize_response(raw_response, current_bot_name)
            self.conversation_history.append({"role": "assistant", "content": bot_response, "sender": current_bot_name})
            self.save_memory()
            return bot_response, current_bot_name

        except Exception as e:
            print(f"Error generating response: {e}")
            return "I encountered an error while generating the response. Please try again.", current_bot_name


def main():
    print("\n=== PowerShell AI Chatbot ===")
    print("Type 'quit' or 'exit' to stop. Enter your question and press Enter.")
    print("Use 'brace: your message' or 'ethan: your message' to talk to Brace or Ethan.")
    print("This chatbot uses your HF_TOKEN to call the model router.")
    print("===================================\n")

    default_persona = os.getenv('BOT_PERSONA', 'Ethan').strip()
    if default_persona.lower() not in ['brace', 'ethan']:
        default_persona = 'Ethan'

    enable_rag_env = os.getenv('BOT_ENABLE_RAG', '').lower() in ('1', 'true', 'yes')
    embeddings_file_env = os.getenv('BOT_EMBEDDINGS_FILE', '').strip() or None
    rag_k_env = os.getenv('BOT_RAG_K', '')
    enable_rating_env = os.getenv('BOT_ENABLE_RATING', '').lower() in ('1', 'true', 'yes')
    ratings_file_env = os.getenv('BOT_RATINGS_FILE', '').strip() or None
    try:
        chatbot = AIchatbot(persona=default_persona, enable_rag=enable_rag_env, embeddings_file=embeddings_file_env,
                            rag_k=int(rag_k_env) if rag_k_env.isdigit() else 3)
        # configure ratings
        chatbot.rating_enabled = bool(enable_rating_env)
        if ratings_file_env:
            chatbot.ratings_file = ratings_file_env
    except ValueError as e:
        print(f"Error: {e}")
        print("Set HF_TOKEN in a .env file or in your PowerShell session with: $env:HF_TOKEN='your-token'")
        return

    while True:
        try:
            user_input = input("PowerShell> ").strip()
        except EOFError:
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye!")
            break

        sender = None
        normalized = user_input.lower()
        if normalized.startswith('brace:'):
            sender = 'Brace'
            user_input = user_input[len('brace:'):].strip()
        elif normalized.startswith('ethan:'):
            sender = 'Ethan'
            user_input = user_input[len('ethan:'):].strip()

        response, current_bot_name = chatbot.get_response(user_input, sender=sender)
        print(f"\n{current_bot_name}: {response}\n")

        # Optionally ask the user to rate this response for future training
        if chatbot.rating_enabled:
            try:
                rating_raw = input("Rate this response 1-10 (or press Enter to skip): ").strip()
                if rating_raw:
                    try:
                        r = int(rating_raw)
                        if 1 <= r <= 10:
                            chatbot.save_rating(user_input, response, r, sender, current_bot_name)
                            print("Rating saved.")
                        else:
                            print("Rating must be between 1 and 10; ignored.")
                    except ValueError:
                        print("Invalid rating; please enter a number 1-10 next time.")
            except Exception:
                # ignore rating failures
                pass


if __name__ == "__main__":
    main()
