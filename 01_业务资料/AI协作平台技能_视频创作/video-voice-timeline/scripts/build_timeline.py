"""Build a measured, local narration timeline; never calls a TTS service."""
import argparse
import math
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-workflow" / "scripts"))
from common import load_project, local_path, new_output_dir, sha256, write_json


def pcm16_mono(source, sample_rate, ffmpeg):
    """Return PCM frames from source; use wave directly only for matching WAV."""
    try:
        with wave.open(str(source), "rb") as stream:
            if stream.getnchannels() == 1 and stream.getsampwidth() == 2 and stream.getframerate() == sample_rate and stream.getcomptype() == "NONE":
                return stream.readframes(stream.getnframes())
    except (wave.Error, EOFError):
        pass
    if not ffmpeg:
        raise ValueError(f"Audio needs ffmpeg conversion: {source}")
    with tempfile.TemporaryDirectory() as temp:
        converted = Path(temp) / "converted.wav"
        command = [ffmpeg, "-y", "-v", "error", "-i", str(source), "-ac", "1", "-ar", str(sample_rate), "-c:a", "pcm_s16le", str(converted)]
        try:
            completed = subprocess.run(command, text=True, capture_output=True, check=False)
        except OSError as exc:
            raise ValueError(f"Cannot run ffmpeg for audio conversion: {exc}") from exc
        if completed.returncode:
            raise ValueError(f"ffmpeg audio conversion failed for {source}: {completed.stderr.strip()}")
        with wave.open(str(converted), "rb") as stream:
            if (stream.getnchannels(), stream.getsampwidth(), stream.getframerate(), stream.getcomptype()) != (1, 2, sample_rate, "NONE"):
                raise ValueError("ffmpeg did not produce PCM16 mono audio")
            return stream.readframes(stream.getnframes())


def build(project_path, output_path, ffmpeg=None):
    project_path = Path(project_path).resolve()
    project = load_project(project_path)
    output = new_output_dir(output_path)
    audio_dir = output / "audio"
    audio_dir.mkdir()
    rate, pause, tail, fps = project["audio"]["sample_rate"], project["audio"]["pause"], project["audio"]["tail"], project["canvas"]["fps"]
    pause_bytes = b"\0\0" * round(pause * rate)
    pages = []
    for page in project["pages"]:
        chunks, segments, cursor = [], [], 0.0
        for index, segment in enumerate(page["segments"]):
            if not segment.get("audio"):
                raise ValueError(f"Missing existing single-sentence audio for {page['id']}/{segment['id']}; synthesize it before building a timeline")
            source = local_path(project_path.parent, segment["audio"])
            if not source.is_file():
                raise ValueError(f"Segment audio does not exist: {segment['audio']}")
            pcm = pcm16_mono(source, rate, ffmpeg)
            seconds = len(pcm) / (2 * rate)
            start, end = cursor, cursor + seconds
            segments.append({"id": segment["id"], "text": segment["text"], "start": start, "end": end})
            chunks.append(pcm)
            cursor = end
            if index + 1 < len(page["segments"]):
                chunks.append(pause_bytes)
                cursor += len(pause_bytes) / (2 * rate)
        page_audio = audio_dir / f"{page['id']}.wav"
        with wave.open(str(page_audio), "wb") as stream:
            stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(rate)
            stream.writeframes(b"".join(chunks))
        frames = math.ceil((cursor + tail) * fps)
        pages.append({"id": page["id"], "audio": f"audio/{page['id']}.wav", "segments": segments,
                      "narration_end": cursor, "audio_duration": cursor, "duration": frames / fps, "frames": frames})
    timeline = {"schema_version": 1, "project_sha256": sha256(project_path), "fps": fps, "sample_rate": rate, "tail": tail, "pages": pages}
    write_json(output / "timeline.json", timeline)
    return timeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True); parser.add_argument("--output", required=True); parser.add_argument("--ffmpeg")
    args = parser.parse_args()
    try:
        build(args.project, args.output, args.ffmpeg)
    except (OSError, ValueError, wave.Error) as exc:
        print(f"timeline failed: {exc}", file=sys.stderr); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
