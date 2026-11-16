---
name: adobe-animate-fla-export
description: Use when a course project needs Adobe Animate/FLA files exported into full-scene PNG frame sequences for animation microcourse rendering, especially for 栗子微课 AI提取库 assets, FLA/XFL source projects, JSFL batch export, and replacing static preview templates with true animated frames.
---

# Adobe Animate FLA Export

Use this skill when the user asks to solve static FLA template playback, export `.fla`/`.xfl` animation frames, integrate Adobe Animate assets into `assets/animation_frames`, or make microcourse characters/scenes move from FLA source files.

## Core Rule

For AI提取库 or other final-video FLA templates, prefer this pipeline:

`FLA source -> Adobe Animate JSFL export -> assets/animation_frames/<collection>/<scene_id>/frame_XXXX.png -> renderer reads frame sequence -> final MP4`

Do not rebuild these scenes by manually layering background PNGs and character PNGs when integrated FLA frame sequences are available.

## Repository Defaults

For `microclass-skill-main`:

- FLA source templates: `assets/scenes/lizi_2026/ai_extraction_sources/`
- Expected frame output: `assets/animation_frames/ai_extraction/<scene_id>/frame_XXXX.png`
- Frame manifest: `assets/animation_frames/ai_extraction/manifest.json`
- Batch JSFL exporter: `scripts/export_all_fla_frames.jsfl`
- Preview sequence fallback: `scripts/generate_ai_extraction_preview_sequences.py`
- Final renderer example: `scripts/render_course_final.py`

## Workflow

1. Check whether true exported frames already exist:
   - Look for `assets/animation_frames/ai_extraction/<scene_id>/frame_*.png`.
   - Verify `manifest.json` has `exported: true` and expected frame counts.
2. If frames are missing and Adobe Animate is installed:
   - Open Adobe Animate.
   - Run `scripts/export_all_fla_frames.jsfl` from Animate via `File > Commands > Run Script`, or run Animate with JSFL if the installed version supports command-line execution.
   - Ensure output goes to `assets/animation_frames/ai_extraction/` with the scene ids used by the renderer: `title`, `lizi_exterior`, `meeting_three`, `sicong_side`, `sicong_front`, `meimei_screen`, `lele_angle1`, `lele_angle2`, `knowledge_bg`, `summary`, `graphic_template`.
3. If Adobe Animate is not installed or cannot run:
   - Say clearly that true FLA vector animation cannot be exported on this machine.
   - Use preview sequence fallback only as a temporary substitute: `python -B scripts/generate_ai_extraction_preview_sequences.py`.
   - Mark it as fallback, not equivalent to true Animate-exported frames.
4. Re-render the course after frames are present.
5. Validate:
   - Run `ffmpeg -v error -i <final.mp4> -f null -`.
   - Extract two frames from the same animated scene and compare pixels; mean difference should be greater than zero.
   - Check logs show frame-sequence usage, such as `FLA-frames`, not static preview-only mode.

## Adobe Animate Notes

- `.fla` files are zipped XFL projects. Reading XML can inspect canvas, fps, layers, and nominal frame count, but it does not render vector animation.
- True rendering requires Adobe Animate or a compatible renderer that can execute the Animate timeline.
- Export complete scene frames, not separated character layers, because AI提取库 templates are designed as integrated scenes.
- Keep frame file names zero-padded: `frame_0001.png`, `frame_0002.png`, etc.
- If replacing fallback frames with true Animate frames, clear the scene directory first to avoid mixed old/new frames.

## Safety

- Delete or replace only frame directories inside the expected course or asset output path.
- Never delete FLA source files unless the user explicitly asks.
- Keep preview fallback scripts available; they are useful when Animate is unavailable.
