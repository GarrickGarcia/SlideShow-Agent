"""Generate animated transitions between slides using Kling 2.6 Pro."""

import os

import fal_client
import requests

from .utils import get_fal_key, api_call_with_retry


# Available transition styles with their prompts
TRANSITION_STYLES = {
    "cinematic": "Cinematic dissolve with subtle particles flowing across frame, elegant light streaks",
    "zoom_blur": "Dynamic zoom blur, content rushes toward camera with motion blur effect",
    "swipe": "Smooth horizontal swipe with 3D parallax depth effect",
    "shatter": "Elements gracefully break apart into pieces that float and scatter",
    "morph": "Organic morphing, shapes smoothly flow and transform",
    "particles": "Content dissolves into glowing particles that swirl outward",
    "flip": "3D card flip with realistic depth and shadow",
    "wave": "Ripple wave effect spreading across frame",
    "slide_left": "Content slides smoothly to the left revealing darkness",
    "fade_blur": "Soft blur transition with gentle fade effect",
}

# Default transition style
DEFAULT_STYLE = "cinematic"


def _init_fal():
    """Initialize fal client with API key."""
    os.environ["FAL_KEY"] = get_fal_key()


def generate_transition(
    from_slide_path: str,
    transition_number: int,
    output_dir: str = "./transitions",
    transition_style: str = "cinematic"
) -> str:
    """Generate an animated transition from the outgoing slide.

    Args:
        from_slide_path: Path to the outgoing slide image.
        transition_number: Transition number for filename.
        output_dir: Directory to save transition videos.
        transition_style: Style of transition animation.

    Returns:
        Path to the generated transition video.
    """
    _init_fal()

    if transition_style not in TRANSITION_STYLES:
        print(f"Warning: Style '{transition_style}' not recognized. Using '{DEFAULT_STYLE}'.")
        transition_style = DEFAULT_STYLE

    # Upload the slide
    with open(from_slide_path, "rb") as f:
        image_url = fal_client.upload(f.read(), "image/png")

    prompt = TRANSITION_STYLES[transition_style]

    def _generate():
        return fal_client.subscribe(
            "fal-ai/kling-video/v2.6/pro/image-to-video",
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "duration": "5",
                "aspect_ratio": "16:9",
                "cfg_scale": 0.5,
                "generate_audio": False,
                "negative_prompt": "static, frozen, still image, no movement",
            },
        )

    result = api_call_with_retry(_generate)

    video_url = result["video"]["url"]

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"transition_{transition_number:02d}.mp4")

    response = requests.get(video_url)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path


def generate_transitions_batch(
    slide_images: list[str],
    output_dir: str = "./transitions",
    transition_style: str = "cinematic"
) -> list[str]:
    """Generate transitions between all slides (n-1 transitions for n slides).

    Args:
        slide_images: List of paths to slide images.
        output_dir: Directory to save transition videos.
        transition_style: Style of transition animation.

    Returns:
        List of paths to generated transition videos.
    """
    paths = []
    total = len(slide_images) - 1

    if total < 1:
        print("Warning: Need at least 2 slides to generate transitions.")
        return paths

    for i in range(total):
        print(f"Generating transition {i + 1}/{total}...")
        path = generate_transition(
            slide_images[i],
            i + 1,
            output_dir,
            transition_style,
        )
        paths.append(path)
        print(f"  Saved: {path}")

    return paths


def list_transition_styles() -> dict[str, str]:
    """Get available transition styles and their descriptions.

    Returns:
        Dictionary mapping style names to descriptions.
    """
    return TRANSITION_STYLES.copy()
