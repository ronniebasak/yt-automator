import io
import warnings
import modal

# Suppress known warnings from model dependencies
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Define the container image with Chatterbox TTS
image = (
    modal.Image.debian_slim()
    .pip_install(
        "chatterbox-tts",
        "torchaudio",
    )
)

app = modal.App("chatterbox-tts", image=image)

@app.cls(
    gpu="T4",
    scaledown_window=300,
)
class ChatterboxTTS:
    @modal.enter()
    def load_model(self):
        from chatterbox.tts import ChatterboxTTS
        self.model = ChatterboxTTS.from_pretrained(device="cuda")

    @modal.method()
    def generate(
        self,
        text: str,
        audio_prompt_path: str = None,
        exaggeration: float = 0.5,
        cfg_weight: float = 0.5
    ) -> bytes:
        """Generate speech from text and return audio bytes"""
        wav = self.model.generate(
            text,
            audio_prompt_path=audio_prompt_path,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight
        )

        # Convert to bytes
        import torchaudio
        buffer = io.BytesIO()
        torchaudio.save(buffer, wav, self.model.sr, format="wav")
        buffer.seek(0)
        return buffer.getvalue()

@app.local_entrypoint()
def main(text: str, exaggeration: float = 0.5, cfg_weight: float = 0.5):
    """Local entrypoint to test the TTS"""
    tts = ChatterboxTTS()
    audio_bytes = tts.generate.remote(text, exaggeration=exaggeration, cfg_weight=cfg_weight)

    with open("output.wav", "wb") as f:
        f.write(audio_bytes)

    print(f"Generated audio saved to output.wav")

@app.function()
@modal.fastapi_endpoint(method="POST")
def api_generate(text: str, exaggeration: float = 0.5, cfg_weight: float = 0.5):
    """Web API endpoint for TTS generation"""
    tts = ChatterboxTTS()
    audio_bytes = tts.generate.remote(text, exaggeration=exaggeration, cfg_weight=cfg_weight)

    return modal.Response(
        audio_bytes,
        headers={"Content-Type": "audio/wav"}
    )
