"""Generate voiceover audio using Eleven Labs v3 via fal.ai."""

import os
from typing import Optional

import fal_client
import requests

from .utils import get_fal_key, api_call_with_retry


# Available voices
VOICES = ["George", "Aria", "Rachel", "Sam", "Charlie", "Emily"]

# Voice descriptions for reference
VOICE_DESCRIPTIONS = {
    "George": "Professional male voice, clear and authoritative - good for business",
    "Aria": "Professional female voice, warm and engaging - good for training",
    "Rachel": "Conversational female voice - good for casual content",
    "Sam": "Young male voice, energetic - good for marketing and tech",
    "Charlie": "Neutral, authoritative voice - good for documentaries",
    "Emily": "Soft female voice, calming - good for wellness content",
}


def _init_fal():
    """Initialize fal client with API key."""
    os.environ["FAL_KEY"] = get_fal_key()


def generate_voiceover(
    text: str,
    slide_number: int,
    output_dir: str = "./audio",
    voice: str = "George"
) -> str:
    """Generate voiceover audio for a slide narration.

    Args:
        text: Narration script text.
        slide_number: Slide number for filename.
        output_dir: Directory to save audio files.
        voice: Voice name (George, Aria, Rachel, Sam, Charlie, Emily).

    Returns:
        Path to the generated audio file.
    """
    _init_fal()

    if voice not in VOICES:
        print(f"Warning: Voice '{voice}' not recognized. Using 'George'.")
        voice = "George"

    def _generate():
        return fal_client.subscribe(
            "fal-ai/elevenlabs/tts/eleven-v3",
            arguments={
                "text": text,
                "voice": voice,
                "speed": 1.0,
                "output_format": "mp3_44100_128",
            },
        )

    result = api_call_with_retry(_generate)

    audio_url = result["audio"]["url"]

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"narration_{slide_number:02d}.mp3")

    response = requests.get(audio_url)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path


def generate_voiceover_batch(
    narrations: list[str],
    output_dir: str = "./audio",
    voice: str = "George"
) -> list[str]:
    """Generate voiceovers for all slides.

    Args:
        narrations: List of narration scripts.
        output_dir: Directory to save audio files.
        voice: Voice name to use for all narrations.

    Returns:
        List of paths to generated audio files.
    """
    paths = []
    total = len(narrations)

    for i, text in enumerate(narrations, 1):
        print(f"Generating voiceover {i}/{total}...")
        path = generate_voiceover(text, i, output_dir, voice)
        paths.append(path)
        print(f"  Saved: {path}")

    return paths


def get_voice_info(voice: Optional[str] = None) -> dict:
    """Get information about available voices.

    Args:
        voice: Specific voice to get info for. If None, returns all voices.

    Returns:
        Dictionary with voice information.
    """
    if voice:
        if voice in VOICE_DESCRIPTIONS:
            return {voice: VOICE_DESCRIPTIONS[voice]}
        return {}

    return VOICE_DESCRIPTIONS.copy()
