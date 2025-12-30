"""Generate voiceover audio using Eleven Labs v3 via fal.ai."""

import os
from typing import Optional

import fal_client
import requests

from .utils import get_fal_key, api_call_with_retry


# Available voices - maps name to voice ID (None means use name directly)
VOICES = {
    "George": None,      # Built-in voice
    "Aria": None,        # Built-in voice
    "Rachel": None,      # Built-in voice
    "Sam": None,         # Built-in voice
    "Charlie": None,     # Built-in voice
    "Emily": None,       # Built-in voice
    "Hope": "tnSpp4vdxKPjI9w0GnoV",  # Custom voice ID from ElevenLabs
}

# Voice descriptions for reference
VOICE_DESCRIPTIONS = {
    "George": "Professional male voice, clear and authoritative - good for business",
    "Aria": "Professional female voice, warm and engaging - good for training",
    "Rachel": "Conversational female voice - good for casual content",
    "Sam": "Young male voice, energetic - good for marketing and tech",
    "Charlie": "Neutral, authoritative voice - good for documentaries",
    "Emily": "Soft female voice, calming - good for wellness content",
    "Hope": "Natural female voice, warm and clear - good for professional narration",
}


def _resolve_voice(voice: str) -> str:
    """Resolve voice name or ID to the value to send to API.

    The fal.ai Eleven Labs API accepts both voice names and voice IDs
    in the same 'voice' parameter.

    Args:
        voice: Voice name (e.g., "George") or voice ID (e.g., "tnSpp4vdxKPjI9w0GnoV").

    Returns:
        The voice value to use in the API call (either name or ID).
    """
    # Check if it's a known voice name with a custom ID
    if voice in VOICES:
        voice_id = VOICES[voice]
        if voice_id is not None:
            return voice_id  # Use the custom voice ID
        return voice  # Use the voice name directly

    # Check if it looks like a voice ID (contains digits or is long)
    if len(voice) > 15 or any(c.isdigit() for c in voice):
        # Assume it's a custom voice ID
        return voice

    # Unknown voice name - warn and fall back to George
    print(f"Warning: Voice '{voice}' not recognized. Using 'George'.")
    return "George"


def is_valid_voice(voice: str) -> bool:
    """Check if a voice name or ID is valid.

    Args:
        voice: Voice name or voice ID.

    Returns:
        True if the voice is a known name or looks like a valid ID.
    """
    if voice in VOICES:
        return True
    # Accept any string that looks like a voice ID
    if len(voice) > 15 or any(c.isdigit() for c in voice):
        return True
    return False


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
        voice: Voice name (George, Aria, Hope, etc.) or voice ID.

    Returns:
        Path to the generated audio file.
    """
    _init_fal()

    # Resolve voice name/ID
    voice_param = _resolve_voice(voice)

    def _generate():
        return fal_client.subscribe(
            "fal-ai/elevenlabs/tts/eleven-v3",
            arguments={
                "text": text,
                "voice": voice_param,
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


def combine_narrations_with_pauses(
    narrations: list[str],
    pause_marker: str = "...",
    pause_between_slides: int = 2
) -> str:
    """Combine multiple narration scripts into one with pauses.

    Args:
        narrations: List of narration scripts for each slide.
        pause_marker: Text marker for pauses (e.g., "..." or "[pause]").
        pause_between_slides: Number of pause markers between slides.

    Returns:
        Combined narration script with pauses.
    """
    pause = f" {pause_marker} " * pause_between_slides
    return pause.join(narrations)


def generate_combined_voiceover(
    narrations: list[str],
    output_dir: str = "./audio",
    output_filename: str = "narration_full.mp3",
    voice: str = "George",
    pause_marker: str = "...",
    pause_count: int = 2
) -> str:
    """Generate a single voiceover for all slides with natural pauses.

    This creates a cohesive narration with consistent voice, tone, and pacing
    across all slides, with pauses between sections.

    Args:
        narrations: List of narration scripts for each slide.
        output_dir: Directory to save audio file.
        output_filename: Name for the output file.
        voice: Voice name (George, Aria, Hope, etc.) or voice ID.
        pause_marker: Text marker for pauses.
        pause_count: Number of pause markers between slides.

    Returns:
        Path to the generated audio file.
    """
    _init_fal()

    # Resolve voice name/ID
    voice_param = _resolve_voice(voice)

    # Combine all narrations with pauses
    combined_script = combine_narrations_with_pauses(
        narrations, pause_marker, pause_count
    )

    print(f"Combined script length: {len(combined_script)} characters")

    def _generate():
        return fal_client.subscribe(
            "fal-ai/elevenlabs/tts/eleven-v3",
            arguments={
                "text": combined_script,
                "voice": voice_param,
                "speed": 1.0,
                "output_format": "mp3_44100_128",
            },
        )

    result = api_call_with_retry(_generate)

    audio_url = result["audio"]["url"]

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    response = requests.get(audio_url)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path
