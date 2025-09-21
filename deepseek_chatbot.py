import sys
import os
import json
import io
import asyncio
from openai import OpenAI
from huggingface_hub import InferenceClient
from pydub import AudioSegment
from pydub.playback import play
from dotenv import load_dotenv 

# --- Load .env File with Debug Info ---
env_path = os.path.join(os.path.dirname(__file__), ".env")
print("🔍 Looking for .env at:", env_path)
print("📂 Does .env exist?", os.path.isfile(env_path))

load_dotenv(dotenv_path=env_path)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
print("🔑 Loaded DISCORD_TOKEN:", repr(DISCORD_TOKEN)[:20] if DISCORD_TOKEN else "None (Not found!)")

HF_TOKEN = os.getenv("HF_TOKEN")
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "C:\\ffmpeg\\bin\\ffmpeg.exe")

# --- Python Executable Debug ---
print("🐍 Python executable:", sys.executable)

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import pyaudio
except ImportError:
    pyaudio = None

import speech_recognition as sr
import discord

print("Python executable:", sys.executable)

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

        self.client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=self.hf_token)
        self.conversation_history = self.load_memory()
        self.sticky_memory = self.load_sticky_memory()

        self.tts_model = os.getenv("HF_TTS_MODEL", "suno/bark")
        self.tts_client = InferenceClient(model=self.tts_model, provider="auto", token=self.hf_token)

        self.audio_output_path = "moxie_response.wav"
        self.voice_clone_path = None
        self.speech_enabled = True
        self.voice_input_enabled = pyaudio is not None

        print("Moxie is awake and ready to cause trouble.")

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        return []

    def save_memory(self):
        with open(self.memory_file, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)

    def load_sticky_memory(self):
        if os.path.exists(self.sticky_file):
            with open(self.sticky_file, 'r') as f:
                return json.load(f)
        return {}

    def speak_childlike(self, audio_bytes):
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
        new_rate = int(audio.frame_rate * 1.6)
        high_pitch_audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_rate})
        high_pitch_audio = high_pitch_audio.set_frame_rate(44100)
        high_pitch_audio = high_pitch_audio - 3  # Slight volume reduction
    
        output_buffer = io.BytesIO()
        high_pitch_audio.export(output_buffer, format="wav")
        output_buffer.seek(0)
        return output_buffer  # Return BytesIO stream instead of playing

    def speak(self, text):
        if not self.speech_enabled:
            return None
        try:
            styled_text = "[young girl] " + text
            audio_bytes = self.tts_client.text_to_speech(styled_text)
            if isinstance(audio_bytes, dict) and "audio" in audio_bytes:
                audio_bytes = audio_bytes["audio"]
            if isinstance(audio_bytes, (bytes, bytearray)):
                return audio_bytes  # Return audio bytes for voice playback
        except Exception as e:
            print(f"[TTS Error] {e}")
            if pyttsx3:
                engine = pyttsx3.init()
                engine.setProperty('rate', 180)
                for voice in engine.getProperty('voices'):
                    if "female" in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
                engine.say(text)
                engine.runAndWait()
        return None

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
            return bot_response
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Oops, something went wrong."

    def listen_to_user(self):
        if not self.voice_input_enabled:
            print("Voice input is disabled.")
            return None

        recognizer = sr.Recognizer()
        try:
            mic = sr.Microphone()
        except Exception as e:
            print(f"Mic issue: {e}")
            return None

        print("Moxie: I'm listening...")

        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            print("Didn't catch that.")
        except sr.RequestError as e:
            print(f"API Error: {e}")
        return None


class DiscordMCP(discord.Client):
    def __init__(self, ai_bot: AIchatbot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_bot = ai_bot
        self.voice_clients_map = {}  # guild.id -> voice_client

    async def on_ready(self):
        print(f"Moxie is now online on Discord as {self.user}!")

    async def on_voice_state_update(self, member, before, after):
        # Track voice client state on disconnect
        if member == self.user:
            guild_id = member.guild.id
            if after.channel is None:
                print(f"Moxie disconnected from voice channel in guild {guild_id}")
                self.voice_clients_map.pop(guild_id, None)

    async def on_message(self, message):
        if message.author == self.user:
            return

        content = message.content.lower()

        # Debug print to check what type message.channel is at start of on_message
        print(f"[DEBUG] message.channel: {message.channel} (type: {type(message.channel)})")

        if content.startswith("!moxie "):
            query = message.content[7:].strip()
            
            # Safe trigger_typing: check if method exists
            if hasattr(message.channel, "trigger_typing"):    
                await message.channel.trigger_typing()
            else:
                print("[WARNING] message.channel has no trigger_typing method!")
    
            
            loop = asyncio.get_event_loop()
            reply = await loop.run_in_executor(None, self.ai_bot.get_response, query)
            await message.channel.send(f"🦊 Moxie: {reply}")

        elif content == "!join":
            if message.author.voice and message.author.voice.channel:
                voice_channel = message.author.voice.channel
                
                # Debug print to confirm voice channel type
                print(f"[DEBUG] voice_channel: {voice_channel} (type: {type(voice_channel)})")

                
                guild_id = message.guild.id
                try:
                    current_vc = self.voice_clients_map.get(guild_id)

                    if current_vc and current_vc.is_connected():
                        await current_vc.move_to(voice_channel)
                        await message.channel.send(f"🦊 Moved to {voice_channel.name}!")
                    else:
                        new_vc = await voice_channel.connect()
                        self.voice_clients_map[guild_id] = new_vc
                        await message.channel.send(f"🦊 Joined {voice_channel.name}!")
                except asyncio.TimeoutError:
                    await message.channel.send("🦊 Timeout while connecting to voice. Please try again.")
                except Exception as e:
                    await message.channel.send(f"🦊 Failed to join voice channel: {e}")
            else:
                await message.channel.send("🦊 You need to be in a voice channel for me to join!")

        elif content == "!leave":
            guild_id = message.guild.id
            vc = self.voice_clients_map.get(guild_id)
            if vc and vc.is_connected():
                await vc.disconnect()
                self.voice_clients_map.pop(guild_id, None)
                await message.channel.send("🦊 Bye bye! Leaving the voice channel.")
            else:
                await message.channel.send("🦊 I'm not in a voice channel!")

        elif content.startswith("!say "):
            text = message.content[5:].strip()
            if not text:
                await message.channel.send("🦊 Say what?? Give me some words!")
                return

            guild_id = message.guild.id
            vc = self.voice_clients_map.get(guild_id)

            if not vc or not vc.is_connected():
                await message.channel.send("🦊 I need to be in a voice channel first! Use `!join`.")
                return

             # Safely trigger typing in the text channel if possible
        if hasattr(message.channel, "trigger_typing"):
            await message.channel.trigger_typing()
        else:
            print(f"[WARNING] Can't trigger typing: {type(message.channel)}")


            loop = asyncio.get_event_loop()

            # Step 1: Generate the base TTS audio
            base_audio = await loop.run_in_executor(None, self.ai_bot.speak, text)

            # Step 2: Apply the childlike pitch transformation
            if base_audio:
                processed_audio = await loop.run_in_executor(None, self.ai_bot.speak_childlike, base_audio)

            # Step 3: Use FFmpegPCMAudio with the processed audio stream
                audio_source = discord.FFmpegPCMAudio(
                    source=processed_audio, 
                    pipe=True, 
                    executable=FFMPEG_PATH  # Optional: explicitly use your ffmpeg path
                )

                if vc.is_playing():
                    vc.stop()

                vc.play(audio_source)
                await message.channel.send(f"🦊 Said: {text}")
            else:
                await message.channel.send("🦊 Sorry, I couldn't generate the audio.")

            if base_audio:
                audio_source = discord.FFmpegPCMAudio(source=io.BytesIO(base_audio), pipe=True)

                if vc.is_playing():
                    vc.stop()

                vc.play(audio_source)
                await message.channel.send(f"🦊 Said: {text}")
            else:
                await message.channel.send("🦊 Sorry, I couldn't generate the audio.")


# Main bot token
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

if not DISCORD_TOKEN:
    print("Error: DISCORD_TOKEN environment variable is not set.")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

ai_bot = AIchatbot()
client = DiscordMCP(ai_bot=ai_bot, intents=intents)
client.run(DISCORD_TOKEN)
print("DISCORD_TOKEN (first 10 chars):", repr(DISCORD_TOKEN[:10]) if DISCORD_TOKEN else "None")

if not DISCORD_TOKEN or len(DISCORD_TOKEN.strip()) < 10:
    print("❌ ERROR: DISCORD_TOKEN is missing or invalid. Please check your .env file.")
    exit(1)
else:
    print("✅ Discord token loaded.")

print("Current working directory:", os.getcwd())
print("Looking for .env in:", os.path.abspath("."))
print("Does .env exist?", os.path.isfile(".env"))