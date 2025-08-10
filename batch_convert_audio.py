#!/usr/bin/env python3
"""
Batch Audio Format Converter
Converts multiple audio files to PCM16 or PCM8 format in batch.

Usage:
    python batch_convert_audio.py [--format pcm16|pcm8] [--sample-rate 44100] [--input-dir ./] [--output-dir ./converted/]
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
import glob

# Supported audio file extensions
AUDIO_EXTENSIONS = ['.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a', '.wma']

def check_ffmpeg():
    """Check if ffmpeg is installed and available."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def convert_single_file(input_file, output_file, pcm_format='pcm16', sample_rate=44100):
    """Convert a single audio file to specified PCM format."""
    
    # Map format names to ffmpeg codec names
    codec_map = {
        'pcm16': 'pcm_s16le',  # 16-bit signed integer PCM
        'pcm8': 'pcm_s8'       # 8-bit signed integer PCM
    }
    
    codec = codec_map[pcm_format]
    
    # Build ffmpeg command
    cmd = [
        'ffmpeg',
        '-i', input_file,           # Input file
        '-acodec', codec,           # Audio codec
        '-ar', str(sample_rate),    # Sample rate
        '-ac', '1',                 # Convert to mono
        '-y',                       # Overwrite output file
        output_file                 # Output file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def find_audio_files(directory, recursive=True):
    """Find all audio files in the specified directory."""
    audio_files = []
    
    if recursive:
        for ext in AUDIO_EXTENSIONS:
            pattern = os.path.join(directory, '**', f'*{ext}')
            audio_files.extend(glob.glob(pattern, recursive=True))
            pattern = os.path.join(directory, '**', f'*{ext.upper()}')
            audio_files.extend(glob.glob(pattern, recursive=True))
    else:
        for ext in AUDIO_EXTENSIONS:
            pattern = os.path.join(directory, f'*{ext}')
            audio_files.extend(glob.glob(pattern))
            pattern = os.path.join(directory, f'*{ext.upper()}')
            audio_files.extend(glob.glob(pattern))
    
    return list(set(audio_files))  # Remove duplicates

def main():
    parser = argparse.ArgumentParser(
        description="Batch convert audio files to PCM16 or PCM8 WAV format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Convert all audio files in current directory to PCM16
    python batch_convert_audio.py
    
    # Convert all audio files to PCM8 format
    python batch_convert_audio.py --format pcm8
    
    # Convert files from specific input directory to output directory
    python batch_convert_audio.py --input-dir ./audio_files --output-dir ./converted --format pcm16
    
    # Convert with custom sample rate
    python batch_convert_audio.py --sample-rate 48000
        """
    )
    
    parser.add_argument('--format', choices=['pcm16', 'pcm8'], default='pcm16',
                       help='PCM format (default: pcm16)')
    parser.add_argument('--sample-rate', type=int, default=44100,
                       help='Sample rate in Hz (default: 44100)')
    parser.add_argument('--input-dir', default='./',
                       help='Input directory path (default: current directory)')
    parser.add_argument('--output-dir', default='./converted/',
                       help='Output directory path (default: ./converted/)')
    parser.add_argument('--recursive', action='store_true',
                       help='Search for files recursively in subdirectories')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be converted without actually converting')
    
    args = parser.parse_args()
    
    # Check if ffmpeg is available
    if not check_ffmpeg():
        print("❌ Error: ffmpeg is not installed or not found in PATH")
        print("Please install ffmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    # Check if input directory exists
    if not os.path.exists(args.input_dir):
        print(f"❌ Error: Input directory '{args.input_dir}' does not exist")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    if not args.dry_run:
        os.makedirs(args.output_dir, exist_ok=True)
    
    # Find all audio files
    print(f"🔍 Searching for audio files in '{args.input_dir}'...")
    audio_files = find_audio_files(args.input_dir, args.recursive)
    
    if not audio_files:
        print("❌ No audio files found!")
        print(f"Supported extensions: {', '.join(AUDIO_EXTENSIONS)}")
        sys.exit(1)
    
    print(f"📁 Found {len(audio_files)} audio file(s)")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - Files that would be converted:")
        for i, input_file in enumerate(audio_files, 1):
            input_path = Path(input_file)
            output_name = f"{input_path.stem}_{args.format}.wav"
            output_path = Path(args.output_dir) / output_name
            print(f"  {i:2d}. {input_file} → {output_path}")
        print(f"\nFormat: {args.format.upper()}")
        print(f"Sample Rate: {args.sample_rate} Hz")
        return
    
    # Convert each file
    successful = 0
    failed = 0
    
    print(f"\n🔄 Converting to {args.format.upper()} format...")
    print(f"Sample Rate: {args.sample_rate} Hz")
    print(f"Output Directory: {args.output_dir}")
    print("─" * 50)
    
    for i, input_file in enumerate(audio_files, 1):
        input_path = Path(input_file)
        output_name = f"{input_path.stem}_{args.format}.wav"
        output_path = Path(args.output_dir) / output_name
        
        print(f"[{i:2d}/{len(audio_files)}] Converting {input_path.name}... ", end="", flush=True)
        
        success = convert_single_file(
            str(input_path),
            str(output_path),
            args.format,
            args.sample_rate
        )
        
        if success:
            print("✅")
            successful += 1
        else:
            print("❌")
            failed += 1
    
    # Summary
    print("─" * 50)
    print(f"🎉 Batch conversion completed!")
    print(f"✅ Successful: {successful}")
    if failed > 0:
        print(f"❌ Failed: {failed}")
    print(f"📁 Output directory: {args.output_dir}")

if __name__ == '__main__':
    main()
