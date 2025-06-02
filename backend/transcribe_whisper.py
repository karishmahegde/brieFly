import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# transcribe_audio()
# Purpose: Transcribes audio files using OpenAI's Whisper model.
# Parameters:
#   - file_path (str): Path to the audio file (.mp3, .m4a, etc.)
# Returns:
#   - str: Transcribed text if successful, or an error message if failed.
# ─────────────────────────────────────────────────────────────────────────────
def transcribe_audio(file_path):
    try:
        # Initialize OpenAI API client using API key from environment variable
        client = openai.OpenAI(api_key = os.getenv("OPENAI_API_KEY"))   #Open AI API Key from https://platform.openai.com/docs/overview
        
        # Open the audio file in binary read mode
        with open(file_path, "rb") as audio_file:
            # Send the audio to OpenAI's Whisper model for transcription
            transcript = client.audio.transcriptions.create(
                model="whisper-1",  # Use Whisper v1 model for transcription
                file=audio_file
            )
        return transcript.text  # Return the transcribed text from the response
    except Exception as e:
        return f"❌ Error during transcription: {e}"