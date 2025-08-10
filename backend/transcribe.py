import os
from groq import Groq
from dotenv import load_dotenv
import json

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)
filename = "speech.wav"

with open(filename, "rb") as file:
    transcription = client.audio.transcriptions.create(
        file=(filename, file.read()),
        model="distil-whisper-large-v3-en",
        response_format="verbose_json",
        timestamp_granularities=["word"],
    )

# Print full transcript
print("Transcript:\n", transcription.text)

# Print word-level timestamps
print("\nTimestamps per word:")
for word_info in transcription.words:
    print(f"{word_info['word']} - Start: {word_info['start']}s, End: {word_info['end']}s")
