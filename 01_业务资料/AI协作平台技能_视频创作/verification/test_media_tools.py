import importlib.util
import json
import math
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
from types import SimpleNamespace
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIMELINE = ROOT / "video-voice-timeline" / "scripts" / "build_timeline.py"
COMPOSE = ROOT / "video-compose" / "scripts" / "compose_video.py"
CHECK = ROOT / "video-quality-check" / "scripts" / "check_video.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)], text=True,
                          capture_output=True, check=False)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_wav(path, sample_rate, sample_count):
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(struct.pack("<" + "h" * sample_count, *([0] * sample_count)))


class MediaToolTests(unittest.TestCase):
    def project(self, root):
        data = {
            "schema_version": 1, "title": "离线测试", "canvas": {"width": 1280, "height": 720, "fps": 25},
            "audio": {"sample_rate": 16000, "pause": 0.25, "tail": 0.30},
            "pages": [{"id": "p01", "title": "页", "bullets": [{"id": "b01", "text": "点", "segment_id": "s01"}],
                       "segments": [{"id": "s01", "text": "测试音", "audio": "audio/s01.wav"}]}],
        }
        (root / "audio").mkdir()
        (root / "project.json").write_text(json.dumps(data), encoding="utf-8")
        return root / "project.json"

    def test_timeline_measures_pcm_samples_and_uses_ceiling_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self.project(root)
            write_wav(root / "audio/s01.wav", 16000, 1600)  # synthetic test tone, 0.1s
            output = root / "timeline-output"
            result = run(TIMELINE, "--project", project, "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            timeline = json.loads((output / "timeline.json").read_text(encoding="utf-8"))
            page = timeline["pages"][0]
            self.assertEqual(page["audio_duration"], 0.1)
            self.assertEqual(page["narration_end"], 0.1)
            self.assertEqual(page["frames"], math.ceil((0.1 + 0.3) * 25))
            self.assertEqual(page["duration"], page["frames"] / 25)
            self.assertTrue((output / "audio/p01.wav").is_file())

    def test_timeline_rejects_missing_segment_audio_and_nonempty_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self.project(root)
            missing = run(TIMELINE, "--project", project, "--output", root / "out")
            self.assertNotEqual(missing.returncode, 0)
            occupied = root / "occupied"
            occupied.mkdir()
            (occupied / "old.txt").write_text("old", encoding="utf-8")
            write_wav(root / "audio/s01.wav", 16000, 1)
            result = run(TIMELINE, "--project", project, "--output", occupied)
            self.assertNotEqual(result.returncode, 0)

    def test_compose_rejects_missing_or_nonsequential_frames_before_ffmpeg(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "frames").mkdir()
            (root / "audio").mkdir()
            manifest = {"schema_version": 1, "project_sha256": "x", "timeline_sha256": "y", "fps": 25,
                        "width": 1280, "height": 720,
                        "pages": [{"id": "p01", "directory": "frames", "frames": 2, "duration": 0.08,
                                   "audio": "audio/p01.wav"}]}
            path = root / "frames-manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run(COMPOSE, "--manifest", path, "--output", root / "out", "--ffmpeg", "definitely-missing")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("frame", result.stderr.lower())

    def test_quality_report_uses_probe_facts_and_marks_semantic_review_required(self):
        checker = load_module("check_video_report_under_test", CHECK)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "final.mp4"
            video.write_bytes(b"placeholder")
            composition = root / "composition.json"
            composition.write_text(json.dumps({"fps": 25, "width": 1280, "height": 720, "frame_count": 10, "output": "final.mp4"}), encoding="utf-8")
            report = root / "report.json"
            facts = {"streams": [{"codec_type": "video", "codec_name": "h264", "width": 1280, "height": 720,
                                  "avg_frame_rate": "25/1", "nb_frames": "10"},
                                 {"codec_type": "audio", "codec_name": "aac", "sample_rate": "16000", "channels": 1}],
                     "format": {"duration": "0.4"}}
            with mock.patch.object(checker.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=json.dumps(facts), stderr="")):
                checker.check(video, composition, "fake-ffprobe", report)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(data["automatic"]["video_stream"]["pass"])
            self.assertTrue(data["automatic"]["frame_count"]["pass"])
            self.assertTrue(data["review_required"])

    def test_quality_check_refuses_to_overwrite_existing_report(self):
        checker = load_module("check_video_overwrite_under_test", CHECK)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "final.mp4"; video.write_bytes(b"placeholder")
            composition = root / "composition.json"
            composition.write_text(json.dumps({"fps": 25, "width": 1280, "height": 720, "frame_count": 10}), encoding="utf-8")
            report = root / "report.json"; report.write_text("keep", encoding="utf-8")
            with mock.patch.object(checker.subprocess, "run") as probe_run:
                with self.assertRaises(ValueError): checker.check(video, composition, "fake-ffprobe", report)
            probe_run.assert_not_called()
            self.assertEqual(report.read_text(encoding="utf-8"), "keep")

    def test_quality_check_keeps_space_containing_probe_path_as_one_argument(self):
        checker = load_module("check_video_under_test", CHECK)
        facts = {"streams": [{"codec_type": "video", "codec_name": "h264", "width": 1280, "height": 720,
                              "avg_frame_rate": "25/1", "nb_frames": "10"},
                             {"codec_type": "audio", "codec_name": "aac"}]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); video = root / "final.mp4"; video.write_bytes(b"video")
            composition = root / "composition.json"
            composition.write_text(json.dumps({"fps": 25, "width": 1280, "height": 720, "frame_count": 10}), encoding="utf-8")
            completed = SimpleNamespace(returncode=0, stdout=json.dumps(facts), stderr="")
            with mock.patch.object(checker.subprocess, "run", return_value=completed) as probe_run:
                report = checker.check(video, composition, r"C:\Program Files\ffprobe\ffprobe.exe", root / "report.json")
            self.assertTrue(report["automatic_pass"])
            self.assertEqual(probe_run.call_args.args[0][0], r"C:\Program Files\ffprobe\ffprobe.exe")

    def test_quality_main_returns_nonzero_when_automatic_checks_fail(self):
        checker = load_module("check_video_main_under_test", CHECK)
        with mock.patch.object(checker, "check", return_value={"automatic_pass": False}), \
             mock.patch.object(sys, "argv", ["check_video.py", "--video", "x", "--composition", "y", "--ffprobe", "z", "--output", "r"]):
            self.assertNotEqual(checker.main(), 0)


if __name__ == "__main__":
    unittest.main()
