#!/usr/bin/env python3
"""
Video TTS Generator

Workflow:
1. Parse JSX/XML file to data models
2. Generate TTS audio for each scene
3. Update scene durations based on audio
4. Add 1.5s offsets between scenes (except first)
5. Merge all audio files
6. Write final output
"""

import os
import requests
import subprocess
from pathlib import Path
from typing import List, Optional
import tempfile
import json
import dotenv

# Import your parser (assuming it's in video_script_parser.py)
from fffinder.steps.script_parser import VideoScriptParser, VideoContainer, Scene, VoiceOver

dotenv.load_dotenv()

class TTSGenerator:
    """Handles TTS generation via API"""
    
    def __init__(self, api_url: str, auth_token: Optional[str] = None):
        self.api_url = api_url
        self.auth_token = auth_token or os.getenv('TTS_AUTH_TOKEN')
        
        if not self.auth_token:
            raise ValueError("TTS_AUTH_TOKEN environment variable is required")
    
    def generate_audio(self, text: str, exaggeration: float = 0.2) -> bytes:
        """Generate audio from text using TTS API"""
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "text": text,
            "exaggeration": exaggeration
        }
        
        print(f"Generating TTS for: {text[:50]}...")
        
        response = requests.post(self.api_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"TTS API error {response.status_code}: {response.text}")
        
        return response.content
    
    def save_audio(self, audio_data: bytes, filepath: str) -> str:
        """Save audio data to file"""
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        return filepath


class AudioProcessor:
    """Handles audio processing and merging using ffmpeg"""
    
    @staticmethod
    def get_audio_duration(filepath: str) -> float:
        """Get duration of audio file in seconds using ffprobe"""
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_format', filepath
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        except (subprocess.CalledProcessError, KeyError, ValueError) as e:
            raise Exception(f"Failed to get audio duration for {filepath}: {e}")
    
    @staticmethod
    def create_silence(duration: float, output_path: str) -> str:
        """Create a silent audio file of specified duration"""
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', f'anullsrc=duration={duration}',
            '-y', output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to create silence: {e}")
    
    @staticmethod
    def merge_audio_files(audio_files: List[str], output_path: str) -> str:
        """Merge multiple audio files into one using ffmpeg"""
        if not audio_files:
            raise ValueError("No audio files to merge")
        
        if len(audio_files) == 1:
            # Just copy the single file
            cmd = ['ffmpeg', '-i', audio_files[0], '-y', output_path]
        else:
            # Create filter complex for concatenation
            inputs = []
            for file in audio_files:
                inputs.extend(['-i', file])
            
            filter_complex = f"concat=n={len(audio_files)}:v=0:a=1[out]"
            
            cmd = ['ffmpeg'] + inputs + ['-filter_complex', filter_complex, 
                   '-map', '[out]', '-y', output_path]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to merge audio files: {e}")


class VideoTTSProcessor:
    """Main processor for video TTS generation"""
    
    def __init__(self, tts_api_url: str, auth_token: Optional[str] = None):
        self.tts = TTSGenerator(tts_api_url, auth_token)
        self.audio_processor = AudioProcessor()
        self.temp_dir = None
    
    def process_video_script(self, script_file_path: str, output_path: str, 
                           scene_offset: float = 1.5, exaggeration: float = 0.2) -> str:
        """
        Main processing function
        
        Args:
            script_file_path: Path to JSX/XML script file
            output_path: Path for final merged audio file
            scene_offset: Offset between scenes in seconds (default 1.5s)
            exaggeration: TTS exaggeration level (default 0.2)
        """
        
        # Create temporary directory for intermediate files
        self.temp_dir = tempfile.mkdtemp(prefix="video_tts_")
        temp_path = Path(self.temp_dir)
        
        try:
            # Step 1: Parse script file
            print("Step 1: Parsing script file...")
            container = self._parse_script_file(script_file_path)
            
            # Step 2: Generate TTS for each scene
            print("Step 2: Generating TTS audio...")
            scene_audio_files = self._generate_scene_audio(container, temp_path, exaggeration)
            
            # Step 3: Update scene durations
            print("Step 3: Updating scene durations...")
            self._update_scene_durations(container, scene_audio_files)
            
            # Step 4: Add offsets between scenes
            print("Step 4: Adding scene offsets...")
            final_audio_files = self._add_scene_offsets(scene_audio_files, temp_path, scene_offset)
            
            # Step 5: Merge all audio
            print("Step 5: Merging audio files...")
            final_output = self.audio_processor.merge_audio_files(final_audio_files, output_path)
            
            print(f"✅ Video TTS generation complete: {final_output}")
            return final_output
            
        finally:
            # Cleanup temporary files
            self._cleanup_temp_files()
    
    def _parse_script_file(self, script_file_path: str) -> VideoContainer:
        """Parse the script file into data models"""
        with open(script_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        parser = VideoScriptParser()
        return parser.parse_script(content)
    
    def _generate_scene_audio(self, container: VideoContainer, temp_path: Path, 
                            exaggeration: float) -> List[str]:
        """Generate TTS audio for each scene"""
        scene_audio_files = []
        
        for i, scene in enumerate(container.scenes):
            if not scene.voice_over:
                print(f"  Skipping scene {i+1} '{scene.name}' - no voice over")
                continue
            
            # Get full text for the scene
            full_text = scene.voice_over.serialize_to_text()
            
            # Generate TTS audio
            audio_data = self.tts.generate_audio(full_text, exaggeration)
            
            # Save to temporary file
            audio_file = temp_path / f"scene_{i:03d}_{scene.name}.wav"
            self.tts.save_audio(audio_data, str(audio_file))
            scene_audio_files.append(str(audio_file))
            
            print(f"  Generated audio for scene {i+1}: {scene.name}")
        
        return scene_audio_files
    
    def _update_scene_durations(self, container: VideoContainer, audio_files: List[str]):
        """Update scene durations based on actual audio length"""
        scene_index = 0
        
        for scene in container.scenes:
            if not scene.voice_over:
                continue
            
            if scene_index < len(audio_files):
                audio_duration = self.audio_processor.get_audio_duration(audio_files[scene_index])
                
                # Update voice over timing - use offset to store actual audio duration
                scene.voice_over.start_time = 0.0  # Will be set when calculating final timeline
                scene.voice_over.inset = 0.0
                scene.voice_over.offset = audio_duration  # Store actual duration in offset
                
                print(f"  Scene '{scene.name}': {audio_duration:.2f}s")
                scene_index += 1
    
    def _add_scene_offsets(self, scene_audio_files: List[str], temp_path: Path, 
                          scene_offset: float) -> List[str]:
        """Add offsets between scenes and prepare final audio list"""
        if not scene_audio_files:
            return []
        
        final_files = []
        
        # First scene - no offset
        final_files.append(scene_audio_files[0])
        
        # Subsequent scenes - add offset before each
        for i in range(1, len(scene_audio_files)):
            # Create silence file for offset
            silence_file = temp_path / f"offset_{i:03d}.wav"
            self.audio_processor.create_silence(scene_offset, str(silence_file))
            
            # Add silence then scene audio
            final_files.append(str(silence_file))
            final_files.append(scene_audio_files[i])
            
            print(f"  Added {scene_offset}s offset before scene {i+1}")
        
        return final_files
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"Cleaned up temporary files: {self.temp_dir}")


def main():
    """Example usage"""
    
    # Configuration
    TTS_API_URL = "https://ronniebasak--chatterbox-tts-api-generate.modal.run/"
    SCRIPT_FILE = "script.xml"  # Your JSX/XML file path
    OUTPUT_FILE = "final_video_audio.wav"
    
    # Initialize processor
    processor = VideoTTSProcessor(TTS_API_URL)
    
    try:
        # Process the video script
        result = processor.process_video_script(
            script_file_path=SCRIPT_FILE,
            output_path=OUTPUT_FILE,
            scene_offset=0.5,  # 1.5 second offset between scenes
            exaggeration=0.4   # TTS exaggeration level
        )
        
        print(f"\n🎉 Success! Final audio saved to: {result}")
        
        # Optional: Print final duration
        duration = AudioProcessor.get_audio_duration(result)
        print(f"📊 Total duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())