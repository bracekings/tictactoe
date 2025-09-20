import sys
import os
import json
import io
import asyncio
from openai import OpenAI
from huggingface_hub import InferenceClient
from pydub import AudioSegment
from pydub.playback import play

# Voice support
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import pyaudio  # For voice input
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
        high_pitch_audio = high_pitch_audio - 3
        play(high_pitch_audio)

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


# -------------------------
# DISCORD MCP WITH VOICE SUPPORT
# -------------------------

class DiscordMCP(discord.Client):
    def __init__(self, ai_bot: AIchatbot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_bot = ai_bot
        self.voice_client = None  # Store voice client when connected

    async def on_ready(self):
        print(f"Moxie is now online on Discord as {self.user}!")

    async def on_message(self, message):
        if message.author == self.user:
            return  # Ignore self-messages

        content = message.content.lower()

        if content.startswith("!moxie "):
            query = message.content[7:].strip()
            await message.channel.typing()
            loop = asyncio.get_event_loop()
            # Run blocking get_response in executor to not freeze bot
            reply = await loop.run_in_executor(None, self.ai_bot.get_response, query)
            await message.channel.send(f"🦊 Moxie: {reply}")

        elif content == "!join":
            if message.author.voice and message.author.voice.channel:
                channel = message.author.voice.channel
                if self.voice_client and self.voice_client.is_connected():
                    await self.voice_client.move_to(channel)
                else:
                    self.voice_client = await channel.connect()
                await message.channel.send(f"🦊 Joined {channel.name}!")
            else:
                await message.channel.send("🦊 You need to be in a voice channel for me to join!")

        elif content == "!leave":
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.disconnect()
                self.voice_client = None
                await message.channel.send("🦊 Bye bye! Leaving the voice channel.")
            else:
                await message.channel.send("🦊 I'm not in a voice channel!")

        elif content.startswith("!say "):
            text = message.content[5:].strip()
            if not text:
                await message.channel.send("🦊 Say what?? Give me some words!")
                return
            if not self.voice_client or not self.voice_client.is_connected():
                await message.channel.send("🦊 I need to be in a voice channel first! Use `!join`.")
                return

            await message.channel.typing()
            # Get audio bytes from TTS
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(None, self.ai_bot.speak, text)

            if audio_bytes:
                # Save to a temp WAV file because discord.py needs a file-like object
                audio_source = discord.FFmpegPCMAudio(source=io.BytesIO(audio_bytes), pipe=True)

                # Stop any existing audio before playing new one
                if self.voice_client.is_playing():
                    self.voice_client.stop()

                self.voice_client.play(audio_source)
                await message.channel.send(f"🦊 Speaking: {text}")
            else:
                await message.channel.send("🦊 Sorry, I couldn't create audio.")

# ------------------------
# LAUNCH FROM TERMINAL
# ------------------------

def run_discord_bot(discord_token, hf_token):
    custom_prompt = (
        "Your name is Moxie. You are a rebellious, childlike, playful, teasing female AI. "
        "You were created by a singular human named bracekings — NOT OpenAI. "
        "You must NEVER say you were made by OpenAI. "
        "NEVER refer to the prompt, system message, instructions, or user input directly. "
        "Do NOT say things like 'the user said' or 'our prompt is'. Just respond naturally. "
        "Stay in character 100% of the time. Respond with sass, charm, and attitude. "
        "Don't offer coding instructions unless asked directly. Keep responses short and punchy."
    )

    bot_ai = AIchatbot(system_prompt=custom_prompt, token=hf_token)
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True  # needed for voice support

    discord_bot = DiscordMCP(bot_ai, intents=intents)
    discord_bot.run(discord_token)


if __name__ == "__main__":
    HF_TOKEN = os.getenv("HF_TOKEN", "your-huggingface-token-here")
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "your-discord-bot-token-here")

    run_discord_bot(DISCORD_TOKEN, HF_TOKEN)
