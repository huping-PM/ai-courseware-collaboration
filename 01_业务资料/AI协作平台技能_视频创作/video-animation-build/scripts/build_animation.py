"""Build self-contained deterministic HTML pages from project and timeline inputs."""
from __future__ import annotations

import argparse
import base64
import html
import shutil
import sys
import re
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[2] / "video-workflow" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))
from common import local_path, new_output_dir, sha256, validate_timeline, write_json  # noqa: E402


def image_data_uri(path: Path) -> str:
    types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
    mime = types.get(path.suffix.lower())
    if not mime:
        raise ValueError(f"Unsupported page image type: {path.suffix}")
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def validate_basic_layout(project: dict) -> None:
    font = project["style"]["font"]
    if not re.fullmatch(r"[\w .-]{1,80}", font, re.UNICODE):
        raise ValueError("基础模板不接受不安全的字体名称")
    for page in project["pages"]:
        if len(page["title"]) > 30:
            raise ValueError(f"页面 {page['id']} 标题超过基础模板容量，请拆页或精简标题")
        count = len(page["bullets"]); has_image = bool(page.get("image"))
        # Matches the PPT template: 28px body text and the usable list widths.
        per_line = 23 if has_image else 38
        lines = 4 if count == 1 else 2 if count in (2, 3) else 1
        capacity = per_line * lines
        for bullet in page["bullets"]:
            if len(bullet["text"]) > capacity:
                raise ValueError(f"页面 {page['id']} 要点超过基础模板容量（{capacity}字），请拆页")


def page_html(project: dict, page: dict, timing: dict, project_path: Path) -> str:
    style = project["style"]
    windows = {segment["id"]: [segment["start"], segment["end"]] for segment in timing["segments"]}
    bullet_html = "".join(f'<li data-segment-id="{html.escape(b["segment_id"])}">{html.escape(b["text"])}</li>' for b in page["bullets"])
    image = ""
    if page.get("image"):
        path = local_path(project_path.parent, page["image"])
        if not path.is_file(): raise ValueError(f"Page image is missing: {page['image']}")
        image = f'<img class="page-image" alt="" src="{image_data_uri(path)}">'
    reveal = ",".join(f'{json_key(key)}:{value!r}' for key, value in windows.items())
    list_class = "with-image" if image else "without-image"
    return f'''<!doctype html><html lang="{html.escape(project.get("language", "zh-CN"))}"><head><meta charset="utf-8"><style>
html,body{{margin:0;width:1280px;height:720px;overflow:hidden;background:{style['background']};font-family:"{style['font']}",sans-serif}}
#stage{{box-sizing:border-box;width:1280px;height:720px;padding:48px 64px;border-left:18px solid {style['accent']};color:{style['foreground']};opacity:1}}
h1{{margin:0 0 42px;font-size:42px;line-height:1.25}} ul{{margin:0;padding-left:32px}} ul.with-image{{width:720px}} ul.without-image{{width:1100px}} li{{font-size:28px;line-height:1.45;margin:16px 0;opacity:0}} .page-image{{position:absolute;right:64px;top:155px;width:360px;height:402px;object-fit:contain}}
</style></head><body><main id="stage"><h1>{html.escape(page['title'])}</h1><ul class="{list_class}">{bullet_html}</ul>{image}</main><script>
const windows={{{reveal}}}; const narrationEnd={timing['narration_end']!r}; const duration={timing['duration']!r}; window.__layoutErrors=[];
function clamp(v,a,b){{return Math.max(a,Math.min(b,v));}}
window.seek=function(t){{t=Number(t);if(!Number.isFinite(t))t=0; document.querySelectorAll('[data-segment-id]').forEach(el=>{{const w=windows[el.dataset.segmentId];const fadeIn=Math.min(.18,Math.max(.05,(w[1]-w[0])*.25));el.style.opacity=clamp((t-w[0])/fadeIn,0,1);}}); const fade=duration>narrationEnd?1-clamp((t-narrationEnd)/(duration-narrationEnd),0,1):1;document.getElementById('stage').style.opacity=fade;}};
window.seek(0); document.querySelectorAll('h1,li').forEach(el=>{{if(el.scrollHeight>el.clientHeight||el.scrollWidth>el.clientWidth)window.__layoutErrors.push(el.tagName+' text overflow');}}); window.__videoReady=true;
</script></body></html>'''


def json_key(value: str) -> str:
    """Quote strings safely for JavaScript/CSS font values."""
    import json
    return json.dumps(value, ensure_ascii=False)


def build(project_path: Path, timeline_path: Path, output: Path) -> None:
    project, timeline = validate_timeline(project_path, timeline_path)
    validate_basic_layout(project)
    output = new_output_dir(output)
    pages = []
    for page, timing in zip(project["pages"], timeline["pages"]):
        html_name = f"{page['id']}.html"
        (output / html_name).write_text(page_html(project, page, timing, project_path), encoding="utf-8")
        source_audio = local_path(timeline_path.parent, timing["audio"])
        audio_name = f"audio/{page['id']}{source_audio.suffix.lower()}"
        target_audio = output / audio_name; target_audio.parent.mkdir(exist_ok=True)
        shutil.copyfile(source_audio, target_audio)
        pages.append({"id": page["id"], "html": html_name, "frames": timing["frames"], "duration": timing["duration"], "audio": audio_name})
    write_json(output / "pages-manifest.json", {"schema_version": 1, "project_sha256": sha256(project_path), "timeline_sha256": sha256(timeline_path), "fps": project["canvas"]["fps"], "width": 1280, "height": 720, "pages": pages})


def main() -> int:
    parser = argparse.ArgumentParser(description="Build self-contained deterministic animation HTML.")
    parser.add_argument("--project", required=True, type=Path); parser.add_argument("--timeline", required=True, type=Path); parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        build(args.project.resolve(), args.timeline.resolve(), args.output.resolve())
    except (OSError, ValueError, ImportError) as exc:
        print(f"build_animation: {exc}", file=sys.stderr); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
