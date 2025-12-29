# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SlideShow-Agent is an AI agent that creates video presentations with AI-generated slides, voiceovers, and animated transitions. It uses fal.ai APIs (Nano Banana Pro, Eleven Labs, Kling 2.6 Pro) and FFmpeg for video assembly.

## Skill Location

The main skill is at `.claude/skills/slideshow-video-agent/SKILL.md`

## Python Environment

- If `.venv` or `venv` exists, use: `.venv\Scripts\python.exe`
- Otherwise use: `C:\Users\ggarcia\AppData\Local\ESRI\conda\envs\arcgispro-py3-vscode\python.exe`
- Always quote Windows paths and include `.exe` extension
- Use forward slashes or escape backslashes in paths

## Setup

1. Add FAL_KEY to `.env` file (get from https://fal.ai/dashboard/keys)
2. Install FFmpeg and add to PATH
3. Install dependencies: `pip install -r requirements.txt`

## Development Guidelines

- Avoid emojis and special Unicode characters in scripts (Windows encoding issues)
- Store secrets in `.env` or config files, never in code
- `.env` is in `.gitignore`

## Project Structure

```
SlideShow-Agent/
  .env                    # FAL_KEY (not in git)
  requirements.txt        # Python dependencies
  Reference Images/       # Brand logos for slide generation
  output/                 # Generated videos (not in git)
  .claude/skills/slideshow-video-agent/
    SKILL.md              # Main skill definition
    scripts/              # Python modules
    references/           # Documentation
```

## Key Scripts

- `scripts/orchestrator.py` - Main workflow coordinator
- `scripts/slide_generator.py` - Nano Banana Pro integration
- `scripts/voiceover.py` - Eleven Labs TTS integration
- `scripts/transition_generator.py` - Kling video transitions
- `scripts/video_assembler.py` - FFmpeg video assembly
