import io
import warnings
import modal
from fastapi import Depends, HTTPException, status, Response, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union
import json

# Suppress known warnings from model dependencies
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Define the container image with WhisperX and dependencies
image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04", add_python="3.10"
    )
    .apt_install(["ffmpeg", "libsndfile1"])
    .pip_install(
            "torch==2.1.0+cu118",
            "torchaudio==2.1.0+cu118",
            "whisperx>=3.1.0",
            "faster-whisper",
            "pyannote.audio==3.1.1",
            "fastapi[standard]",
            "numpy<2.0.0",
            "numba",
            "pydub",
            "python-multipart",
            "lightning==2.1.0",
            extra_options="--extra-index-url https://download.pytorch.org/whl/cu118"
        )
    .run_commands(
        # Set environment variables
        "export TORCH_AUDIO_BACKEND=soundfile",
        # Verify CUDA installation
        "nvidia-smi || echo 'NVIDIA driver check'",
        # Download alignment models during build
        "python -c \"import warnings; warnings.filterwarnings('ignore'); import whisperx; whisperx.load_align_model('en', 'cpu')\" || true",
    )
)

app = modal.App("whisperx-transcription", image=image)

# Authentication scheme
auth_scheme = HTTPBearer()


@app.cls(
    gpu="T4",
    scaledown_window=300,  # Fixed: use scaledown_window instead of container_idle_timeout
)
class WhisperXTranscriber:
    @modal.enter()
    def load_models(self):
        """Load WhisperX models on container startup"""
        import whisperx
        import gc
        import warnings
        import os
        import torch

        # Suppress deprecation warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=UserWarning)

        # Set environment variables for better compatibility
        os.environ["TORCH_AUDIO_BACKEND"] = "soundfile"

        # Enable TF32 for better performance on newer GPUs
        if torch.cuda.is_available():
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "float32"

        # Load the transcription model
        print("Loading WhisperX transcription model...")
        try:
            self.transcription_model = whisperx.load_model(
                "large-v2", self.device, compute_type=self.compute_type
            )
            print("✓ Transcription model loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load large-v2 model, falling back to base: {e}")
            self.transcription_model = whisperx.load_model(
                "base", self.device, compute_type=self.compute_type
            )

        # Pre-load alignment model for English (most common)
        print("Loading alignment model for English...")
        try:
            self.align_model_en, self.align_metadata_en = whisperx.load_align_model(
                language_code="en", device=self.device
            )
            # Store for other languages (loaded on demand)
            self.align_models = {"en": (self.align_model_en, self.align_metadata_en)}
            print("✓ Alignment model loaded successfully")
        except Exception as e:
            print(f"Warning: Could not pre-load alignment model: {e}")
            self.align_models = {}

        print("Models loaded successfully!")

    def _load_alignment_model(self, language_code: str):
        """Load alignment model for specific language"""
        import whisperx
        import warnings

        if language_code not in self.align_models:
            print(f"Loading alignment model for language: {language_code}")
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    model, metadata = whisperx.load_align_model(
                        language_code=language_code, device=self.device
                    )
                self.align_models[language_code] = (model, metadata)
                print(f"✓ Alignment model for {language_code} loaded successfully")
            except Exception as e:
                print(
                    f"Warning: Could not load alignment model for {language_code}: {e}"
                )
                # Fall back to English model if available
                if "en" in self.align_models:
                    print("Falling back to English alignment model")
                    self.align_models[language_code] = self.align_models["en"]
                else:
                    raise Exception(f"No alignment model available for {language_code}")

        return self.align_models[language_code]

    @modal.method()
    def convert_audio_to_bytes(
        self, audio_file_bytes: bytes, original_filename: str
    ) -> bytes:
        """
        Convert uploaded audio file to WAV format suitable for WhisperX

        Args:
            audio_file_bytes: Raw bytes from uploaded file
            original_filename: Original filename to determine format

        Returns:
            WAV format audio bytes
        """
        import tempfile
        import os
        from pydub import AudioSegment

        temp_output_path = None
        temp_input_path = None
        try:
            # Save uploaded bytes to temporary file with original extension
            file_ext = os.path.splitext(original_filename)[1].lower()
            if not file_ext:
                file_ext = ".wav"  # Default to wav if no extension

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=file_ext
            ) as temp_input:
                temp_input.write(audio_file_bytes)
                temp_input_path = temp_input.name

            # Load audio with pydub (supports many formats)
            try:
                audio = AudioSegment.from_file(temp_input_path)
            except Exception as e:
                # Try to infer format if auto-detection fails
                if file_ext in [".mp3"]:
                    audio = AudioSegment.from_mp3(temp_input_path)
                elif file_ext in [".wav"]:
                    audio = AudioSegment.from_wav(temp_input_path)
                elif file_ext in [".flac"]:
                    audio = AudioSegment.from_file(temp_input_path, format="flac")
                elif file_ext in [".m4a", ".mp4"]:
                    audio = AudioSegment.from_file(temp_input_path, format="mp4")
                elif file_ext in [".ogg"]:
                    audio = AudioSegment.from_ogg(temp_input_path)
                else:
                    raise Exception(f"Unsupported audio format: {file_ext}")

            # Convert to WAV format suitable for WhisperX
            # - 16kHz sample rate (WhisperX default)
            # - Mono channel
            # - 16-bit depth
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

            # Export to bytes
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".wav"
            ) as temp_output:
                audio.export(temp_output.name, format="wav")

                with open(temp_output.name, "rb") as f:
                    wav_bytes = f.read()

                os.unlink(temp_output.name)

            # Clean up input file
            os.unlink(temp_input_path)

            return wav_bytes

        except Exception as e:
            # Clean up on error
            if "temp_input_path" in locals():
                try:
                    os.unlink(temp_input_path)
                except:
                    pass
            if "temp_output_path" in locals():
                try:
                    os.unlink(temp_output_path)
                except:
                    pass
            raise Exception(f"Audio conversion failed: {str(e)}")

    @modal.method()
    def transcribe_with_alignment(
        self,
        audio_bytes: bytes,
        batch_size: int = 16,
        language: Optional[str] = None,
        return_char_alignments: bool = False,
        enable_diarization: bool = False,
        hf_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio with word-level timestamps using forced alignment

        Args:
            audio_bytes: Audio file bytes
            batch_size: Batch size for transcription (reduce if low on GPU memory)
            language: Language code (auto-detect if None)
            return_char_alignments: Whether to return character-level alignments
            enable_diarization: Whether to perform speaker diarization
            hf_token: HuggingFace token for diarization (required if enable_diarization=True)

        Returns:
            Dictionary containing transcription results with word-level timestamps
        """
        import whisperx
        import tempfile
        import os
        import gc
        import torch
        import warnings

        # Suppress warnings during processing
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            results = {}

            try:
                # Save audio bytes to temporary file
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".wav"
                ) as temp_audio:
                    temp_audio.write(audio_bytes)
                    temp_audio_path = temp_audio.name

                # Load audio
                audio = whisperx.load_audio(temp_audio_path)

                # Step 1: Transcribe with Whisper
                print("Starting transcription...")
                transcription_result = self.transcription_model.transcribe(
                    audio, batch_size=batch_size, language=language
                )

                detected_language = transcription_result["language"]
                results["language"] = detected_language
                results["segments_before_alignment"] = transcription_result["segments"]

                print(f"Transcription complete. Detected language: {detected_language}")

                # Step 2: Forced alignment for word-level timestamps
                print("Starting forced alignment...")
                align_model, align_metadata = self._load_alignment_model(
                    detected_language
                )

                alignment_result = whisperx.align(
                    transcription_result["segments"],
                    align_model,
                    align_metadata,
                    audio,
                    self.device,
                    return_char_alignments=return_char_alignments,
                )

                results["segments"] = alignment_result["segments"]
                results["word_segments"] = alignment_result.get("word_segments", [])

                if return_char_alignments:
                    results["char_segments"] = alignment_result.get("char_segments", [])

                print("Forced alignment complete.")

                # Step 3: Speaker diarization (optional)
                if enable_diarization:
                    if not hf_token:
                        raise ValueError(
                            "HuggingFace token required for speaker diarization"
                        )

                    print("Starting speaker diarization...")
                    try:
                        diarize_model = whisperx.DiarizationPipeline(
                            use_auth_token=hf_token, device=self.device
                        )

                        diarization_result = diarize_model(audio)

                        # Assign speakers to words
                        final_result = whisperx.assign_word_speakers(
                            diarization_result, alignment_result
                        )

                        results["segments"] = final_result["segments"]
                        results["speakers"] = list(
                            set(
                                [
                                    word.get("speaker", "UNKNOWN")
                                    for segment in final_result["segments"]
                                    for word in segment.get("words", [])
                                ]
                            )
                        )

                        print("✓ Speaker diarization complete.")

                    except Exception as e:
                        print(f"Warning: Speaker diarization failed: {e}")
                        print("Continuing without speaker labels...")
                        # Continue without diarization

                # Clean up temporary file
                os.unlink(temp_audio_path)

                # Clean up GPU memory
                gc.collect()
                torch.cuda.empty_cache()

                return results

            except Exception as e:
                # Clean up on error
                if "temp_audio_path" in locals():
                    try:
                        os.unlink(temp_audio_path)
                    except:
                        pass

                gc.collect()
                torch.cuda.empty_cache()
                raise e

    @modal.method()
    def get_word_level_timestamps(self, audio_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Simplified method to get just word-level timestamps

        Returns:
            List of dictionaries with word, start, end, confidence
        """
        result = self.transcribe_with_alignment(audio_bytes)

        words = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                words.append(
                    {
                        "word": word_info.get("word", ""),
                        "start": word_info.get("start", 0.0),
                        "end": word_info.get("end", 0.0),
                        "confidence": word_info.get("score", 0.0),
                    }
                )

        return words


@app.local_entrypoint()
def main(
    audio_file: str,
    language: str = None,
    batch_size: int = 16,
    enable_diarization: bool = False,
    output_file: str = "transcription_result.json",
):
    """Local entrypoint to test WhisperX transcription"""

    # Read audio file
    with open(audio_file, "rb") as f:
        audio_bytes = f.read()

    # Initialize transcriber
    transcriber = WhisperXTranscriber()

    # Perform transcription with alignment
    result = transcriber.transcribe_with_alignment.remote(
        audio_bytes=audio_bytes,
        language=language,
        batch_size=batch_size,
        enable_diarization=enable_diarization,
    )

    # Save results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Transcription results saved to {output_file}")

    # Print summary
    print(f"\nSummary:")
    print(f"Detected language: {result['language']}")
    print(f"Number of segments: {len(result['segments'])}")

    # Print first few words with timestamps
    print(f"\nFirst 10 words with timestamps:")
    word_count = 0
    for segment in result["segments"]:
        for word_info in segment.get("words", []):
            if word_count < 10:
                print(
                    f"  {word_info.get('word', '')}: {word_info.get('start', 0):.2f}s - {word_info.get('end', 0):.2f}s"
                )
                word_count += 1


from pydantic import BaseModel


class TranscriptionRequest(BaseModel):
    audio_data: str  # base64 encoded audio
    language: Optional[str] = None
    batch_size: int = 16
    return_char_alignments: bool = False
    enable_diarization: bool = False
    hf_token: Optional[str] = None
    words_only: bool = False  # If True, return only word timestamps


@app.function(secrets=[modal.Secret.from_name("chatterbox-auth-token")])
@modal.fastapi_endpoint(method="POST", docs=True)
def api_transcribe_file(
    audio_file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    batch_size: int = Form(16),
    return_char_alignments: bool = Form(False),
    enable_diarization: bool = Form(False),
    hf_token: Optional[str] = Form(None),
    words_only: bool = Form(False),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    """
    WhisperX transcription with file upload support

    Accepts various audio formats (MP3, WAV, FLAC, M4A, OGG, etc.)
    and automatically converts them to the format required by WhisperX.
    """
    import os

    # Validate Bearer token
    if token.credentials != os.environ["AUTH_TOKEN"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate file type
    allowed_extensions = {
        ".mp3",
        ".wav",
        ".flac",
        ".m4a",
        ".mp4",
        ".ogg",
        ".webm",
        ".aac",
    }
    file_ext = os.path.splitext(audio_file.filename or "")[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {file_ext}. Supported formats: {', '.join(allowed_extensions)}",
        )

    try:
        # Read uploaded file
        audio_file_bytes = audio_file.file.read()

        if len(audio_file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio file"
            )

        # Initialize transcriber
        transcriber = WhisperXTranscriber()

        # Convert audio to suitable format
        converted_audio_bytes = transcriber.convert_audio_to_bytes.remote(
            audio_file_bytes, audio_file.filename or "audio.wav"
        )

        if words_only:
            # Return simplified word timestamps
            words = transcriber.get_word_level_timestamps.remote(converted_audio_bytes)
            return {"words": words}
        else:
            # Return full transcription results
            result = transcriber.transcribe_with_alignment.remote(
                audio_bytes=converted_audio_bytes,
                batch_size=batch_size,
                language=language,
                return_char_alignments=return_char_alignments,
                enable_diarization=enable_diarization,
                hf_token=hf_token,
            )
            return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        )


@app.function(secrets=[modal.Secret.from_name("chatterbox-auth-token")])
@modal.fastapi_endpoint(method="POST", docs=True)
def api_transcribe(
    body: TranscriptionRequest,
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    """
    WhisperX transcription with forced alignment API endpoint

    Set words_only=True to get simplified word timestamps output
    """
    import os
    import base64

    # Validate Bearer token
    if token.credentials != os.environ["AUTH_TOKEN"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode audio data
        audio_bytes = base64.b64decode(body.audio_data)

        # Initialize transcriber
        transcriber = WhisperXTranscriber()

        if body.words_only:
            # Return simplified word timestamps
            words = transcriber.get_word_level_timestamps.remote(audio_bytes)
            return {"words": words}
        else:
            # Return full transcription results
            result = transcriber.transcribe_with_alignment.remote(
                audio_bytes=audio_bytes,
                batch_size=body.batch_size,
                language=body.language,
                return_char_alignments=body.return_char_alignments,
                enable_diarization=body.enable_diarization,
                hf_token=body.hf_token,
            )
            return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        )
