from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os
import json
import requests
from pathlib import Path
import tempfile
import time
from typing import List, Dict
import re
import shutil

# Load environment variables
load_dotenv()

app = FastAPI(title="Text-to-Speech with Timestamps API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float

class TTSResponse(BaseModel):
    transcript: str
    timestamps: List[WordTimestamp]
    script: str  # Added script to response
    audio_file_path: str  # Added audio file path

# Initialize Groq client
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY environment variable not set")

client = Groq(api_key=api_key)

# Load prompts from JSON file
def load_prompts():
    try:
        with open('prompt.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback prompt if file doesn't exist
        return {
            "SCRIPT_GENERATION_PROMPT": """You are a professional script writer for short-form video content. 
            Convert the given article into an engaging, conversational script suitable for text-to-speech. 
            Make it sound natural, add transitions, and keep it engaging. Remove any formatting and make it flow well when spoken aloud."""
        }

def generate_script(article_content: str) -> str:
    """Generate TTS-friendly script from article content using Groq LLM"""
    try:
        prompts = load_prompts()
        
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": prompts["SCRIPT_GENERATION_PROMPT"]
                },
                {
                    "role": "user",
                    "content": article_content
                }
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None
        )
        
        return completion.choices[0].message.content.strip()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")

def text_to_speech(script_text: str, output_dir: str, filename: str = "speech.wav") -> str:
    """Convert script text to speech using Chatterbox TTS API with retry logic"""
    max_retries = 3
    base_delay = 5
    
    # Check if script is too long and truncate if necessary
    if len(script_text) > 5000:  # Chatterbox TTS reasonable limit
        print(f"Script too long ({len(script_text)} chars), truncating to 5000 chars...")
        script_text = script_text[:5000] + "..."
    
    for attempt in range(max_retries):
        try:
            speech_file_path = Path(output_dir) / filename
            
            # Chatterbox TTS API endpoint
            url = "https://ronniebasak--chatterbox-tts-api-generate.modal.run/"
            
            # Headers matching the curl request
            headers = {
                "accept": "application/json",
                "Authorization": "Bearer HACKERMAN2020HACKERMAN",
                "Content-Type": "application/json"
            }
            
            # Data payload matching the curl request
            data = {
                "text": "Floodwaters turn into a holy ritual! Meet UP cop Chandradeep Nishad, who's taking the internet by storm with his unusual response to Prayagraj's floods. He's waist-deep in water, inside his own home, offering flowers and prayers... saying Jai Ganga Maiya ki! You came knocking at my door, Mother!",
                "exaggeration": 0.4,
                "cfg_weight": 0.3
            }
            
            print(f"Attempting TTS conversion with Chatterbox API (attempt {attempt + 1}/{max_retries})...")
            print(f"Text length: {len(script_text)} characters")
            
            # Make the request with extended timeout for audio processing
            response = requests.post(url, headers=headers, json=data, timeout=120)
            
            # Handle rate limiting
            if response.status_code == 429:  # Too Many Requests
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff: 5s, 10s, 20s
                    print(f"Rate limit hit. Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                    continue
                else:
                    raise HTTPException(
                        status_code=429, 
                        detail={
                            "error": "Chatterbox TTS API rate limit exceeded",
                            "suggestion": "Please wait a few minutes before trying again",
                            "retry_after": "300"
                        }
                    )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: Invalid API token for Chatterbox TTS"
                )
            
            # Handle other HTTP errors
            if response.status_code != 200:
                print(f"API returned status code: {response.status_code}")
                print(f"Response text: {response.text}")
                
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Retrying after {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Chatterbox TTS API error: {response.status_code} - {response.text}"
                    )
            
            # Validate response content
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            
            print(f"Response content-type: {content_type}")
            print(f"Response content length: {content_length} bytes")
            
            # Check if we received valid audio data
            if content_length < 1000:  # Audio files should be reasonably large
                print(f"Warning: Response content seems too small for audio: {content_length} bytes")
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                    continue
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Invalid or empty audio response from Chatterbox TTS API"
                    )
            
            # Save the audio file
            with open(speech_file_path, 'wb') as f:
                f.write(response.content)
            
            # Verify the file was created successfully
            if not speech_file_path.exists():
                raise Exception("Failed to create audio file")
            
            
            file_size = speech_file_path.stat().st_size
            if file_size == 0:
                raise Exception("Generated audio file is empty")
            
            print(f"✅ TTS conversion completed successfully using Chatterbox API")
            print(f"📁 Audio file saved: {speech_file_path}")
            print(f"📊 File size: {file_size} bytes ({file_size/1024:.1f} KB)")
            
            return str(speech_file_path)
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"⏰ Request timeout on attempt {attempt + 1}. Waiting {delay}s before retry...")
                time.sleep(delay)
                continue
            else:
                raise HTTPException(
                    status_code=408, 
                    detail="Chatterbox TTS API request timed out after multiple attempts. The service might be busy."
                )
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"🌐 Network error: {e}. Waiting {delay} seconds before retry...")
                time.sleep(delay)
                continue
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Chatterbox TTS API network error: {str(e)}"
                )
                
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"❌ Unexpected error: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
                continue
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Chatterbox TTS conversion failed: {str(e)}"
                )
    
    # Fallback error (should never reach here)
    raise HTTPException(
        status_code=500, 
        detail="Chatterbox TTS conversion failed after all retry attempts"
    )

def transcribe_with_timestamps(audio_file_path: str) -> Dict:
    """Transcribe audio file and return timestamps"""
    try:
        with open(audio_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), file.read()),
                model="distil-whisper-large-v3-en",
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )
        
        return {
            "transcript": transcription.text,
            "words": [
                {
                    "word": word_info['word'],
                    "start": word_info['start'],
                    "end": word_info['end']
                }
                for word_info in transcription.words
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/generate-tts-timestamps", response_model=TTSResponse)
async def generate_tts_with_timestamps(
    content: str = Form(..., description="Article content to convert to speech with timestamps")
):
    """
    Generate TTS and return transcript with word-level timestamps from article content
    
    This endpoint:
    1. Cleans and validates the input content
    2. Generates a TTS-friendly script using AI
    3. Converts the script to speech audio using Chatterbox TTS
    4. Transcribes the audio to get word-level timestamps
    5. Returns both the transcript and detailed timestamps
    
    Args:
        content: The article content to process (accepts any text with automatic cleaning)
    
    Returns:
        TTSResponse: Contains transcript, script, audio file path, and list of word timestamps
    """
    output_dir = None
    
    try:
        # Clean and validate the content
        cleaned_content = content.replace('\r\n', '\n').replace('\r', '\n')
        cleaned_content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned_content)
        cleaned_content = cleaned_content.strip()
        
        if not cleaned_content:
            raise HTTPException(status_code=400, detail="Content cannot be empty after cleaning")
        
        print(f"🚀 Starting TTS pipeline for content ({len(cleaned_content)} chars)")
        
        # Create output directory in current working directory
        current_dir = Path.cwd()
        output_dir = current_dir / "audio_files"
        output_dir.mkdir(exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = int(time.time())
        audio_filename = f"speech_{timestamp}.wav"
        
        print(f"📁 Audio will be saved to: {output_dir / audio_filename}")
        
        # Step 1: Generate TTS-friendly script from article
        print("📝 Step 1: Generating script...")
        script_text = generate_script(cleaned_content)
        print(f"✅ Script generated ({len(script_text)} chars)")
        
        # Save script to file as well
        script_filename = f"script_{timestamp}.txt"
        script_path = output_dir / script_filename
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_text)
        print(f"📄 Script saved to: {script_path}")
        
        # Step 2: Convert script to speech audio using Chatterbox
        print("🎵 Step 2: Converting script to speech...")
        audio_file_path = text_to_speech(script_text, str(output_dir), audio_filename)
        
        # Step 3: Transcribe audio and extract word timestamps
        print("🎤 Step 3: Transcribing audio with timestamps...")
        transcription_result = transcribe_with_timestamps(audio_file_path)
        print(f"✅ Transcription completed ({len(transcription_result['words'])} words)")
        
        # Step 4: Format response with timestamps
        print("📊 Step 4: Formatting response...")
        timestamps = [
            WordTimestamp(
                word=word_data["word"],
                start=word_data["start"],
                end=word_data["end"]
            )
            for word_data in transcription_result["words"]
        ]
        
        # Get relative path for response
        relative_audio_path = str(Path("audio_files") / audio_filename)
        
        print(f"🎉 Pipeline completed successfully!")
        print(f"📄 Final transcript: {transcription_result['transcript'][:100]}...")
        print(f"⏰ Total timestamps: {len(timestamps)}")
        print(f"🎵 Audio file: {relative_audio_path}")
        print(f"📝 Script file: {Path('audio_files') / script_filename}")
        
        return TTSResponse(
            transcript=transcription_result["transcript"],
            timestamps=timestamps,
            script=script_text,
            audio_file_path=relative_audio_path
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"💥 Unexpected error in pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    finally:
        # Note: We don't clean up the output directory since user wants to keep files
        print("✅ Audio and script files preserved in ./audio_files/ directory")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "TTS with Timestamps API",
        "tts_provider": "Chatterbox TTS",
        "transcription_provider": "Groq Whisper"
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Text-to-Speech with Timestamps API",
        "version": "2.0",
        "tts_provider": "Chatterbox TTS (Open Source)",
        "endpoints": {
            "POST /generate-tts-timestamps": "Generate TTS and return transcript with word timestamps (Form-based)",
            "GET /health": "Health check",
            "GET /docs": "API documentation"
        },
        "usage": {
            "web": "Visit /docs to use the interactive form interface",
            "curl": "curl -X POST 'http://localhost:8000/generate-tts-timestamps' -d 'content=Your article here'",
            "python": "requests.post(url, data={'content': 'Your article here'})"
        },
        "features": [
            "Form-based input (handles special characters)",
            "AI script generation from articles", 
            "High-quality Chatterbox TTS conversion",
            "Word-level timestamp extraction",
            "Automatic retry logic with exponential backoff",
            "Comprehensive error handling"
        ],
        "note": "This API uses form data (not JSON) to handle articles with special characters"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)