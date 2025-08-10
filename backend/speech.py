import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import json

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

with open('prompt.json', 'r') as f:
    prompts = json.load(f)

# This will save the audio file in the same folder as your Python script
speech_file_path = Path(__file__).parent / "speech.wav"

# Your script content (cleaned up for TTS)
script_text = """
Life comes full circle in the most unexpected ways. 
Meet Nithin Kamath, CEO of Zerodha, India's largest stockbroker. He and his brother bootstrapped the company in 2010.
But what you might not know is that Deepak Shenoy, the CEO of Capitalmind Financial Services, was one of the first people to lend his credibility to Zerodha.
He even had his name on their website as an advisor!
Fast forward to today, and Nithin Kamath just invested in Deepak Shenoy's Capitalmind Financial Services through Rainmatter, Zerodha's long-term investment initiative.
But here's the crazy part... Capitalmind just received a mutual fund license, and this is their first external institutional funding!
So, what's the big deal? This investment shows that life comes full circle - Nithin Kamath is now backing the man who helped him succeed!
With a non-interfering investment philosophy, Rainmatter is a perfect fit for Capitalmind. The synergy between Zerodha and Capitalmind is undeniable.
Will this investment change the game for Capitalmind? Share your thoughts!
"""

# Direct API call to Groq TTS endpoint
url = "https://api.groq.com/openai/v1/audio/speech"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "playai-tts",
    "voice": "Fritz-PlayAI",
    "input": script_text,
    "response_format": "wav"
}

try:
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  # Raises an HTTPError for bad responses
    
    # Save the audio file
    with open(speech_file_path, 'wb') as f:
        f.write(response.content)
    
    print(f"Audio saved to: {speech_file_path}")
    
except requests.exceptions.RequestException as e:
    print(f"Error making request: {e}")
except Exception as e:
    print(f"An error occurred: {e}")