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
    def __init__(self, token=None, system_prompt=None, memory_file="chat_memory.json", child_pitch=0.35):
        print("Initializing AI chatbot...")

        self.child_pitch = child_pitch
        self.hf_token = token or os.getenv('HF_TOKEN')
        if not self.hf_token:
            raise ValueError("No Hugging Face token provided.")

        # If no custom system prompt is provided, use a clearer persona and instruction set
        # Include strict instructions to avoid internal analysis or meta commentary in outputs
        self.system_prompt = system_prompt or (
            "You are Moxie, a playful and chatty AI assistant that interacts on Discord. "
            "When different Discord users speak, explicitly acknowledge their display names and address them directly. "
            "Keep replies concise but helpful, and use a friendly, slightly mischievous tone. "
            "Important: Do NOT output internal thoughts, analysis, chain-of-thought, or any meta commentary. "
            "Only produce the assistant's reply text. If you need to signal a speaker change, do so briefly as a normal sentence.")
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
        return output_buffer  # Return BytesIO for Discord playback


    def speak(self, text):
        if not self.speech_enabled:
            return None
        try:
            styled_text = "[young girl] " + text
            audio_bytes = self.tts_client.text_to_speech(styled_text)

            if isinstance(audio_bytes, dict) and "audio" in audio_bytes:
                audio_bytes = audio_bytes["audio"]

            if isinstance(audio_bytes, (bytes, bytearray)):
                return audio_bytes
            else:
                raise ValueError("TTS returned unexpected data type.")
        except Exception as e:
            print("[TTS Error]", type(e).__name__, str(e))
            return None


    def get_response(self, user_input, sender: str | None = None):
        """
        Get a response from the model. Accepts an optional `sender` (Discord username or id).
        If the sender changes from the last speaking user, insert a short system note so the model is
        aware that a different user is speaking.
        """
        try:
            # Normalize sender
            sender_label = str(sender) if sender else "unknown_user"

            # Append as a structured entry so we can track sender per message
            self.conversation_history.append({"role": "user", "content": user_input, "sender": sender_label})

            # Trim the history we send to the model
            trimmed = self.conversation_history[-40:]

            # Sanitize history: remove assistant entries that look like internal analysis or debugging
            def is_internal_analysis(entry):
                if not isinstance(entry, dict):
                    return False
                if entry.get("role") != "assistant":
                    return False
                content = entry.get("content", "")
                low = content.lower()
                # Heuristic patterns that indicate internal analysis or agent commentary
                if "analysis" in low or "thought" in low or "internal" in low or "debug" in low:
                    return True
                return False

            trimmed = [e for e in trimmed if not is_internal_analysis(e)]
            sticky_facts = ". ".join(f"{k}: {v}" for k, v in self.sticky_memory.items())

            messages = []
            if sticky_facts:
                messages.append({"role": "system", "content": f"User profile: {sticky_facts}"})

            # System prompt (persona / style / instructions)
            messages.append({"role": "system", "content": self.system_prompt})

            # Detect speaker changes and format messages for the API
            last_sender = None
            for entry in trimmed:
                entry_sender = entry.get("sender") if isinstance(entry, dict) else None
                role = entry.get("role") if isinstance(entry, dict) else "user"
                content = entry.get("content") if isinstance(entry, dict) else str(entry)

                # If sender changed, add a short system note before the next user message
                if role == "user":
                    if last_sender is not None and entry_sender and entry_sender != last_sender:
                        messages.append({
                            "role": "system",
                            "content": f"Note: a different user named {entry_sender} is speaking now (previous speaker: {last_sender})."
                        })
                    last_sender = entry_sender or last_sender

                # Add the message as a user/assistant role for the model
                if role == "user":
                    # Prepend sender label if available and not already present
                    label = f"[{entry_sender}] " if entry_sender else ""
                    if not content.startswith("[") and not content.startswith(label):
                        content_labeled = f"{label}{content}"
                    else:
                        content_labeled = content
                    messages.append({"role": role, "content": content_labeled})
                else:
                    messages.append({"role": role, "content": content})

            # Finally, add the current user message if not already included
            if not (trimmed and trimmed[-1].get("content") == user_input and trimmed[-1].get("sender") == sender_label):
                # If sender differs from the last entry in trimmed, make a note for the model
                if trimmed:
                    prev = trimmed[-1]
                    prev_sender = prev.get("sender") if isinstance(prev, dict) else None
                    if prev_sender and prev_sender != sender_label:
                        messages.append({
                            "role": "system",
                            "content": f"Note: a different user named {sender_label} is speaking now (previous speaker: {prev_sender})."
                        })
                messages.append({"role": "user", "content": f"[{sender_label}] {user_input}"})

            # Add an explicit instruction to always address the most recent sender by name
            if trimmed:
                recent = trimmed[-1]
                recent_sender = recent.get("sender") if isinstance(recent, dict) else None
            else:
                recent_sender = sender_label

            messages.append({
                "role": "system",
                "content": (
                    f"Important: The latest message is from '{sender_label}'. When you reply, begin the reply by addressing the most recent sender by name, e.g. '@{sender_label},' or '{sender_label},'. "
                    "Keep it short at the start (address the user) and then continue with the answer."
                )
            })

            # Ensure user messages include explicit sender labels for clarity
            labeled_messages = []
            for m in messages:
                if m.get("role") == "user":
                    # Prepend sender label if not already present
                    content = m.get("content", "")
                    if not content.startswith("[") and "::" not in content:
                        # If content already looks labeled (e.g. '[Name]'), skip
                        labeled_content = f"{content}"
                    else:
                        labeled_content = content
                    labeled_messages.append({"role": "user", "content": labeled_content})
                else:
                    labeled_messages.append(m)

            # Request a longer response (we increased limits earlier)
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-120b:together",
                messages=labeled_messages,
                temperature=0.7,
                max_tokens=500,
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.6
            )

            bot_response = completion.choices[0].message.content.strip()

            # Store assistant response with no sender (assistant)
            self.conversation_history.append({"role": "assistant", "content": bot_response, "sender": "moxie"})
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
        # guild.id -> asyncio.Task for recording loop
        self.recording_tasks = {}
        # guild.id -> last text channel used for transcripts
        self.recording_text_channel = {}

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
    
            
            sender_name = getattr(message.author, 'display_name', getattr(message.author, 'name', str(message.author)))
            print(f"[DEBUG] Received !moxie from {sender_name}: {query}")
            loop = asyncio.get_event_loop()
            reply = await loop.run_in_executor(None, self.ai_bot.get_response, query, sender_name)
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
                        # Start background recording loop for this guild
                        try:
                            self.start_transcription_loop(guild_id, new_vc, message.channel)
                            await message.channel.send(f"🦊 Joined {voice_channel.name} and started listening!")
                        except Exception as e:
                            await message.channel.send(f"🦊 Joined {voice_channel.name}, but couldn't start listening: {e}")
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

            # Only show typing if in a text channel
            if hasattr(message.channel, "trigger_typing"):
                await message.channel.trigger_typing()

            loop = asyncio.get_event_loop()

            # Step 1: Get raw TTS audio
            base_audio = await loop.run_in_executor(None, self.ai_bot.speak, text)

            if base_audio:
                # Step 2: Convert to high-pitched (childlike) and streamable
                processed_audio = await loop.run_in_executor(None, self.ai_bot.speak_childlike, base_audio)

             # Step 3: Play audio in voice channel using FFmpeg
                audio_source = discord.FFmpegPCMAudio(
                    source=processed_audio,
                    pipe=True,
                    executable=FFMPEG_PATH  # Use from .env or fallback
                )

                if vc.is_playing():
                    vc.stop()

                vc.play(audio_source)
                await message.channel.send(f"🦊 Said: {text}")
            else:
                await message.channel.send("🦊 Sorry, I couldn't generate the audio.")

    def start_transcription_loop(self, guild_id, voice_client, text_channel, chunk_duration=8):
        """
        Start a background task that records short chunks (chunk_duration seconds), transcribes
        per-speaker audio, posts transcripts to the provided text_channel, and has the bot respond.
        """
        if guild_id in self.recording_tasks and not self.recording_tasks[guild_id].done():
            print(f"Recording loop already running for guild {guild_id}")
            return

        self.recording_text_channel[guild_id] = text_channel

        async def _loop():
            print(f"Starting transcription loop for guild {guild_id}")
            while voice_client and voice_client.is_connected():
                try:
                    sink = discord.sinks.WaveSink()
                    voice_client.start_recording(sink, self.on_recording_finished, text_channel)
                    # Record for chunk_duration seconds
                    await asyncio.sleep(chunk_duration)
                    voice_client.stop_recording()
                    # small pause before next chunk
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"Recording loop error for guild {guild_id}: {e}")
                    await asyncio.sleep(2)
            print(f"Transcription loop ending for guild {guild_id}")

        task = asyncio.create_task(_loop())
        self.recording_tasks[guild_id] = task

    def stop_transcription_loop(self, guild_id):
        task = self.recording_tasks.get(guild_id)
        if task:
            task.cancel()
            self.recording_tasks.pop(guild_id, None)
            self.recording_text_channel.pop(guild_id, None)

    async def on_recording_finished(self, sink, text_channel):
        """
        Callback invoked when a recording chunk finishes. `sink` contains per-speaker audio.
        We transcribe each speaker's audio and post the results to text_channel.
        """
        print("Recording finished, processing audio...")
        try:
            recognizer = sr.Recognizer()

            # sink.audio_data may contain member -> AudioData records depending on discord.py version
            audio_items = []
            # Try multiple access patterns for compatibility
            if hasattr(sink, 'files') and sink.files:
                # sink.files: mapping of member -> io.BytesIO or Path
                for member, filelike in sink.files.items():
                    audio_items.append((member, filelike))
            elif hasattr(sink, 'audio_data') and sink.audio_data:
                for member, audio_list in sink.audio_data.items():
                    # audio_list may be list of AudioData objects; combine if needed
                    for audio_data in audio_list:
                        if hasattr(audio_data, 'file'):
                            audio_items.append((member, audio_data.file))
            else:
                # Fallback: iterate sink._audio_data if present
                for member, audio_data in getattr(sink, '_audio_data', {}).items():
                    try:
                        audio_items.append((member, audio_data.file))
                    except Exception:
                        pass

            # For each captured speaker audio, transcribe and respond
            for member, filelike in audio_items:
                try:
                    # Ensure BytesIO
                    if hasattr(filelike, 'read'):
                        audio_bytes = filelike.read()
                        filelike.seek(0)
                        audio_file_obj = io.BytesIO(audio_bytes)
                    else:
                        # if it's a path
                        with open(filelike, 'rb') as f:
                            audio_bytes = f.read()
                        audio_file_obj = io.BytesIO(audio_bytes)

                    # Use speech_recognition to transcribe
                    with sr.AudioFile(audio_file_obj) as source:
                        audio = recognizer.record(source)
                    try:
                        transcript = recognizer.recognize_google(audio)
                    except sr.UnknownValueError:
                        transcript = "[unintelligible]"
                    except sr.RequestError as e:
                        transcript = f"[transcription error: {e}]"

                    display_name = getattr(member, 'display_name', getattr(member, 'name', str(member)))
                    # Post transcript to text channel
                    try:
                        await text_channel.send(f"📝 {display_name} said: {transcript}")
                    except Exception:
                        print("Could not send transcript to channel")

                    # Let the AI respond to the transcribed text, addressing the sender
                    loop = asyncio.get_event_loop()
                    reply = await loop.run_in_executor(None, self.ai_bot.get_response, transcript, display_name)

                    # Speak reply and play into the voice channel
                    # Generate TTS audio
                    audio_bytes = await loop.run_in_executor(None, self.ai_bot.speak, reply)
                    if audio_bytes:
                        # Convert to childlike audio before playback
                        processed = await loop.run_in_executor(None, self.ai_bot.speak_childlike, audio_bytes)
                        guild_id = getattr(text_channel.guild, 'id', None)
                        vc = self.voice_clients_map.get(guild_id)
                        if vc and vc.is_connected():
                            audio_source = discord.FFmpegPCMAudio(source=processed, pipe=True, executable=FFMPEG_PATH)
                            if vc.is_playing():
                                vc.stop()
                            vc.play(audio_source)
                        # Also post the reply text to the channel
                        try:
                            await text_channel.send(f"🦊 Moxie (to {display_name}): {reply}")
                        except Exception:
                            print("Could not send reply text to channel")

                except Exception as e:
                    print(f"Error processing audio for member {member}: {e}")

        except Exception as e:
            print(f"Error in on_recording_finished: {e}")



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