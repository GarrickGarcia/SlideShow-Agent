---
name: slideshow-video-agent
description: "Creates video presentations with STATIC slides and ANIMATED transitions using fal.ai. Supports reference images (logos, color schemes) for brand consistency."
license: MIT
---

# Animated Slideshow Video Agent (fal.ai)

## Overview

Creates professional video presentations with:
- **STATIC slides** - Images that do NOT move while voiceover plays
- **ANIMATED transitions** - Cinematic motion graphics BETWEEN slides only
- **Voiceover narration** - Audio over static slides
- **Brand consistency** - Reference images (logos, colors) applied to all slides

```
[Static Slide 1] → [Animated Transition] → [Static Slide 2] → ...
   + voiceover         2-3 seconds            + voiceover
```

## Services (Single fal.ai API Key)

| Service | Model ID | Purpose |
|---------|----------|---------|
| **Nano Banana Pro** | `fal-ai/nano-banana-pro` | Text-only slide generation |
| **Nano Banana Pro Edit** | `fal-ai/nano-banana-pro/edit` | Text + reference images → slides |
| **Kling 2.6 Pro** | `fal-ai/kling-video/v2.6/pro/image-to-video` | Animated transitions ONLY |
| **Eleven Labs v3** | `fal-ai/elevenlabs/tts/eleven-v3` | Voiceover narration |

## Required Environment

```bash
export FAL_KEY="your-fal-ai-api-key"
pip install fal-client requests
apt-get install ffmpeg
```

---

## Two Slide Generation Modes

### Mode 1: Text Only (No References)
Use `fal-ai/nano-banana-pro` for generic slides without brand requirements.

```python
result = fal_client.subscribe(
    "fal-ai/nano-banana-pro",
    arguments={
        "prompt": "Professional slide titled 'Welcome' with modern design",
        "aspect_ratio": "16:9",
        "output_format": "png"
    }
)
```

### Mode 2: Text + Reference Images (Brand Consistent)
Use `fal-ai/nano-banana-pro/edit` when you have logos, color palettes, or style guides.

```python
result = fal_client.subscribe(
    "fal-ai/nano-banana-pro/edit",  # Edit endpoint
    arguments={
        "prompt": "Professional slide titled 'Welcome' matching the brand style and colors from the reference images",
        "image_urls": [
            "https://example.com/logo.png",      # Company logo
            "https://example.com/colors.png"     # Color palette
        ],
        "aspect_ratio": "16:9",
        "output_format": "png"
    }
)
```

---

## Reference Image Support

### Uploading Local Reference Images

```python
import fal_client

def upload_references(image_paths: list[str]) -> list[str]:
    """Upload local images to fal.ai and return URLs."""
    urls = []
    for path in image_paths:
        with open(path, "rb") as f:
            ext = path.lower().split('.')[-1]
            mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg'}.get(ext, 'image/png')
            url = fal_client.upload(f.read(), mime)
            urls.append(url)
    return urls

# Upload once, use for all slides
ref_urls = upload_references(["./logo.png", "./brand_colors.png"])
```

### Reference Image Types

| Type | Description | Example |
|------|-------------|---------|
| **Logo** | Company/product logo | PNG with transparency |
| **Color palette** | Brand color swatches | Simple color grid |
| **Style guide** | Example of desired style | Existing slide design |
| **Template** | Layout reference | PowerPoint slide screenshot |

---

## Complete Slide Generator with Reference Support

```python
import os
import fal_client
import requests
from typing import Optional

def upload_references(paths: list[str]) -> list[str]:
    """Upload local images to fal.ai storage."""
    urls = []
    for path in paths:
        with open(path, "rb") as f:
            ext = path.lower().split('.')[-1]
            mime = {'png': 'image/png', 'jpg': 'image/jpeg'}.get(ext, 'image/png')
            urls.append(fal_client.upload(f.read(), mime))
    return urls


def generate_slide(
    title: str,
    visual: str,
    slide_num: int,
    output_dir: str = "./slides",
    reference_urls: Optional[list[str]] = None
) -> str:
    """
    Generate a slide with optional reference images.
    
    Args:
        title: Slide title text
        visual: Description of slide visuals
        slide_num: Slide number for filename
        output_dir: Output directory
        reference_urls: URLs of reference images (logo, colors, etc.)
    """
    
    prompt = f"""Professional presentation slide:
- Title: "{title}" in large, clear text
- Visual: {visual}
- Style: Modern, clean, 16:9 format
- ALL text must be legible
- Match the branding, colors, and style from reference images"""

    # Choose endpoint based on whether we have references
    if reference_urls:
        result = fal_client.subscribe(
            "fal-ai/nano-banana-pro/edit",
            arguments={
                "prompt": prompt,
                "image_urls": reference_urls,
                "aspect_ratio": "16:9",
                "output_format": "png"
            }
        )
    else:
        result = fal_client.subscribe(
            "fal-ai/nano-banana-pro",
            arguments={
                "prompt": prompt,
                "aspect_ratio": "16:9",
                "output_format": "png"
            }
        )
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"slide_{slide_num:02d}.png")
    
    with open(output_path, "wb") as f:
        f.write(requests.get(result["images"][0]["url"]).content)
    
    return output_path
```

---

## Voiceover Generation

```python
def generate_voiceover(text: str, slide_num: int, voice: str = "George") -> str:
    result = fal_client.subscribe(
        "fal-ai/elevenlabs/tts/eleven-v3",
        arguments={"text": text, "voice": voice, "output_format": "mp3_44100_128"}
    )
    
    output_path = f"audio/narration_{slide_num:02d}.mp3"
    os.makedirs("audio", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(requests.get(result["audio"]["url"]).content)
    
    return output_path
```

---

## Transition Generation (Only Animated Part)

```python
def generate_transition(from_slide: str, trans_num: int, style: str = "cinematic") -> str:
    """Generate animated transition - the ONLY motion in the video."""
    
    with open(from_slide, "rb") as f:
        image_url = fal_client.upload(f.read(), "image/png")
    
    prompts = {
        "cinematic": "Cinematic dissolve with particles flowing across frame",
        "zoom_blur": "Dynamic zoom blur rushing toward camera",
        "swipe": "Smooth horizontal swipe with 3D parallax",
        "shatter": "Elements break apart and scatter gracefully",
        "particles": "Content dissolves into swirling particles"
    }
    
    result = fal_client.subscribe(
        "fal-ai/kling-video/v2.6/pro/image-to-video",
        arguments={
            "prompt": prompts.get(style, prompts["cinematic"]),
            "image_url": image_url,
            "duration": "5",
            "aspect_ratio": "16:9",
            "generate_audio": False
        }
    )
    
    output_path = f"transitions/trans_{trans_num:02d}.mp4"
    os.makedirs("transitions", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(requests.get(result["video"]["url"]).content)
    
    return output_path
```

---

## FFmpeg Assembly

```python
import subprocess
import json

def get_duration(path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def create_static_slide_video(image: str, audio: str, output: str):
    """Static image + audio (NO motion)."""
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", image, "-i", audio,
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p",
        "-t", str(get_duration(audio)), "-r", "30", "-shortest", output
    ], check=True)


def trim_transition(input_path: str, output_path: str, duration: float = 2.5):
    full_dur = get_duration(input_path)
    start = max(0, (full_dur - duration) / 2)
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(start), "-i", input_path,
        "-t", str(duration), "-c:v", "libx264", "-an", output_path
    ], check=True)


def assemble_video(slides: list, audios: list, transitions: list, output: str):
    """[Slide+Audio] → [Transition] → [Slide+Audio] → ..."""
    os.makedirs("temp", exist_ok=True)
    segments = []
    
    for i, (slide, audio) in enumerate(zip(slides, audios)):
        seg = f"temp/slide_{i+1:02d}.mp4"
        create_static_slide_video(slide, audio, seg)
        segments.append(seg)
        
        if i < len(transitions):
            trimmed = f"temp/trans_{i+1:02d}_trim.mp4"
            trim_transition(transitions[i], trimmed)
            segments.append(trimmed)
    
    with open("temp/concat.txt", "w") as f:
        for s in segments:
            f.write(f"file '{os.path.abspath(s)}'\n")
    
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "temp/concat.txt",
        "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", output
    ], check=True)
```

---

## Complete Example with References

```python
import fal_client
import requests
import os

def create_branded_presentation(
    slides_data: list[dict],
    reference_images: list[str],  # Local paths to logo, colors, etc.
    output: str = "presentation.mp4",
    voice: str = "George"
):
    """Create presentation with brand-consistent slides."""
    
    # Setup directories
    for d in ["slides", "audio", "transitions", "temp"]:
        os.makedirs(d, exist_ok=True)
    
    # Upload reference images ONCE (reuse for all slides)
    print("Uploading reference images...")
    ref_urls = upload_references(reference_images)
    print(f"  Uploaded {len(ref_urls)} references")
    
    slide_images = []
    audio_files = []
    
    # Generate slides with brand references
    for i, s in enumerate(slides_data, 1):
        print(f"Generating slide {i}...")
        
        # Slide with references
        result = fal_client.subscribe(
            "fal-ai/nano-banana-pro/edit",
            arguments={
                "prompt": f'Slide: "{s["title"]}" - {s["visual"]}. Match brand style from references.',
                "image_urls": ref_urls,
                "aspect_ratio": "16:9"
            }
        )
        img_path = f"slides/slide_{i:02d}.png"
        open(img_path, "wb").write(requests.get(result["images"][0]["url"]).content)
        slide_images.append(img_path)
        
        # Voiceover
        result = fal_client.subscribe(
            "fal-ai/elevenlabs/tts/eleven-v3",
            arguments={"text": s["narration"], "voice": voice}
        )
        audio_path = f"audio/audio_{i:02d}.mp3"
        open(audio_path, "wb").write(requests.get(result["audio"]["url"]).content)
        audio_files.append(audio_path)
    
    # Generate transitions
    transitions = []
    for i in range(len(slides_data) - 1):
        print(f"Generating transition {i+1}...")
        trans_path = generate_transition(slide_images[i], i+1)
        transitions.append(trans_path)
    
    # Assemble
    print("Assembling video...")
    assemble_video(slide_images, audio_files, transitions, output)
    print(f"✅ Done: {output}")


# Usage
slides = [
    {"title": "Welcome", "visual": "Modern title with logo", 
     "narration": "Welcome to our presentation."},
    {"title": "Our Mission", "visual": "Clean infographic", 
     "narration": "Our mission is to innovate."},
    {"title": "Thank You", "visual": "Closing slide with contact info", 
     "narration": "Thank you for watching."}
]

create_branded_presentation(
    slides_data=slides,
    reference_images=["./logo.png", "./brand_colors.png"],
    output="branded_presentation.mp4",
    voice="Aria"
)
```

---

## JSON Configuration Format

```json
{
    "title": "Company Presentation",
    "voice": "George",
    "transition_style": "cinematic",
    "reference_images": ["./logo.png", "./colors.png"],
    "reference_urls": ["https://example.com/style.png"],
    "slides": [
        {
            "title": "Welcome",
            "visual": "Title slide with company logo prominently displayed",
            "narration": "Welcome to our quarterly update."
        }
    ]
}
```

---

## Cost Summary

| Item | Cost |
|------|------|
| Slides (with or without refs) | $0.15/image |
| Voiceovers | ~$0.30/1000 chars |
| Transitions | $0.35 each (5 sec) |
| **5-slide presentation** | **~$2.75-3.00** |

---

## Key Points

1. **Use `fal-ai/nano-banana-pro/edit`** when you have reference images
2. **Upload references once**, reuse URLs for all slides
3. **Slides are STATIC** - no motion during voiceover
4. **Transitions are ANIMATED** - the only motion in the video
5. **Reference images** ensure brand consistency across all slides
