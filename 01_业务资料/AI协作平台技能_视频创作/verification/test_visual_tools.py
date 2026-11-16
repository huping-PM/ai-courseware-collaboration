"""End-to-end contract checks for the editable PPT and deterministic HTML builders."""
from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import re
import unittest
import wave
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
PPT = PACKAGE / "video-ppt-build" / "scripts" / "build_ppt.py"
ANIMATION = PACKAGE / "video-animation-build" / "scripts" / "build_animation.py"


class VisualToolTests(unittest.TestCase):
    def make_project(self, root: Path) -> tuple[Path, Path]:
        (root / "audio").mkdir()
        (root / "image.png").write_bytes(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/"
            "OQmZVQAAAABJRU5ErkJggg=="
        ))
        with wave.open(str(root / "audio" / "p01.wav"), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(24000)
            handle.writeframes(b"\0\0" * 24000)
        project = {
            "schema_version": 1, "title": "测试课程", "language": "zh-CN",
            "canvas": {"width": 1280, "height": 720, "fps": 25},
            "style": {"font": "Microsoft YaHei", "background": "#F7FBF8", "foreground": "#0F3D2E", "accent": "#34C77B"},
            "audio": {"sample_rate": 24000, "pause": 0.25, "tail": 0.30},
            "pages": [{"id": "p01", "title": "核心观点", "image": "image.png",
                       "bullets": [{"id": "b01", "text": "一个可编辑要点", "segment_id": "s01"}],
                       "segments": [{"id": "s01", "text": "一句完整口播。", "audio": "audio/p01.wav"}],
                       "source_refs": ["source.md#1"]}],
        }
        project_path = root / "project.json"
        project_path.write_text(json.dumps(project, ensure_ascii=False), encoding="utf-8")
        timeline = {"schema_version": 1, "project_sha256": hashlib.sha256(project_path.read_bytes()).hexdigest(),
                    "fps": 25, "sample_rate": 24000, "tail": 0.3,
                    "pages": [{"id": "p01", "audio": "audio/p01.wav",
                               "segments": [{"id": "s01", "text": "一句完整口播。", "start": 0.0, "end": 1.0}],
                               "narration_end": 1.0, "audio_duration": 1.0, "duration": 1.32, "frames": 33}]}
        timeline_path = root / "timeline.json"
        timeline_path.write_text(json.dumps(timeline, ensure_ascii=False), encoding="utf-8")
        return project_path, timeline_path

    def run_tool(self, *args: Path | str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, *map(str, args)], text=True, capture_output=True)

    def test_build_ppt_writes_editable_slide_with_sentence_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project, _ = self.make_project(Path(temp))
            output = Path(temp) / "deck.pptx"
            result = self.run_tool(PPT, "--project", project, "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            from pptx import Presentation
            deck = Presentation(output)
            self.assertEqual(len(deck.slides), 1)
            self.assertIn("核心观点", " ".join(s.text for s in deck.slides[0].shapes if hasattr(s, "text")))
            self.assertIn("一句完整口播。", deck.slides[0].notes_slide.notes_text_frame.text)

    def test_ppt_contains_a_non_square_image_without_stretching(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); project, _ = self.make_project(root)
            from PIL import Image
            Image.new("RGB", (400, 100), "blue").save(root / "image.png")
            output = root / "deck.pptx"
            result = self.run_tool(PPT, "--project", project, "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            from pptx import Presentation
            picture = next(shape for shape in Presentation(output).slides[0].shapes if shape.shape_type == 13)
            self.assertAlmostEqual(picture.width / picture.height, 4.0, places=2)

    def test_both_builders_reject_text_that_exceeds_basic_template_capacity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); project, timeline = self.make_project(root)
            data = json.loads(project.read_text(encoding="utf-8"))
            data["pages"][0]["bullets"][0]["text"] = "过长内容" * 70
            project.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            # Refresh the timeline's required raw-project digest without changing its segment mapping.
            timeline_data = json.loads(timeline.read_text(encoding="utf-8"))
            timeline_data["project_sha256"] = hashlib.sha256(project.read_bytes()).hexdigest()
            timeline.write_text(json.dumps(timeline_data, ensure_ascii=False), encoding="utf-8")
            ppt = self.run_tool(PPT, "--project", project, "--output", root / "too-long.pptx")
            animation = self.run_tool(ANIMATION, "--project", project, "--timeline", timeline, "--output", root / "too-long")
            self.assertNotEqual(ppt.returncode, 0); self.assertIn("拆页", ppt.stderr)
            self.assertNotEqual(animation.returncode, 0); self.assertIn("拆页", animation.stderr)

    def test_builders_reject_existing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project, timeline = self.make_project(root)
            deck = root / "exists.pptx"; deck.write_bytes(b"exists")
            output_dir = root / "exists"; output_dir.mkdir(); (output_dir / "old.txt").write_text("old")
            self.assertNotEqual(self.run_tool(PPT, "--project", project, "--output", deck).returncode, 0)
            self.assertNotEqual(self.run_tool(ANIMATION, "--project", project, "--timeline", timeline, "--output", output_dir).returncode, 0)

    def test_build_animation_embeds_image_copies_audio_and_exposes_seek(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project, timeline = self.make_project(root)
            output = root / "animation"
            result = self.run_tool(ANIMATION, "--project", project, "--timeline", timeline, "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "pages-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["project_sha256"], hashlib.sha256(project.read_bytes()).hexdigest())
            page = manifest["pages"][0]
            self.assertEqual(page["frames"], 33)
            self.assertTrue((output / page["audio"]).is_file())
            html = (output / page["html"]).read_text(encoding="utf-8")
            self.assertIn("window.seek", html)
            self.assertIn("window.__videoReady", html)
            self.assertIn("window.__layoutErrors", html)
            self.assertNotIn("transition:", html)
            self.assertIn("data:image/png;base64", html)
            script = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
            probe = '''
const vm=require('vm'); const script=process.argv[1];
const stage={style:{}}, bullet={dataset:{segmentId:'s01'},style:{},tagName:'LI',scrollHeight:1,clientHeight:1,scrollWidth:1,clientWidth:1};
const document={querySelectorAll:q=>q==='[data-segment-id]'?[bullet]:[bullet],querySelector:q=>stage,getElementById:q=>stage};
const window={}; vm.runInNewContext(script,{window,document,Number,Math});
window.seek(.10); const once=JSON.stringify([bullet.style.opacity,stage.style.opacity]);
window.seek(.70); window.seek(.10); const twice=JSON.stringify([bullet.style.opacity,stage.style.opacity]);
if(once!==twice) process.exit(1);
'''
            deterministic = subprocess.run(["node", "-e", probe, script], text=True, capture_output=True)
            self.assertEqual(deterministic.returncode, 0, deterministic.stderr)


if __name__ == "__main__":
    unittest.main()
