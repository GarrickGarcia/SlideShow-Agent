"""Create COP presentation with dynamic custom transitions.

Reuses existing slides and audio, generates new animated transitions
using Kling O1 Reference-to-Video which morphs from start frame (@Image1)
to end frame (@Image2) for true slide-to-slide transitions.

Transitions:
1. Logo -> Man on Arrow: Linework morphs, text slides away
2. Man on Arrow -> Calendar: Man runs off, swirling forms calendar
3. Calendar -> People Circle: Clock dissolves into people network
4. People Circle -> Join Today: Circle expands into reaching hands
"""

import sys
import os

# Add the skill scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".claude", "skills", "slideshow-video-agent"))

from scripts.transition_generator import generate_transitions_batch
from scripts.video_assembler import assemble_slideshow_with_single_audio
from scripts.utils import ensure_output_dirs

# Paths to existing assets
SLIDE_IMAGES = [
    "./output/slides/slide_01.png",
    "./output/slides/slide_02.png",
    "./output/slides/slide_03.png",
    "./output/slides/slide_04.png",
    "./output/slides/slide_05.png",
]

AUDIO_FILE = "./output/audio/narration_full.mp3"
OUTPUT_PATH = "./output/cop_presentation_dynamic.mp4"

# Custom transition prompts using @Image1 (start) and @Image2 (end) references
# Each prompt describes how to morph from the current slide to the next
TRANSITION_PROMPTS = [
    # Transition 1: Slide 1 (COP Logo) -> Slide 2 (Man on Arrow)
    (
        "Starting from @Image1, the circular logo linework begins to pulse with energy. "
        "The interconnected lines gracefully untangle and flow to the right side, "
        "morphing and reshaping into the silhouette of a person on an arrow as shown in @Image2. "
        "Text elements elegantly slide and transform into the new positions. "
        "The transformation completes smoothly, landing exactly on the composition of @Image2. "
        "Professional, fluid motion throughout."
    ),

    # Transition 2: Slide 2 (Man on Arrow) -> Slide 3 (Calendar/Clock)
    (
        "Starting from @Image1, the arrow graphic extends dramatically while the figure "
        "springs to life and runs up the arrow path. As the runner and arrow animate off screen, "
        "swirling lines spiral into view, dancing and flowing before condensing into the "
        "calendar and clock shapes shown in @Image2. Text transitions smoothly to match "
        "the new layout. The animation ends precisely on @Image2. "
        "Energetic but professional, like an animated infographic."
    ),

    # Transition 3: Slide 3 (Calendar/Clock) -> Slide 4 (People Circle)
    (
        "Starting from @Image1, the calendar and clock graphics spin gently, their lines "
        "unraveling into flowing ribbons. The ribbons swirl outward in an expanding pattern, "
        "then curve back and reform into the circle of connected human figures shown in @Image2. "
        "Each figure appears one by one around the ring. Text transitions with a smooth fade. "
        "The animation lands exactly on @Image2 - time transforming into community. "
        "Elegant, professional, satisfying motion."
    ),

    # Transition 4: Slide 4 (People Circle) -> Slide 5 (Join Today)
    (
        "Starting from @Image1, the circle of connected people pulses with energy, then "
        "the figures gracefully move outward, arms extending. The expanding motion transforms "
        "as the elements reshape into the reaching hands composition shown in @Image2. "
        "Text sweeps in to match the final layout. The animation conveys invitation and welcome, "
        "ending precisely on @Image2 with a sense of completeness and call to action. "
        "Professional but warm and engaging."
    ),
]


def main():
    print("Creating COP Presentation with DYNAMIC Transitions")
    print("=" * 60)
    print("Using existing slides and audio")
    print("Generating TRUE MORPH transitions (Kling O1 Reference-to-Video)")
    print("Each transition morphs from start slide to end slide exactly")
    print("=" * 60)

    # Verify existing assets exist
    for slide in SLIDE_IMAGES:
        if not os.path.exists(slide):
            print(f"ERROR: Slide not found: {slide}")
            print("Please run create_cop_presentation.py first to generate slides.")
            return None

    if not os.path.exists(AUDIO_FILE):
        print(f"ERROR: Audio not found: {AUDIO_FILE}")
        print("Please run create_cop_presentation.py first to generate audio.")
        return None

    print(f"\nSlides: {len(SLIDE_IMAGES)} existing slides")
    print(f"Audio: {AUDIO_FILE}")
    print(f"Transitions: {len(TRANSITION_PROMPTS)} custom morph animations")
    print(f"Output: {OUTPUT_PATH}")
    print()

    # Setup output directories
    dirs = ensure_output_dirs("./output")
    transitions_dir = str(dirs["transitions"])
    temp_dir = str(dirs["temp"])

    # Generate new transitions with custom prompts
    print("=" * 60)
    print("GENERATING MORPH TRANSITIONS (Kling O1 Reference-to-Video)")
    print("Using start (@Image1) and end (@Image2) frames for true morphing")
    print("=" * 60)

    transition_videos = generate_transitions_batch(
        slide_images=SLIDE_IMAGES,
        output_dir=transitions_dir,
        transition_style="morph",  # Fallback style (won't be used since all have custom prompts)
        custom_prompts=TRANSITION_PROMPTS,
    )

    print(f"\nGenerated {len(transition_videos)} morph transitions")

    # Assemble final video
    print("\n" + "=" * 60)
    print("ASSEMBLING FINAL VIDEO (FFmpeg)")
    print("Syncing slides with existing audio track")
    print("=" * 60)

    final_video = assemble_slideshow_with_single_audio(
        slide_images=SLIDE_IMAGES,
        audio_file=AUDIO_FILE,
        transition_videos=transition_videos,
        output_path=OUTPUT_PATH,
        temp_dir=temp_dir,
        transition_duration=2.5,
    )

    print("\n" + "=" * 60)
    print(f"COMPLETE! Video saved to: {final_video}")
    print("=" * 60)

    return final_video


if __name__ == "__main__":
    result = main()
    if result:
        print(f"\nDynamic presentation complete: {result}")
