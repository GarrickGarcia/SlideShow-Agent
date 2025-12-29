# Building an Animated Slideshow Video Agent with Claude Code
## Using fal.ai Unified API

## Overview: What This System Creates

This system creates video presentations with:

1. **Static slides** - Professional slide images that remain completely still while voiceover narrates
2. **Cinematic transitions** - Animated motion graphics BETWEEN slides (the only animated parts)
3. **Voiceover narration** - Audio that plays over the static slides
4. **Brand consistency** - Reference images (logos, colors, style guides) can be used to match your brand

```
[Static Slide 1 + Voiceover] → [Animated Transition] → [Static Slide 2 + Voiceover] → ...
```

---

## The Three AI Services (via Single fal.ai API Key)

| Service | Model ID | Purpose |
|---------|----------|---------|
| **Nano Banana Pro** | `fal-ai/nano-banana-pro` | Text-to-image slide generation |
| **Nano Banana Pro Edit** | `fal-ai/nano-banana-pro/edit` | Text + reference images → slides |
| **Kling 2.6 Pro** | `fal-ai/kling-video/v2.6/pro/image-to-video` | Animated transitions between slides |
| **Eleven Labs v3** | `fal-ai/elevenlabs/tts/eleven-v3` | Voiceover narration |

---

## Setup: Single API Key

```bash
export FAL_KEY="your-fal-api-key-here"
```

Get your key at: [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)

---

## NEW: Using Reference Images for Brand Consistency

Nano Banana Pro's **edit endpoint** (`fal-ai/nano-banana-pro/edit`) accepts:
- A text prompt describing what you want
- **Multiple reference images** (logos, color palettes, style examples)

This allows you to generate slides that match your brand identity!

### Reference Image Use Cases

| Reference Type | Example Use |
|----------------|-------------|
| **Logo** | Include company logo in slide designs |
| **Color palette** | Match brand colors throughout |
| **Style guide** | Copy visual style from example |
| **Template** | Base new slides on existing design |
| **Photo** | Include specific imagery |

---

## Core Python Modules

### 1. slide_generator.py - With Reference Image Support

```python
"""Generate presentation slides using Nano Banana Pro via fal.ai
Supports both text-only and text + reference images"""

import os
import fal_client
import requests
from typing import Optional

def upload_reference_images(image_paths: list[str]) -> list[str]:
    """
    Upload local reference images to fal.ai storage.
    
    Args:
        image_paths: List of local file paths to reference images
        
    Returns:
        List of fal.ai URLs for the uploaded images
    """
    urls = []
    for path in image_paths:
        with open(path, "rb") as f:
            # Determine mime type
            ext = path.lower().split('.')[-1]
            mime_types = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/png')
            
            url = fal_client.upload(f.read(), mime_type)
            urls.append(url)
    return urls


def generate_slide(
    title: str,
    visual_description: str,
    slide_number: int,
    output_dir: str = "./slides",
    reference_images: Optional[list[str]] = None,
    reference_urls: Optional[list[str]] = None
) -> str:
    """
    Generate a static presentation slide image.
    
    Can use EITHER:
    - Text prompt only (basic generation)
    - Text prompt + reference images (brand-consistent generation)
    
    Args:
        title: The slide title text
        visual_description: Detailed description of slide visuals
        slide_number: Slide number for filename
        output_dir: Directory to save slide images
        reference_images: Local paths to reference images (logos, colors, etc.)
        reference_urls: URLs of reference images (if already hosted)
        
    Returns:
        Path to the generated slide image
    """
    
    prompt = f"""Create a professional presentation slide:
- Title: "{title}" displayed prominently at the top in large, clear text
- Visual content: {visual_description}
- Style: Modern, clean corporate presentation design
- Aspect ratio: 16:9 widescreen format
- Ensure ALL text is perfectly legible and correctly spelled
- Match the style, colors, and branding from the reference images provided
- Do not include slide numbers"""

    # Determine which endpoint to use
    has_references = bool(reference_images or reference_urls)
    
    if has_references:
        # Use the edit endpoint with reference images
        image_urls = reference_urls or []
        
        # Upload local images if provided
        if reference_images:
            uploaded_urls = upload_reference_images(reference_images)
            image_urls.extend(uploaded_urls)
        
        result = fal_client.subscribe(
            "fal-ai/nano-banana-pro/edit",  # Edit endpoint for image references
            arguments={
                "prompt": prompt,
                "image_urls": image_urls,  # Reference images
                "num_images": 1,
                "aspect_ratio": "16:9",
                "output_format": "png"
            }
        )
    else:
        # Use basic text-to-image endpoint
        result = fal_client.subscribe(
            "fal-ai/nano-banana-pro",
            arguments={
                "prompt": prompt,
                "num_images": 1,
                "aspect_ratio": "16:9",
                "output_format": "png"
            }
        )
    
    # Download the generated image
    image_url = result["images"][0]["url"]
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"slide_{slide_number:02d}.png")
    
    response = requests.get(image_url)
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return output_path


def generate_slide_batch(
    slides: list[dict], 
    output_dir: str = "./slides",
    reference_images: Optional[list[str]] = None,
    reference_urls: Optional[list[str]] = None
) -> list[str]:
    """
    Generate multiple slides, all using the same reference images for consistency.
    
    Args:
        slides: List of dicts with 'title' and 'visual_description'
        output_dir: Directory to save slides
        reference_images: Local paths to reference images (applied to ALL slides)
        reference_urls: URLs of reference images (applied to ALL slides)
        
    Returns:
        List of paths to generated slide images
    """
    # Upload reference images once (reuse URLs for all slides)
    uploaded_urls = []
    if reference_images:
        print("Uploading reference images...")
        uploaded_urls = upload_reference_images(reference_images)
    
    all_refs = (reference_urls or []) + uploaded_urls
    
    paths = []
    for i, slide in enumerate(slides, 1):
        path = generate_slide(
            title=slide["title"],
            visual_description=slide["visual_description"],
            slide_number=i,
            output_dir=output_dir,
            reference_urls=all_refs if all_refs else None
        )
        paths.append(path)
        print(f"Generated slide {i}/{len(slides)}: {path}")
    
    return paths
```

### 2. voiceover.py - Narration with Eleven Labs v3

```python
"""Generate voiceover audio using Eleven Labs v3 via fal.ai"""

import os
import fal_client
import requests

def generate_voiceover(
    text: str,
    slide_number: int,
    output_dir: str = "./audio",
    voice: str = "George"
) -> str:
    """
    Generate voiceover audio for a slide narration.
    
    Args:
        text: Narration script text
        slide_number: Slide number for filename
        output_dir: Directory to save audio files
        voice: Voice name (George, Aria, Rachel, Sam, etc.)
        
    Returns:
        Path to the generated audio file
    """
    result = fal_client.subscribe(
        "fal-ai/elevenlabs/tts/eleven-v3",
        arguments={
            "text": text,
            "voice": voice,
            "speed": 1.0,
            "output_format": "mp3_44100_128"
        }
    )
    
    audio_url = result["audio"]["url"]
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"narration_{slide_number:02d}.mp3")
    
    response = requests.get(audio_url)
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return output_path


def generate_voiceover_batch(
    narrations: list[str],
    output_dir: str = "./audio",
    voice: str = "George"
) -> list[str]:
    """Generate voiceovers for all slides."""
    paths = []
    for i, text in enumerate(narrations, 1):
        path = generate_voiceover(text, i, output_dir, voice)
        paths.append(path)
        print(f"Generated voiceover {i}/{len(narrations)}")
    return paths


# Available voices
VOICES = ["George", "Aria", "Rachel", "Sam", "Charlie", "Emily"]
```

### 3. transition_generator.py - Animated Transitions

```python
"""Generate animated transitions between slides using Kling 2.6 Pro"""

import os
import fal_client
import requests

def generate_transition(
    from_slide_path: str,
    transition_number: int,
    output_dir: str = "./transitions",
    transition_style: str = "cinematic"
) -> str:
    """
    Generate an animated transition from the outgoing slide.
    
    Args:
        from_slide_path: Path to the outgoing slide image
        transition_number: Transition number for filename
        output_dir: Directory to save transition videos
        transition_style: Style of transition animation
        
    Returns:
        Path to the generated transition video
    """
    
    # Upload the slide
    with open(from_slide_path, "rb") as f:
        image_url = fal_client.upload(f.read(), "image/png")
    
    # Transition prompts by style
    prompts = {
        "cinematic": "Cinematic dissolve with subtle particles flowing across frame, elegant light streaks",
        "zoom_blur": "Dynamic zoom blur, content rushes toward camera with motion blur effect",
        "swipe": "Smooth horizontal swipe with 3D parallax depth effect",
        "shatter": "Elements gracefully break apart into pieces that float and scatter",
        "morph": "Organic morphing, shapes smoothly flow and transform",
        "particles": "Content dissolves into glowing particles that swirl outward",
        "flip": "3D card flip with realistic depth and shadow",
        "wave": "Ripple wave effect spreading across frame",
        "slide_left": "Content slides smoothly to the left revealing darkness",
        "fade_blur": "Soft blur transition with gentle fade effect"
    }
    
    result = fal_client.subscribe(
        "fal-ai/kling-video/v2.6/pro/image-to-video",
        arguments={
            "prompt": prompts.get(transition_style, prompts["cinematic"]),
            "image_url": image_url,
            "duration": "5",
            "aspect_ratio": "16:9",
            "cfg_scale": 0.5,
            "generate_audio": False,
            "negative_prompt": "static, frozen, still image, no movement"
        }
    )
    
    video_url = result["video"]["url"]
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"transition_{transition_number:02d}.mp4")
    
    response = requests.get(video_url)
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return output_path


def generate_transitions_batch(
    slide_images: list[str],
    output_dir: str = "./transitions",
    transition_style: str = "cinematic"
) -> list[str]:
    """Generate transitions between all slides (n-1 transitions for n slides)."""
    paths = []
    for i in range(len(slide_images) - 1):
        path = generate_transition(
            slide_images[i], 
            i + 1, 
            output_dir, 
            transition_style
        )
        paths.append(path)
        print(f"Generated transition {i+1}/{len(slide_images)-1}")
    return paths
```

### 4. video_assembler.py - FFmpeg Assembly

```python
"""Assemble final video: static slides + voiceover + animated transitions"""

import os
import subprocess
import json

def get_duration(file_path: str) -> float:
    """Get duration of an audio or video file."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", 
         "-show_format", file_path],
        capture_output=True, text=True
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def create_slide_with_audio(image_path: str, audio_path: str, output_path: str):
    """Create a STATIC video from slide image + voiceover audio."""
    duration = get_duration(audio_path)
    
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        "-r", "30",
        "-shortest",
        output_path
    ], check=True, capture_output=True)


def trim_transition(input_path: str, output_path: str, duration: float = 2.5):
    """Trim transition video to desired length."""
    full_dur = get_duration(input_path)
    start = max(0, (full_dur - duration) / 2)
    
    subprocess.run([
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", input_path,
        "-t", str(duration),
        "-c:v", "libx264",
        "-an",
        output_path
    ], check=True, capture_output=True)


def assemble_slideshow(
    slide_images: list[str],
    audio_files: list[str],
    transition_videos: list[str],
    output_path: str,
    temp_dir: str = "./temp",
    transition_duration: float = 2.5
) -> str:
    """Assemble: [Slide1+Audio] → [Transition] → [Slide2+Audio] → ..."""
    
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    segments = []
    
    for i, (image, audio) in enumerate(zip(slide_images, audio_files)):
        # Static slide with voiceover
        slide_video = os.path.join(temp_dir, f"slide_{i+1:02d}.mp4")
        create_slide_with_audio(image, audio, slide_video)
        segments.append(slide_video)
        print(f"Created slide segment {i+1}/{len(slide_images)}")
        
        # Transition (except after last slide)
        if i < len(transition_videos):
            trimmed = os.path.join(temp_dir, f"trans_{i+1:02d}_trim.mp4")
            trim_transition(transition_videos[i], trimmed, transition_duration)
            segments.append(trimmed)
    
    # Concatenate
    concat_file = os.path.join(temp_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for seg in segments:
            f.write(f"file '{os.path.abspath(seg)}'\n")
    
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264", "-c:a", "aac",
        "-movflags", "+faststart",
        output_path
    ], check=True, capture_output=True)
    
    print(f"✅ Final video: {output_path}")
    return output_path
```

### 5. orchestrator.py - Main Workflow with Reference Images

```python
"""Main orchestrator with reference image support"""

import os
import json
from dataclasses import dataclass, field
from typing import Optional

from .slide_generator import generate_slide_batch
from .voiceover import generate_voiceover_batch
from .transition_generator import generate_transitions_batch
from .video_assembler import assemble_slideshow


@dataclass
class Slide:
    title: str
    visual_description: str
    narration: str


@dataclass
class PresentationConfig:
    """Configuration for the presentation."""
    slides: list[Slide]
    output_path: str = "./output/presentation.mp4"
    voice: str = "George"
    transition_style: str = "cinematic"
    transition_duration: float = 2.5
    
    # Reference images for brand consistency
    reference_images: list[str] = field(default_factory=list)  # Local paths
    reference_urls: list[str] = field(default_factory=list)    # URLs


def create_slideshow_video(config: PresentationConfig) -> str:
    """
    Create a complete slideshow video with optional reference images.
    
    Reference images (logos, color palettes, style guides) will be used
    to ensure all slides match your brand identity.
    
    Args:
        config: PresentationConfig with slides and settings
        
    Returns:
        Path to the final video
    """
    work_dir = os.path.dirname(config.output_path) or "."
    slides_dir = os.path.join(work_dir, "slides")
    audio_dir = os.path.join(work_dir, "audio")
    transitions_dir = os.path.join(work_dir, "transitions")
    temp_dir = os.path.join(work_dir, "temp")
    
    # Prepare slide data
    slide_defs = [
        {"title": s.title, "visual_description": s.visual_description}
        for s in config.slides
    ]
    narrations = [s.narration for s in config.slides]
    
    # Check for reference images
    has_refs = bool(config.reference_images or config.reference_urls)
    
    # ===== STEP 1: Generate slide images =====
    print("=" * 60)
    print("STEP 1: Generating STATIC slide images (Nano Banana Pro)")
    if has_refs:
        print("        Using reference images for brand consistency")
        print(f"        References: {len(config.reference_images)} local, {len(config.reference_urls)} URLs")
    print("=" * 60)
    
    slide_images = generate_slide_batch(
        slides=slide_defs,
        output_dir=slides_dir,
        reference_images=config.reference_images if config.reference_images else None,
        reference_urls=config.reference_urls if config.reference_urls else None
    )
    
    # ===== STEP 2: Generate voiceovers =====
    print("\n" + "=" * 60)
    print("STEP 2: Generating voiceover audio (Eleven Labs v3)")
    print(f"        Voice: {config.voice}")
    print("=" * 60)
    
    audio_files = generate_voiceover_batch(narrations, audio_dir, config.voice)
    
    # ===== STEP 3: Generate transitions =====
    print("\n" + "=" * 60)
    print("STEP 3: Generating ANIMATED transitions (Kling 2.6 Pro)")
    print(f"        Style: {config.transition_style}")
    print("=" * 60)
    
    transition_videos = generate_transitions_batch(
        slide_images, 
        transitions_dir, 
        config.transition_style
    )
    
    # ===== STEP 4: Assemble =====
    print("\n" + "=" * 60)
    print("STEP 4: Assembling final video (FFmpeg)")
    print("=" * 60)
    
    final_video = assemble_slideshow(
        slide_images=slide_images,
        audio_files=audio_files,
        transition_videos=transition_videos,
        output_path=config.output_path,
        temp_dir=temp_dir,
        transition_duration=config.transition_duration
    )
    
    print("\n" + "=" * 60)
    print(f"✅ COMPLETE! Video saved to: {final_video}")
    print("=" * 60)
    
    return final_video


def run_from_json(json_path: str) -> str:
    """
    Create presentation from a JSON configuration file.
    
    JSON format:
    {
        "title": "Presentation Title",
        "voice": "George",
        "transition_style": "cinematic",
        "reference_images": ["./logo.png", "./brand_colors.png"],
        "reference_urls": ["https://example.com/style_guide.png"],
        "slides": [
            {
                "title": "Slide Title",
                "visual": "Description of visuals",
                "narration": "Voiceover script"
            }
        ]
    }
    """
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    slides = [
        Slide(
            title=s["title"],
            visual_description=s["visual"],
            narration=s["narration"]
        )
        for s in data["slides"]
    ]
    
    config = PresentationConfig(
        slides=slides,
        output_path=data.get("output_path", "./presentation.mp4"),
        voice=data.get("voice", "George"),
        transition_style=data.get("transition_style", "cinematic"),
        reference_images=data.get("reference_images", []),
        reference_urls=data.get("reference_urls", [])
    )
    
    return create_slideshow_video(config)
```

---

## Example: Using Reference Images

### Example 1: Company Logo + Color Palette

```python
from slideshow_agent import PresentationConfig, Slide, create_slideshow_video

config = PresentationConfig(
    slides=[
        Slide(
            title="Welcome to Acme Corp",
            visual_description="Modern title slide with company branding",
            narration="Welcome to Acme Corporation's quarterly update."
        ),
        Slide(
            title="Q4 Results",
            visual_description="Clean infographic showing growth metrics",
            narration="Our fourth quarter exceeded expectations."
        )
    ],
    voice="George",
    transition_style="cinematic",
    
    # Reference images for brand consistency
    reference_images=[
        "./assets/acme_logo.png",        # Company logo
        "./assets/brand_colors.png",      # Color palette image
        "./assets/slide_template.png"     # Example slide style
    ]
)

create_slideshow_video(config)
```

### Example 2: Style Reference from URL

```python
config = PresentationConfig(
    slides=[...],
    
    # Use hosted reference images
    reference_urls=[
        "https://company.com/brand/logo.png",
        "https://company.com/brand/style-guide.png"
    ]
)
```

### Example 3: JSON Configuration with References

```json
{
    "title": "Product Launch",
    "voice": "Aria",
    "transition_style": "swipe",
    "reference_images": [
        "./brand/logo.png",
        "./brand/colors.png"
    ],
    "slides": [
        {
            "title": "Introducing Widget Pro",
            "visual": "Sleek product hero shot with brand styling",
            "narration": "Introducing the all-new Widget Pro."
        },
        {
            "title": "Key Features",
            "visual": "Feature grid with icons matching brand style",
            "narration": "Packed with features you'll love."
        }
    ]
}
```

---

## How Reference Images Work

When you provide reference images, Nano Banana Pro's **edit endpoint** (`fal-ai/nano-banana-pro/edit`) will:

1. **Analyze the references** - Extract colors, styles, logos, visual elements
2. **Apply to generation** - Create new slides that incorporate these elements
3. **Maintain consistency** - All slides share the same brand identity

### Best Practices for Reference Images

| Reference Type | Recommendations |
|----------------|-----------------|
| **Logo** | High-res PNG with transparency |
| **Color palette** | Simple swatches showing brand colors |
| **Style example** | Existing slide or design that shows desired style |
| **Template** | Clean example of layout you want |

### Prompt Tips for Brand Matching

Include instructions in your visual descriptions:
- "Match the color scheme from the reference images"
- "Include the logo from the reference"
- "Follow the visual style shown in the reference"
- "Use the same typography style as the reference"

---

## Cost Breakdown

| Item | Model | Cost |
|------|-------|------|
| Slides (with refs) | `fal-ai/nano-banana-pro/edit` | $0.15 each |
| Slides (text only) | `fal-ai/nano-banana-pro` | $0.15 each |
| Voiceovers | `fal-ai/elevenlabs/tts/eleven-v3` | ~$0.30/1000 chars |
| Transitions | `fal-ai/kling-video/v2.6/pro/image-to-video` | $0.35 each |

**5-slide presentation with references: ~$2.75-3.00**

---

## Summary

### Two Slide Generation Modes

| Mode | Endpoint | Use Case |
|------|----------|----------|
| **Text only** | `fal-ai/nano-banana-pro` | Generic slides, no brand requirements |
| **Text + References** | `fal-ai/nano-banana-pro/edit` | Brand-consistent slides with logos/colors |

### What's Static vs. Animated

| Element | Animated? | Notes |
|---------|-----------|-------|
| **Slides** | ❌ NO | Static images while voiceover plays |
| **Transitions** | ✅ YES | The only motion in the video |
| **Voiceover** | N/A | Audio over static slides |

The reference images ensure all your slides maintain consistent branding throughout the presentation!
