"""Inspect declared media facts with ffprobe; semantic and visual review stays manual."""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-workflow" / "scripts"))
from common import read_json, sha256, write_json


def fraction(value):
    top, bottom = str(value).split("/", 1)
    return float(top) / float(bottom)


def item(actual, expected, detail=None):
    passed = actual == expected
    return {"pass": passed, "actual": actual, "expected": expected, **({"detail": detail} if detail else {})}


def probe(video, ffprobe):
    command = [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)]
    try: completed = subprocess.run(command, text=True, capture_output=True, check=False)
    except OSError as exc: raise ValueError(f"Cannot run ffprobe: {exc}") from exc
    if completed.returncode: raise ValueError(f"ffprobe failed: {completed.stderr.strip()}")
    try: return __import__("json").loads(completed.stdout)
    except ValueError as exc: raise ValueError("ffprobe did not emit JSON") from exc


def check(video_path, composition_path, ffprobe, output_path):
    video = Path(video_path).resolve(); composition = read_json(composition_path)
    output = Path(output_path).resolve()
    if output.exists(): raise ValueError(f"Refusing to overwrite existing report: {output}")
    if not video.is_file(): raise ValueError("Video does not exist")
    for name in ("fps", "width", "height", "frame_count"):
        if name not in composition: raise ValueError(f"composition missing {name}")
    facts = probe(video, ffprobe); streams = facts.get("streams", [])
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    subtitle_streams = [stream for stream in streams if stream.get("codec_type") == "subtitle"]
    automatic = {"video_stream": {"pass": len(video_streams) == 1, "actual": len(video_streams), "expected": 1},
                 "audio_stream": {"pass": len(audio_streams) == 1, "actual": len(audio_streams), "expected": 1},
                 "subtitle_policy": {"pass": not subtitle_streams, "actual": len(subtitle_streams), "expected": 0, "detail": "First version contains no subtitle stream."}}
    if "output_sha256" in composition:
        automatic["output_sha256"] = item(sha256(video), composition["output_sha256"])
    if len(video_streams) == 1:
        stream = video_streams[0]
        automatic["video_codec"] = item(stream.get("codec_name"), "h264")
        automatic["resolution"] = item([stream.get("width"), stream.get("height")], [composition["width"], composition["height"]])
        try: actual_fps = fraction(stream.get("avg_frame_rate"))
        except (TypeError, ValueError, ZeroDivisionError): actual_fps = None
        automatic["fps"] = item(actual_fps, float(composition["fps"]))
        raw_frames = stream.get("nb_frames")
        try: actual_frames = int(raw_frames)
        except (TypeError, ValueError): actual_frames = None
        automatic["frame_count"] = item(actual_frames, composition["frame_count"], "Unavailable nb_frames fails rather than being inferred.")
    if len(audio_streams) == 1:
        automatic["audio_codec"] = item(audio_streams[0].get("codec_name"), "aac")
    passed = all(check["pass"] for check in automatic.values())
    report = {"schema_version": 1, "video": str(video), "composition": str(Path(composition_path).resolve()), "probe": {"duration": facts.get("format", {}).get("duration"), "stream_count": len(streams)}, "automatic": automatic, "automatic_pass": passed, "review_required": ["Play the complete video and review narration, page timing, visual layout, source accuracy, and semantic correspondence. Automated probing cannot assess pixels or meaning."], "result": "pass" if passed else "fail"}
    write_json(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--video", required=True); parser.add_argument("--composition", required=True); parser.add_argument("--ffprobe", required=True); parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try: report = check(args.video, args.composition, args.ffprobe, args.output)
    except (OSError, ValueError, subprocess.SubprocessError) as exc: print(f"quality check failed: {exc}", file=sys.stderr); return 2
    return 0 if report["automatic_pass"] else 1


if __name__ == "__main__": raise SystemExit(main())
