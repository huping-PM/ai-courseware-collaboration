"""Build a basic, editable 16:9 course deck from a validated project.json."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[2] / "video-workflow" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))
from common import load_project, local_path  # noqa: E402


def rgb(value: str):
    from pptx.dml.color import RGBColor
    return RGBColor.from_string(value.lstrip("#"))


def add_textbox(slide, left, top, width, height, text, *, font, size, color, bold=False):
    from pptx.enum.text import MSO_ANCHOR
    from pptx.util import Pt
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.clear(); frame.word_wrap = True; frame.vertical_anchor = MSO_ANCHOR.TOP
    paragraph = frame.paragraphs[0]; paragraph.text = text
    paragraph.font.name = font; paragraph.font.size = Pt(size); paragraph.font.bold = bold; paragraph.font.color.rgb = color
    return box


def validate_basic_layout(project: dict) -> None:
    """Keep the fixed basic template readable instead of shrinking arbitrary text."""
    font = project["style"]["font"]
    if not re.fullmatch(r"[\w .-]{1,80}", font, re.UNICODE):
        raise ValueError("基础模板不接受不安全的字体名称")
    for page in project["pages"]:
        if len(page["title"]) > 30:
            raise ValueError(f"页面 {page['id']} 标题超过基础模板容量，请拆页或精简标题")
        count = len(page["bullets"]); has_image = bool(page.get("image"))
        # 22pt Chinese text needs roughly 29 logical pixels per character.
        # The image and list indentation leave about 688px / 1,068px respectively.
        per_line = 23 if has_image else 38
        lines = 4 if count == 1 else 2 if count in (2, 3) else 1
        capacity = per_line * lines
        for bullet in page["bullets"]:
            if len(bullet["text"]) > capacity:
                raise ValueError(f"页面 {page['id']} 要点超过基础模板容量（{capacity}字），请拆页")


def add_contained_picture(slide, path: Path, left, top, width, height) -> None:
    from PIL import Image
    with Image.open(path) as image:
        source_width, source_height = image.size
    if source_width <= 0 or source_height <= 0: raise ValueError(f"Invalid image dimensions: {path}")
    scale = min(width / source_width, height / source_height)
    draw_width, draw_height = int(source_width * scale), int(source_height * scale)
    slide.shapes.add_picture(str(path), left + (width - draw_width) // 2, top + (height - draw_height) // 2, width=draw_width, height=draw_height)


def build(project_path: Path, output: Path) -> None:
    if output.exists():
        raise ValueError(f"Refusing to overwrite existing output: {output}")
    project = load_project(project_path)
    validate_basic_layout(project)
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches, Pt

    deck = Presentation(); deck.slide_width = Inches(13.333333); deck.slide_height = Inches(7.5)
    blank = deck.slide_layouts[6]
    style = project["style"]
    for page in project["pages"]:
        slide = deck.slides.add_slide(blank)
        bg = slide.background.fill; bg.solid(); bg.fore_color.rgb = rgb(style["background"])
        accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(.18), Inches(7.5))
        accent.fill.solid(); accent.fill.fore_color.rgb = rgb(style["accent"]); accent.line.fill.background()
        add_textbox(slide, Inches(.65), Inches(.43), Inches(11.9), Inches(.68), page["title"], font=style["font"], size=29, color=rgb(style["foreground"]), bold=True)
        has_image = bool(page.get("image"))
        text_width = Inches(7.45 if has_image else 11.7)
        bullet_top = Inches(1.48)
        bullet_height = Inches(4.95 / len(page["bullets"]))
        for index, bullet in enumerate(page["bullets"]):
            point_size = 22 if len(page["bullets"]) <= 2 else 20 if len(page["bullets"]) == 3 else 18 if len(page["bullets"]) == 4 else 17
            box = add_textbox(slide, Inches(.86), bullet_top + bullet_height * index, text_width, bullet_height - Inches(.08), "• " + bullet["text"], font=style["font"], size=point_size, color=rgb(style["foreground"]))
            box.text_frame.paragraphs[0].space_after = Pt(0)
        if has_image:
            image_path = local_path(project_path.parent, page["image"])
            if not image_path.is_file():
                raise ValueError(f"Page image is missing: {page['image']}")
            add_contained_picture(slide, image_path, Inches(8.65), Inches(1.55), Inches(3.85), Inches(4.3))
        notes = slide.notes_slide.notes_text_frame
        notes.text = "\n".join(segment["text"] for segment in page["segments"])
    output.parent.mkdir(parents=True, exist_ok=True)
    deck.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an editable basic 16:9 PPT deck.")
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        build(args.project.resolve(), args.output.resolve())
    except (OSError, ValueError, ImportError) as exc:
        print(f"build_ppt: {exc}", file=sys.stderr); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
