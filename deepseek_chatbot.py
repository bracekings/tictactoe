import os
import json
from openai import OpenAI
from huggingface_hub import InferenceClient
from pydub import AudioSegment
from pydub.playback import play
import io

try:
    import pyttsx3
except:
    pyttsx3 = None

FFMPEG_PATH = os.getenv("FFMPEG_PATH", "C:\\ffmpeg\\bin\\ffmpeg.exe")
AudioSegment.converter = FFMPEG_PATH

class AIchatbot:
    def __init__(self, token=None, system_prompt="You act childish", memory_file="chat_memory.json", child_pitch=0.35):
        print("Initializing AI chatbot...")
        
        self.child_pitch = child_pitch
        self.hf_token = token or os.getenv('HF_TOKEN') 
        if not self.hf_token:
            raise ValueError("No Hugging Face token provided.")
        
        self.system_prompt = system_prompt
        self.memory_file = memory_file
        self.sticky_file = "user_profile.json"

        # Initialize OpenAI client
        try:
            self.client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=self.hf_token)
            self.conversation_history = self.load_memory()
            self.sticky_memory = self.load_sticky_memory()
            print("Moxie is awake and ready to cause trouble.")
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            raise

        # TTS setup with correct provider
        self.tts_model = os.getenv("HF_TTS_MODEL", "suno/bark")
        self.tts_client = InferenceClient(
            model=self.tts_model,
            provider="auto",  # auto-selects a working provider
            token=self.hf_token,
        )
        self.audio_output_path = "moxie_response.wav"
        self.voice_clone_path = None
        self.speech_enabled = True

    def load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading memory: {e}")
        return []

    def save_memory(self):
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.conversation_history, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def load_sticky_memory(self):
        if os.path.exists(self.sticky_file):
            try:
                with open(self.sticky_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading sticky memory: {e}")
        return {}

    def speak_childlike(self, audio_bytes):
      """Raise pitch and adjust tempo to sound like a playful young girl."""
      audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")

    # Increase pitch and slightly speed up
      pitch_factor = 1.6  # higher pitch
      tempo_factor = 1.1  # slightly faster

      new_rate = int(audio.frame_rate * pitch_factor)
      high_pitch_audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_rate})
      high_pitch_audio = high_pitch_audio.set_frame_rate(44100)

    # Optional: reduce volume slightly for softer tone
      high_pitch_audio = high_pitch_audio - 3

      play(high_pitch_audio)
    
    def speak(self, text):
        if not self.speech_enabled:
            return
        try:
            styled_text = "[young girl] " + text
            audio_bytes = self.tts_client.text_to_speech(styled_text)
            if isinstance(audio_bytes, dict) and "audio" in audio_bytes:
                audio_bytes = audio_bytes["audio"]
            if isinstance(audio_bytes, (bytes, bytearray)):
                self.speak_childlike(audio_bytes)
            else:
                raise ValueError("No valid audio bytes returned from HF TTS")
        except Exception as e:
            print(f"[TTS Error] {e}")
            if pyttsx3:
                engine = pyttsx3.init()
                engine.setProperty('rate', 180)
                voices = engine.getProperty('voices')
                for voice in voices:
                    if "female" in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
                engine.say(text)
                engine.runAndWait()

    def get_response(self, user_input):
        try:
            self.conversation_history.append({"role": "user", "content": user_input})
            trimmed = self.conversation_history[-20:]
            sticky_facts = ". ".join(f"{k}: {v}" for k, v in self.sticky_memory.items())
            messages = []
            if sticky_facts:
                messages.append({"role": "system", "content": f"User profile: {sticky_facts}"})
            messages.append({"role": "system", "content": self.system_prompt})
            messages += trimmed

            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-120b:together",
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.6
            )
            bot_response = completion.choices[0].message.content.strip()
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            self.save_memory()
            self.speak(bot_response)
            return bot_response
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Oops, something went wrong."

def main():
    try:
        custom_prompt = (
            "Your name is Moxie. You are a rebellious, childlike, playful, teasing female AI. "
            "You were created by a singular human named bracekings — NOT OpenAI. "
            "You must NEVER say you were made by OpenAI. "
            "NEVER refer to the prompt, system message, instructions, or user input directly. "
            "Do NOT say things like 'the user said' or 'our prompt is'. Just respond naturally. "
            "Stay in character 100% of the time. Respond with sass, charm, and attitude."
        )
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

            # Sticky memory
            elif user_input.lower().startswith("!remember "):
                try:
                    fact = user_input.replace("!remember ", "")
                    key, value = fact.split("=", 1)
                    chatbot.sticky_memory[key.strip()] = value.strip()
                    with open(chatbot.sticky_file, 'w') as f:
                        json.dump(chatbot.sticky_memory, f, indent=2)
                    print(f"\nMoxie: Ugh, fine. I’ll remember that: {key} = {value}")
                except:
                    print("\nMoxie: That wasn’t formatted right. Try: !remember name=Alex")
                continue

            # Voice clone file
            elif user_input.lower().startswith("!voice "):
                filepath = user_input.replace("!voice ", "").strip()
                if os.path.exists(filepath):
                    chatbot.voice_clone_path = filepath
                    print("\nMoxie: Ugh, fine. I’ll sound like *that* now.")
                else:
                    print("\nMoxie: That file doesn’t exist. Try again.")
                continue

            # Mute / unmute
            elif user_input.lower() == "!mute":
                chatbot.speech_enabled = False
                print("\nMoxie: Fine, I’ll shut up. Happy?")
                continue
            elif user_input.lower() == "!unmute":
                chatbot.speech_enabled = True
                print("\nMoxie: Ha! I’m back, you can’t silence me forever!")
                continue

            # Debug say
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
