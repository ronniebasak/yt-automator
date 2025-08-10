#!/bin/bash

# Simple Audio Format Converter Script
# Converts any audio file to PCM16 or PCM8 WAV format.
#
# Usage:
#     ./convert_audio.sh input.wav [pcm16|pcm8] [sample_rate] [output.wav]

# Default values
PCM_FORMAT="${2:-pcm16}"
SAMPLE_RATE="${3:-44100}"
INPUT_FILE="$1"

# Check if input file is provided
if [ -z "$INPUT_FILE" ]; then
    echo "❌ Error: Please provide an input file"
    echo "Usage: $0 input.wav [pcm16|pcm8] [sample_rate] [output.wav]"
    echo ""
    echo "Examples:"
    echo "  $0 input.wav"
    echo "  $0 input.mp3 pcm8"
    echo "  $0 input.flac pcm16 48000"
    echo "  $0 input.wav pcm16 44100 output.wav"
    exit 1
fi

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Error: Input file '$INPUT_FILE' does not exist"
    exit 1
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ Error: ffmpeg is not installed or not found in PATH"
    echo "Please install ffmpeg: https://ffmpeg.org/download.html"
    exit 1
fi

# Generate output filename if not provided
if [ -z "$4" ]; then
    BASENAME=$(basename "$INPUT_FILE" | sed 's/\.[^.]*$//')
    DIRNAME=$(dirname "$INPUT_FILE")
    OUTPUT_FILE="$DIRNAME/${BASENAME}_${PCM_FORMAT}.wav"
else
    OUTPUT_FILE="$4"
fi

# Map format names to ffmpeg codec names
case "$PCM_FORMAT" in
    pcm16)
        CODEC="pcm_s16le"
        ;;
    pcm8)
        CODEC="pcm_s8"
        ;;
    *)
        echo "❌ Error: Unsupported format '$PCM_FORMAT'. Use 'pcm16' or 'pcm8'"
        exit 1
        ;;
esac

# Show what we're doing
echo "🔄 Converting audio file..."
echo "  Input:       $INPUT_FILE"
echo "  Output:      $OUTPUT_FILE"
echo "  Format:      $PCM_FORMAT"
echo "  Sample Rate: $SAMPLE_RATE Hz"
echo ""

# Run ffmpeg conversion
ffmpeg -i "$INPUT_FILE" -acodec "$CODEC" -ar "$SAMPLE_RATE" -ac 1 -y "$OUTPUT_FILE"

# Check if conversion was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Conversion completed successfully!"
    echo "Output file: $OUTPUT_FILE"
    
    # Show output file info
    echo ""
    echo "📊 Output file information:"
    ffprobe -v quiet -print_format compact -show_streams "$OUTPUT_FILE" 2>/dev/null | grep "codec_name\|sample_rate\|channels\|bits_per_sample" || echo "Could not get file info"
else
    echo ""
    echo "❌ Conversion failed!"
    exit 1
fi
