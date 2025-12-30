"""Create Communities of Practice presentation with minimal text design.

Uses:
- Hope voice for narration
- COP Logo for branding (navy blue and white color scheme)
- Minimal text on slides (3-4 bullet points max)
- Fuller narration script (says "Community of Practice" not "COP")
- AI validation of slides with Claude Haiku 4.5
"""

import sys
import os

# Add the skill scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".claude", "skills", "slideshow-video-agent"))

from scripts import PresentationConfig, Slide, create_slideshow_video

# Define the 5 slides with separate bullet_points (displayed) and narration (spoken)
# Note: narration always says "Community of Practice" - never abbreviated "COP"
slides = [
    Slide(
        title="Communities of Practice",
        bullet_points=[
            "Small groups, big ideas",
            "Cross-departmental learning",
            "Collaborative growth"
        ],
        narration=(
            "Welcome to Abonmarche Communities of Practice. "
            "These are small, cross-departmental groups designed to help employees "
            "learn new tools, share real-world expertise, and strengthen collaboration "
            "across the organization. Communities of Practice are not lectures or "
            "passive trainings. They are discussion-driven, collaborative environments "
            "where every participant contributes."
        ),
        visual_description="The Communities of Practice logo prominently centered",
        is_title_slide=True
    ),
    Slide(
        title="Why Join?",
        bullet_points=[
            "Accelerate professional growth",
            "Improve workflows",
            "Build peer connections"
        ],
        narration=(
            "The goal of a Community of Practice is to accelerate professional growth, "
            "improve workflows, and create meaningful connections across teams. "
            "You will learn from peers who face similar challenges and opportunities, "
            "sharing practical solutions from real projects."
        ),
        visual_description="Line-art icon of an ascending growth path or upward arrow with person figure",
        is_title_slide=False
    ),
    Slide(
        title="How It Works",
        bullet_points=[
            "Monthly meetings",
            "Flexible agenda",
            "Tool demos and Q&A"
        ],
        narration=(
            "Communities of Practice meet monthly following a structured but flexible agenda. "
            "Sessions may include tool or technology deep dives, project knowledge-sharing, "
            "workflow demonstrations, technical insights and lessons learned, and open "
            "question and answer sessions with group discussion."
        ),
        visual_description="Line-art icon of a calendar or meeting/clock symbol",
        is_title_slide=False
    ),
    Slide(
        title="Group Structure",
        bullet_points=[
            "10 participants max",
            "Join up to 3 groups",
            "Cross-departmental mix"
        ],
        narration=(
            "Each Community of Practice is capped at 10 participants to encourage engagement "
            "and meaningful conversation. Participants may join up to three Communities of "
            "Practice based on interest areas. Groups are intentionally cross-departmental "
            "to promote diverse perspectives and build internal networks."
        ),
        visual_description="Line-art icon of connected people in a circle, similar to the COP logo symbol",
        is_title_slide=False
    ),
    Slide(
        title="Join Today",
        bullet_points=[
            "Spots fill quickly",
            "Learn and contribute",
            "Sharpen your skills"
        ],
        narration=(
            "Enrollment is limited and spots fill quickly. Join a Community of Practice "
            "to learn, contribute, and sharpen your skills alongside peers from across "
            "the organization. Grow professionally through peer learning, stay current "
            "with evolving tools and technology, and build a culture of shared knowledge "
            "and collaboration."
        ),
        visual_description="Line-art icon of a hand reaching upward or people joining together",
        is_title_slide=False
    ),
]

# Create presentation config
config = PresentationConfig(
    slides=slides,
    voice="Hope",  # Using Hope voice (ID: tnSpp4vdxKPjI9w0GnoV)
    transition_style="morph",  # Morphing transitions for dynamic graphics
    transition_duration=2.5,
    reference_images=[
        "Reference Images/COP Logo.png"  # Primary style guide for colors and branding
    ],
    output_path="./output/cop_presentation_v2.mp4",
    validate_slides=True,  # Enable AI validation with Claude Haiku 4.5
    max_validation_attempts=3
)

if __name__ == "__main__":
    print("Creating Communities of Practice Presentation (v2)")
    print("=" * 50)
    print(f"Slides: {len(slides)}")
    print(f"Voice: {config.voice}")
    print(f"Transition: {config.transition_style}")
    print(f"Validation: {config.validate_slides}")
    print(f"Reference: {config.reference_images}")
    print(f"Output: {config.output_path}")
    print("=" * 50)

    result = create_slideshow_video(config)
    print(f"\nPresentation complete: {result}")
