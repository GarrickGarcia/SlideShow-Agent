"""Assemble final video: static slides + voiceover + animated transitions."""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional

from .utils import get_ffmpeg_path, get_ffprobe_path, cleanup_temp_dir


def get_duration(file_path: str) -> float:
    """Get duration of an audio or video file.

    Args:
        file_path: Path to audio or video file.

    Returns:
        Duration in seconds.

    Raises:
        RuntimeError: If ffprobe fails to get duration.
    """
    ffprobe = get_ffprobe_path()

    result = subprocess.run(
        [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", file_path],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {file_path}: {result.stderr}")

    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def create_slide_with_audio(
    image_path: str,
    audio_path: str,
    output_path: str,
    frame_rate: int = 30
) -> None:
    """Create a STATIC video from slide image + voiceover audio.

    Args:
        image_path: Path to slide image.
        audio_path: Path to voiceover audio.
        output_path: Path for output video.
        frame_rate: Video frame rate (default 30).

    Raises:
        RuntimeError: If FFmpeg fails.
    """
    ffmpeg = get_ffmpeg_path()
    duration = get_duration(audio_path)

    result = subprocess.run(
        [
            ffmpeg, "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            "-r", str(frame_rate),
            "-shortest",
            output_path,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed creating slide video: {result.stderr}")


def trim_transition(
    input_path: str,
    output_path: str,
    duration: float = 2.5
) -> None:
    """Trim transition video to desired length.

    Takes the middle portion of the transition video.

    Args:
        input_path: Path to input transition video.
        output_path: Path for output trimmed video.
        duration: Desired duration in seconds.

    Raises:
        RuntimeError: If FFmpeg fails.
    """
    ffmpeg = get_ffmpeg_path()
    full_dur = get_duration(input_path)
    start = max(0, (full_dur - duration) / 2)

    result = subprocess.run(
        [
            ffmpeg, "-y",
            "-ss", str(start),
            "-i", input_path,
            "-t", str(duration),
            "-c:v", "libx264",
            "-an",
            output_path,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed trimming transition: {result.stderr}")


def assemble_slideshow(
    slide_images: list[str],
    audio_files: list[str],
    transition_videos: list[str],
    output_path: str,
    temp_dir: str = "./temp",
    transition_duration: float = 2.5,
    cleanup: bool = True
) -> str:
    """Assemble final video: [Slide1+Audio] -> [Transition] -> [Slide2+Audio] -> ...

    Args:
        slide_images: List of paths to slide images.
        audio_files: List of paths to voiceover audio files.
        transition_videos: List of paths to transition videos.
        output_path: Path for final output video.
        temp_dir: Directory for temporary files.
        transition_duration: Duration for transitions in seconds.
        cleanup: Whether to clean up temp files after success.

    Returns:
        Path to the final video.

    Raises:
        ValueError: If slide and audio counts don't match.
        RuntimeError: If FFmpeg fails.
    """
    if len(slide_images) != len(audio_files):
        raise ValueError(
            f"Slide count ({len(slide_images)}) must match "
            f"audio count ({len(audio_files)})"
        )

    ffmpeg = get_ffmpeg_path()
    temp_path = Path(temp_dir)
    temp_path.mkdir(parents=True, exist_ok=True)

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    if output_dir and str(output_dir) != ".":
        output_dir.mkdir(parents=True, exist_ok=True)

    segments = []
    total_slides = len(slide_images)

    try:
        # Create slide videos with audio
        for i, (image, audio) in enumerate(zip(slide_images, audio_files)):
            slide_video = str(temp_path / f"slide_{i + 1:02d}.mp4")
            print(f"  Creating slide segment {i + 1}/{total_slides}...")
            create_slide_with_audio(image, audio, slide_video)
            segments.append(slide_video)

            # Add transition (except after last slide)
            if i < len(transition_videos):
                trimmed = str(temp_path / f"trans_{i + 1:02d}_trim.mp4")
                print(f"  Trimming transition {i + 1}/{len(transition_videos)}...")
                trim_transition(transition_videos[i], trimmed, transition_duration)
                segments.append(trimmed)

        # Create concat file
        concat_file = str(temp_path / "concat.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            for seg in segments:
                # Use forward slashes and escape special characters for FFmpeg
                seg_path = Path(seg).resolve()
                # FFmpeg concat requires forward slashes even on Windows
                seg_str = str(seg_path).replace("\\", "/")
                f.write(f"file '{seg_str}'\n")

        # Concatenate all segments
        print("  Concatenating segments into final video...")
        result = subprocess.run(
            [
                ffmpeg, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-movflags", "+faststart",
                output_path,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed concatenating: {result.stderr}")

        print(f"  Final video saved: {output_path}")

        # Cleanup temp files on success
        if cleanup:
            cleanup_temp_dir(temp_path)

        return output_path

    except Exception as e:
        print(f"Error during assembly: {e}")
        print(f"Temp files preserved at: {temp_path}")
        raise


def get_video_info(video_path: str) -> dict:
    """Get information about a video file.

    Args:
        video_path: Path to video file.

    Returns:
        Dictionary with video information.
    """
    ffprobe = get_ffprobe_path()

    result = subprocess.run(
        [
            ffprobe, "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return {"error": result.stderr}

    return json.loads(result.stdout)
