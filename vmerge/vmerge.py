#!/usr/bin/env python3
"""
Random Video Cropper: Because sometimes you need to slice and dice videos
like a caffeinated chef with commitment issues.
"""

import subprocess
import random
import sys
import os
from pathlib import Path

def get_video_duration(video_path):
    """
    Ask ffprobe very politely how long this video is.
    Returns duration in seconds, or throws a tantrum if the file is being difficult.
    """
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-show_entries', 'format=duration',
        '-of', 'csv=p=0',
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except subprocess.CalledProcessError:
        print(f"Error: Couldn't get duration from {video_path}. Is it actually a video?")
        sys.exit(1)
    except ValueError:
        print(f"Error: Got weird duration data from {video_path}. FFprobe is having an existential crisis.")
        sys.exit(1)

def random_crop_video(reference_video, audio_file, prefix, inset_duration, offset=0):
    """
    The main event: randomly crop a video and slap some new audio on it.

    Args:
        reference_video: Your massive source video
        audio_file: The audio track to replace the original with
        prefix: What to call your shiny new video file
        inset_duration: How many seconds of video you want (the crop length)
        offset: Additional time offset from the random start point (default: 0)
    """

    # Check if files actually exist (because we're not magicians)
    if not os.path.exists(reference_video):
        print(f"Error: Can't find video file '{reference_video}'. Did it run away?")
        sys.exit(1)

    if not os.path.exists(audio_file):
        print(f"Error: Can't find audio file '{audio_file}'. Is it hiding?")
        sys.exit(1)

    # Get the video duration
    total_duration = get_video_duration(reference_video)
    print(f"Source video is {total_duration:.2f} seconds long (that's {total_duration/60:.1f} minutes of potential chaos)")

    # Calculate the maximum start time to avoid cropping beyond the end
    max_start_time = total_duration - inset_duration - offset

    if max_start_time <= 0:
        print(f"Error: Your inset duration ({inset_duration}s) + offset ({offset}s) is longer than the video ({total_duration}s)!")
        print("That's like trying to take a 10-minute shower with a 5-minute timer. Math says no.")
        sys.exit(1)

    # Pick a random start time (this is where the magic happens)
    random_start = random.uniform(0, max_start_time)
    actual_start = random_start + offset

    print(f"Rolling the dice... Starting at {actual_start:.2f} seconds for {inset_duration} seconds")

    # Generate output filename
    video_ext = Path(reference_video).suffix
    output_path = f"{prefix}_cropped{video_ext}"

    # The FFmpeg command that does all the heavy lifting
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output file without asking (living dangerously)
        '-ss', str(actual_start),  # Start time
        '-t', str(inset_duration),  # Duration
        '-i', reference_video,  # Input video
        '-i', audio_file,  # Input audio
        '-c:v', 'libx264',  # Video codec (streaming friendly)
        '-preset', 'fast',  # Encoding preset (good balance of speed vs quality)
        '-crf', '23',  # Quality setting (lower = better quality, higher file size)
        '-c:a', 'aac',  # Audio codec (universally loved)
        '-b:a', '128k',  # Audio bitrate (good enough for most ears)
        '-map', '0:v:0',  # Map video from first input
        '-map', '1:a:0',  # Map audio from second input
        '-movflags', '+faststart',  # Put metadata at beginning for web streaming
        output_path
    ]

    print(f"Cooking up your video with FFmpeg...")
    print(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        print(f"Success! Your masterpiece is ready: {output_path}")
        print(f"Duration: {inset_duration} seconds of pure randomly-selected goodness")

    except subprocess.CalledProcessError as e:
        print(f"Error: FFmpeg threw a fit and refused to cooperate.")
        print(f"Return code: {e.returncode}")
        sys.exit(1)

def main():
    if len(sys.argv) < 5:
        print("Usage: python video_cropper.py <reference_video> <audio_file> <prefix> <inset_duration> [offset]")
        print()
        print("Example: python video_cropper.py big_movie.mp4 cool_song.mp3 highlight 30 5")
        print("This grabs 30 seconds starting from a random point + 5 second offset")
        print()
        sys.exit(1)

    reference_video = sys.argv[1]
    audio_file = sys.argv[2]
    prefix = sys.argv[3]
    inset_duration = float(sys.argv[4])
    offset = float(sys.argv[5]) if len(sys.argv) > 5 else 0

    random_crop_video(reference_video, audio_file, prefix, inset_duration, offset)

if __name__ == "__main__":
    main()
