import os
import io
import json
import asyncio
import tempfile
from dotenv import load_dotenv

import discord
from pydub import AudioSegment
from pydub.playback import play

from huggingface_hub import InferenceClient
from openai import OpenAI

load_dotenv()

FFMPEG_PATH = os.getenv("FFMPEG_PATH", "C:\\ffmpeg\\bin\\ffmpeg.exe")
AudioSegment.converter = FFMPEG_PATH


class AIchatbot:
    def __init__(self, token=None, system_prompt="You act childish", memory_file="chat_memory.json"):
        self.hf_token = token or os.getenv("HF_TOKEN")
        if not self.hf_token:
            raise ValueError("Hugging Face token not provided")

        self.system_prompt = system_prompt
        self.memory_file = memory_file
        self.conversation_history = self.load_memory()

        self.tts_model = os.getenv("HF_TTS_MODEL", "suno/bark")
        self.tts_client = InferenceClient(model=self.tts_model, provider="auto", token=self.hf_token)

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)
        return []

    def save_memory(self):
        with open(self.memory_file, "w") as f:
            json.dump(self.conversation_history, f, indent=2)

    def speak(self, text):
        # Generate TTS audio bytes from Hugging Face model
        try:
            styled_text = "[young girl] " + text
            audio_bytes = self.tts_client.text_to_speech(styled_text)
            if isinstance(audio_bytes, dict) and "audio" in audio_bytes:
                audio_bytes = audio_bytes["audio"]
            if isinstance(audio_bytes, (bytes, bytearray)):
                return audio_bytes
        except Exception as e:
            print(f"TTS error: {e}")
        return None

    def get_response(self, user_input):
        try:
            self.conversation_history.append({"role": "user", "content": user_input})
            trimmed = self.conversation_history[-20:]
            messages = [{"role": "system", "content": self.system_prompt}] + trimmed

            client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=self.hf_token)
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b:together",
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.6,
            )
            bot_response = completion.choices[0].message.content.strip()
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            self.save_memory()
            return bot_response
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Oops, something went wrong."


class DiscordMCP(discord.Client):
    def __init__(self, ai_bot: AIchatbot, *args, **kwargs):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(intents=intents, *args, **kwargs)
        self.ai_bot = ai_bot
        self.voice_clients_map = {}  # guild_id -> voice_client

    async def on_ready(self):
        print(f"Moxie is online as {self.user}!")

    async def on_message(self, message):
        if message.author == self.user:
            return

        content = message.content.lower()
        guild_id = message.guild.id if message.guild else None

        if content.startswith("!moxie "):
            query = message.content[7:].strip()
            await message.channel.typing()
            loop = asyncio.get_event_loop()
            reply = await loop.run_in_executor(None, self.ai_bot.get_response, query)
            await message.channel.send(f"🦊 Moxie: {reply}")

        elif content == "!join":
            if not guild_id:
                await message.channel.send("🦊 This command can only be used in a server.")
                return
            if message.author.voice and message.author.voice.channel:
                channel = message.author.voice.channel
                if guild_id in self.voice_clients_map and self.voice_clients_map[guild_id].is_connected():
                    await self.voice_clients_map[guild_id].move_to(channel)
                else:
                    vc = await channel.connect()
                    self.voice_clients_map[guild_id] = vc
                await message.channel.send(f"🦊 Joined {channel.name}!")
            else:
                await message.channel.send("🦊 You need to be in a voice channel first!")

        elif content == "!leave":
            if guild_id in self.voice_clients_map and self.voice_clients_map[guild_id].is_connected():
                await self.voice_clients_map[guild_id].disconnect()
                del self.voice_clients_map[guild_id]
                await message.channel.send("🦊 Left the voice channel!")
            else:
                await message.channel.send("🦊 I'm not in a voice channel!")

        elif content.startswith("!say "):
            text = message.content[5:].strip()
            if not text:
                await message.channel.send("🦊 Say what?? Give me some words!")
                return

            if guild_id not in self.voice_clients_map or not self.voice_clients_map[guild_id].is_connected():
                await message.channel.send("🦊 I need to join a voice channel first! Use `!join`.")
                return

            vc = self.voice_clients_map[guild_id]

            await message.channel.trigger_typing()
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(None, self.ai_bot.speak, text)

            if audio_bytes:
                with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp_audio:
                    temp_audio.write(audio_bytes)
                    temp_audio.flush()

                    audio_source = discord.FFmpegPCMAudio(temp_audio.name)

                    if vc.is_playing():
                        vc.stop()

                    vc.play(audio_source)
                    await message.channel.send(f"🦊 Said: {text}")
            else:
                await message.channel.send("🦊 Sorry, I couldn't generate the audio.")


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

    bot = DiscordMCP(bot_ai)
    bot.run(discord_token)


if __name__ == "__main__":
    HF_TOKEN = os.getenv("HF_TOKEN")
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

    if not HF_TOKEN or not DISCORD_TOKEN:
        print("❌ ERROR: Please set HF_TOKEN and DISCORD_TOKEN in your environment or .env file")
        exit(1)

    run_discord_bot(DISCORD_TOKEN, HF_TOKEN)
