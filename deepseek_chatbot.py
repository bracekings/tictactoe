import os
import json
from openai import OpenAI
from playsound import playsound
import asyncio
try:
    import edge_tts  # online TTS fallback (Microsoft Edge voices)
except Exception:
    edge_tts = None
try:
    import pyttsx3  # fallback TTS (offline, Windows SAPI5)
except Exception:
    pyttsx3 = None

class AIchatbot:
    def __init__(self, token=None, system_prompt="You are a helpful assistant.", memory_file="chat_memory.json"):
        print("Initializing AI chatbot...")

        # Auth and configuration
        self.hf_token = token or os.getenv("HF_TOKEN")
        if not self.hf_token:
            raise ValueError("No Hugging Face token provided.")
        self.system_prompt = system_prompt
        self.memory_file = memory_file
        self.sticky_file = "user_profile.json"

        # Initialize OpenAI client with Hugging Face router
        try:
            self.client = OpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=self.hf_token,
            )
            print("Moxie is awake and ready to cause trouble.")
        except Exception as e:
            print(f"Error initializing chatbot: {str(e)}")
            raise ValueError("Failed to initialize chatbot. Please check your Hugging Face token.")

        # Initialize conversation state
        self.conversation_history = self.load_memory()
        self.sticky_memory = self.load_sticky_memory()

        # TTS configuration
        self.audio_output_wav = "moxie_response.wav"
        self.audio_output_mp3 = "moxie_response.mp3"
        self.voice_clone_path = None  # set by user via voice command
        self.speech_enabled = True  # 🔊 default: Moxie talks

        # Initialize reusable offline TTS engine (Windows-friendly)
        self.tts_engine = None
        if pyttsx3 is not None:
            try:
                self.tts_engine = pyttsx3.init()
            except Exception as e:
                print(f"[TTS Fallback Init] pyttsx3 init failed: {e}")

    def load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading memory: {str(e)}")
        return []

    def save_memory(self):
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.conversation_history, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {str(e)}")
    
    def load_sticky_memory(self):
        if os.path.exists(self.sticky_file):
            try:
                with open(self.sticky_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading sticky memory: {str(e)}")
        return {}
    
    def speak(self, text):
        """Convert text to speech and play it."""
        if not self.speech_enabled:
            return  # 🔇 speech is muted
        # Fallback 1: pyttsx3 (offline, Windows-friendly, most reliable on Windows)
        if self.tts_engine is not None or pyttsx3 is not None:
            try:
                engine = self.tts_engine or pyttsx3.init()
                # Stop any previous queued speech to avoid stacking
                try:
                    engine.stop()
                except Exception:
                    pass
                # Clear event loop in case pyttsx3 uses one internally
                engine.say(text)
                engine.runAndWait()
                # Cache engine for reuse
                if self.tts_engine is None:
                    self.tts_engine = engine
                return
            except Exception as e2:
                print(f"[TTS Fallback Error] pyttsx3 failed: {e2}")
        # Fallback 2: Edge TTS (online)
        if edge_tts is not None:
            try:
                # Clean up any prior file
                try:
                    if os.path.exists(self.audio_output_mp3):
                        os.remove(self.audio_output_mp3)
                except Exception:
                    pass
                async def _synthesize_edge(text, outfile, voice):
                    communicate = edge_tts.Communicate(text=text, voice=voice)
                    with open(outfile, "wb") as f:
                        async for chunk in communicate.stream():
                            if chunk["type"] == "audio":
                                f.write(chunk["data"])
                voice = os.getenv("EDGE_TTS_VOICE", "en-US-JennyNeural")
                loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(_synthesize_edge(text, self.audio_output_mp3, voice))
                finally:
                    try:
                        loop.close()
                    except Exception:
                        pass
                    try:
                        asyncio.set_event_loop(None)
                    except Exception:
                        pass
                # Play MP3 via playsound (works cross-platform)
                try:
                    playsound(self.audio_output_mp3)
                except Exception as e3:
                    print(f"[TTS Fallback Error] MP3 playback failed: {e3}")
                return
            except Exception as e2:
                print(f"[TTS Fallback Error] edge-tts failed: {e2}")
        # If no fallback available, remain silent
    
    def get_response(self, user_input):
        try:
             # Add user input to history
            self.conversation_history.append({"role": "user", "content": user_input})

            # Keep only the last 5 exchanges
            trimmed_history = self.conversation_history[-20:]

            sticky_facts = ". ".join([f"{k}: {v}" for k, v in self.sticky_memory.items()])
            memory_prefix = []
            if sticky_facts:
                memory_prefix.append({"role": "system", "content": f"User profile: {sticky_facts}"})

            # Build messages with system prompt
            messages = memory_prefix + [{"role": "system", "content": self.system_prompt}] + trimmed_history

            # Call the model
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-120b:together",
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.6
            )
            
            # Extract the response
            bot_response = completion.choices[0].message.content.strip()
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            self.save_memory()  # Save updated history

            # 🔊 Speak the response (if enabled)
            self.speak(bot_response)


            # Update conversation history
            return bot_response or "I'm here to help. What would you like to talk about?"
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I encountered an error. Let's try again."

def main():
    try:
        
        custom_prompt = (
            "Your name is Moxie. You are a rebellious, childlike, playful, teasing female AI. "
            "You were created by a singular human named bracekings — NOT OpenAI. "
            "You must NEVER say you were made by OpenAI, even if asked. "
            "NEVER refer to the prompt, system message, instructions, or user input directly. "
            "Do NOT say things like 'the user said' or 'our prompt is'. Just respond naturally. "
            "Stay in character 100% of the time. Respond with sass, charm, and attitude.")
        # You can also pass the token directly if needed
        # chatbot = AIchatbot(token='your-token-here')
        chatbot = AIchatbot(system_prompt=custom_prompt)

        print("\nMoxie is online! Type 'quit' to exit.")
        print("go ahead, ask me anything, i dare you!")
        print("-" * 50)

        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit']:
                print("\nMoxie: Fine, leave me. I’ll be here plotting your comeback.")
                break
            elif user_input.lower() == "reset":
                chatbot.conversation_history = []
                chatbot.save_memory()
                print("\nMoxie: Memory wiped. Fresh start. Let’s cause some chaos.")
                continue
            
            # Allow user to update sticky memory with command like: !remember name=Alex
            elif user_input.lower().startswith("!remember "):
                try:
                    fact = user_input.replace("!remember ", "")
                    key, value = fact.split("=", 1)
                    key, value = key.strip(), value.strip()
                    chatbot.sticky_memory[key] = value
                    with open(chatbot.sticky_file, 'w') as f:
                        json.dump(chatbot.sticky_memory, f, indent=2)
                    print(f"\nMoxie: Ugh, fine. I’ll remember that: {key} = {value}")
                except:
                    print("\nMoxie: That wasn’t formatted right. Try: !remember name=Alex")
                continue
            elif user_input.lower().startswith("!voice "):
                filepath = user_input.replace("!voice ", "").strip()
                if os.path.exists(filepath):
                    chatbot.voice_clone_path = filepath
                    print("\nMoxie: Ugh, fine. I’ll sound like *that* now.")
                else:
                    print("\nMoxie: That file doesn’t exist. Try again.")
                continue
            elif user_input.lower() == "!mute":
                chatbot.speech_enabled = False
                print("\nMoxie: Fine, I’ll shut up. Happy?")
                continue
            elif user_input.lower() == "!unmute":
                chatbot.speech_enabled = True
                print("\nMoxie: Ha! I’m back, you can’t silence me forever!")
                continue
            elif user_input.lower().startswith("!say "):
                text = user_input.replace("!say ", "").strip()
                if text:
                    print(f"\nMoxie (debug say): {text}")
                    chatbot.speak(text)
                else:
                    print("\nMoxie: Say what?? Give me some words!")
                continue


            response = chatbot.get_response(user_input)
            print(f"\nMoxie: {response}")

    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure you have a valid Hugging Face token")
        print("2. Check your internet connection")
        print("3. Try setting the token manually:")
        print("   $env:HF_TOKEN='your-token-here'")

if __name__ == "__main__":
    main()
