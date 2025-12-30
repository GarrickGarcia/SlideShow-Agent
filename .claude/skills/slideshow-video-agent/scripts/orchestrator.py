"""Main orchestrator for slideshow video generation."""

import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .slide_generator import generate_slide_batch, generate_slide_batch_with_validation
from .voiceover import generate_voiceover_batch, generate_combined_voiceover, VOICES, is_valid_voice
from .transition_generator import generate_transitions_batch, TRANSITION_STYLES
from .video_assembler import assemble_slideshow, assemble_slideshow_with_single_audio
from .utils import (
    ensure_output_dirs,
    get_project_root,
    list_reference_images,
    validate_prerequisites,
)


@dataclass
class Slide:
    """Configuration for a single slide.

    Slides have two types of text content:
    - bullet_points: Brief summaries shown ON the slide (3-4 items, 3-6 words each)
    - narration: Fuller script spoken in voiceover (more detailed than slide text)

    The visual_description describes the graphic style (line-art icons, not photos).
    """

    title: str
    bullet_points: list[str]  # Brief text shown on slide (3-4 items max)
    narration: str            # Fuller script for voiceover
    visual_description: str   # Graphic/icon description (line-art style)
    is_title_slide: bool = False  # If True, display logo prominently


@dataclass
class PresentationConfig:
    """Configuration for the entire presentation."""

    slides: list[Slide]
    output_path: str = "./output/presentation.mp4"
    voice: str = "George"
    transition_style: str = "cinematic"
    transition_duration: float = 2.5

    # Reference images for brand consistency
    reference_images: list[str] = field(default_factory=list)  # Local paths
    reference_urls: list[str] = field(default_factory=list)  # URLs

    # Validation options
    validate_slides: bool = True  # Use Claude to validate slides
    max_validation_attempts: int = 3  # Max regeneration attempts per slide


def create_slideshow_video(config: PresentationConfig) -> str:
    """Create a complete slideshow video with optional reference images.

    Reference images (logos, color palettes, style guides) will be used
    to ensure all slides match your brand identity.

    Args:
        config: PresentationConfig with slides and settings.

    Returns:
        Path to the final video.

    Raises:
        EnvironmentError: If prerequisites are not met.
        RuntimeError: If video generation fails.
    """
    # Validate prerequisites
    prereqs = validate_prerequisites()
    if not prereqs["fal_key"]:
        raise EnvironmentError(
            "FAL_KEY not configured. Add your API key to .env file.\n"
            "Get your key at: https://fal.ai/dashboard/keys"
        )
    if not prereqs["ffmpeg"]:
        raise EnvironmentError(
            "FFmpeg not installed. See workflow_guide.md for installation."
        )

    # Validate voice
    if not is_valid_voice(config.voice):
        print(f"Warning: Voice '{config.voice}' not recognized. Using 'George'.")
        config.voice = "George"

    # Validate transition style
    if config.transition_style not in TRANSITION_STYLES:
        print(f"Warning: Style '{config.transition_style}' not recognized. Using 'cinematic'.")
        config.transition_style = "cinematic"

    # Setup directories
    work_dir = str(Path(config.output_path).parent) or "."
    dirs = ensure_output_dirs(work_dir)
    slides_dir = str(dirs["slides"])
    audio_dir = str(dirs["audio"])
    transitions_dir = str(dirs["transitions"])
    temp_dir = str(dirs["temp"])

    # Prepare slide data with new format
    slide_defs = [
        {
            "title": s.title,
            "bullet_points": s.bullet_points,
            "visual_description": s.visual_description,
            "is_title_slide": s.is_title_slide,
        }
        for s in config.slides
    ]
    narrations = [s.narration for s in config.slides]

    # Check for reference images
    has_refs = bool(config.reference_images or config.reference_urls)

    # ===== STEP 1: Generate slide images =====
    print("=" * 60)
    print("STEP 1: Generating STATIC slide images (Nano Banana Pro)")
    if config.validate_slides:
        print("        With AI validation (Claude Haiku 4.5)")
    if has_refs:
        print("        Using reference images for brand consistency")
        print(f"        Local refs: {len(config.reference_images)}")
        print(f"        URL refs: {len(config.reference_urls)}")
    print("=" * 60)

    if config.validate_slides:
        slide_images = generate_slide_batch_with_validation(
            slides=slide_defs,
            output_dir=slides_dir,
            reference_images=config.reference_images if config.reference_images else None,
            reference_urls=config.reference_urls if config.reference_urls else None,
            validate=True,
            max_validation_attempts=config.max_validation_attempts,
        )
    else:
        slide_images = generate_slide_batch(
            slides=slide_defs,
            output_dir=slides_dir,
            reference_images=config.reference_images if config.reference_images else None,
            reference_urls=config.reference_urls if config.reference_urls else None,
        )

    # ===== STEP 2: Generate transitions =====
    print("\n" + "=" * 60)
    print("STEP 2: Generating ANIMATED transitions (Kling 2.6 Pro)")
    print(f"        Style: {config.transition_style}")
    print("=" * 60)

    transition_videos = generate_transitions_batch(
        slide_images,
        transitions_dir,
        config.transition_style,
    )

    # ===== STEP 3: Generate combined voiceover =====
    print("\n" + "=" * 60)
    print("STEP 3: Generating COMBINED voiceover (Eleven Labs v3)")
    print(f"        Voice: {config.voice}")
    print("        Creating single cohesive narration with pauses")
    print("=" * 60)

    audio_file = generate_combined_voiceover(
        narrations=narrations,
        output_dir=audio_dir,
        output_filename="narration_full.mp3",
        voice=config.voice,
        pause_marker="...",
        pause_count=2,
    )
    print(f"  Saved: {audio_file}")

    # ===== STEP 4: Assemble =====
    print("\n" + "=" * 60)
    print("STEP 4: Assembling final video (FFmpeg)")
    print("        Syncing slides with continuous audio track")
    print("=" * 60)

    final_video = assemble_slideshow_with_single_audio(
        slide_images=slide_images,
        audio_file=audio_file,
        transition_videos=transition_videos,
        output_path=config.output_path,
        temp_dir=temp_dir,
        transition_duration=config.transition_duration,
    )

    print("\n" + "=" * 60)
    print(f"COMPLETE! Video saved to: {final_video}")
    print("=" * 60)

    return final_video


def run_from_json(json_path: str) -> str:
    """Create presentation from a JSON configuration file.

    JSON format:
    {
        "title": "Presentation Title",
        "voice": "George",
        "transition_style": "cinematic",
        "transition_duration": 2.5,
        "reference_images": ["./Reference Images/logo.png"],
        "reference_urls": [],
        "output_path": "./output/presentation.mp4",
        "validate_slides": true,
        "slides": [
            {
                "title": "Slide Title",
                "bullet_points": ["Point 1", "Point 2"],
                "visual": "Description of visuals",
                "narration": "Voiceover script",
                "is_title_slide": false
            }
        ]
    }

    Args:
        json_path: Path to JSON configuration file.

    Returns:
        Path to the final video.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    slides = []
    for i, s in enumerate(data["slides"]):
        # Support both old format (visual_description) and new format (bullet_points)
        bullet_points = s.get("bullet_points")
        if bullet_points is None:
            # Backwards compatibility: use title as single bullet
            bullet_points = [s["title"]]

        slides.append(Slide(
            title=s["title"],
            bullet_points=bullet_points,
            narration=s["narration"],
            visual_description=s.get("visual", s.get("visual_description", "")),
            is_title_slide=s.get("is_title_slide", i == 0),
        ))

    config = PresentationConfig(
        slides=slides,
        output_path=data.get("output_path", "./output/presentation.mp4"),
        voice=data.get("voice", "George"),
        transition_style=data.get("transition_style", "cinematic"),
        transition_duration=data.get("transition_duration", 2.5),
        reference_images=data.get("reference_images", []),
        reference_urls=data.get("reference_urls", []),
        validate_slides=data.get("validate_slides", True),
        max_validation_attempts=data.get("max_validation_attempts", 3),
    )

    return create_slideshow_video(config)


def create_simple_presentation(
    topic: str,
    slides_content: list[dict],
    reference_images: Optional[list[str]] = None,
    voice: str = "George",
    transition_style: str = "cinematic",
    output_path: str = "./output/presentation.mp4",
    validate_slides: bool = True,
) -> str:
    """Simplified interface for creating a presentation.

    Args:
        topic: Topic/title of the presentation.
        slides_content: List of dicts with 'title', 'bullet_points', 'visual', and 'narration'.
        reference_images: List of paths to reference images.
        voice: Voice for narration.
        transition_style: Style for transitions.
        output_path: Path for output video.
        validate_slides: Whether to validate slides with Claude.

    Returns:
        Path to the final video.
    """
    slides = []
    for i, s in enumerate(slides_content):
        bullet_points = s.get("bullet_points")
        if bullet_points is None:
            bullet_points = [s["title"]]

        slides.append(Slide(
            title=s["title"],
            bullet_points=bullet_points,
            narration=s["narration"],
            visual_description=s.get("visual", ""),
            is_title_slide=s.get("is_title_slide", i == 0),
        ))

    config = PresentationConfig(
        slides=slides,
        output_path=output_path,
        voice=voice,
        transition_style=transition_style,
        reference_images=reference_images or [],
        validate_slides=validate_slides,
    )

    return create_slideshow_video(config)


def estimate_cost(num_slides: int, avg_narration_chars: int = 200) -> dict:
    """Estimate the cost of generating a presentation.

    Args:
        num_slides: Number of slides in presentation.
        avg_narration_chars: Average characters per narration.

    Returns:
        Dictionary with cost breakdown.
    """
    slide_cost = num_slides * 0.15
    transition_cost = (num_slides - 1) * 0.35
    voiceover_cost = (num_slides * avg_narration_chars / 1000) * 0.30

    total = slide_cost + transition_cost + voiceover_cost

    return {
        "slides": f"${slide_cost:.2f}",
        "transitions": f"${transition_cost:.2f}",
        "voiceovers": f"${voiceover_cost:.2f}",
        "total": f"${total:.2f}",
        "breakdown": {
            "slide_count": num_slides,
            "transition_count": num_slides - 1,
            "total_chars": num_slides * avg_narration_chars,
        },
    }
