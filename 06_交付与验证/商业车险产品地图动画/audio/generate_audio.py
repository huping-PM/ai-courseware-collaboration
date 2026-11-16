"""Generate the approved per-scene narration and timing manifest."""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import edge_tts


HERE = Path(__file__).resolve().parent
STORYBOARD = HERE.parent.parent / "课程文案" / "商业车险产品地图-PPT分镜.md"
FFMPEG = Path(
    r"C:\Users\Administrator\AppData\Local\Temp\video-skill-verification-runtime"
    r"\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-5%"
MAX_ATTEMPTS = 3


def scene_texts() -> dict[str, str]:
    content = STORYBOARD.read_text(encoding="utf-8")
    headers = list(re.finditer(r"^### (P\d{2})\b.*$", content, re.MULTILINE))
    scenes: dict[str, str] = {}
    for index, header in enumerate(headers):
        scene_id = header.group(1)
        end = headers[index + 1].start() if index + 1 < len(headers) else len(content)
        section = content[header.end() : end]
        spoken = re.findall(r"^> [^：\n]+：(.*)$", section, re.MULTILINE)
        if not spoken:
            raise RuntimeError(f"{scene_id} has no labelled narration")
        scenes[scene_id] = "".join(spoken)
    expected = [f"P{i:02d}" for i in range(1, 18)]
    if list(scenes) != expected:
        raise RuntimeError(f"Expected {expected}; got {list(scenes)}")
    return scenes


async def synthesize(scene_id: str, text: str) -> list[dict[str, float | str]]:
    output = HERE / f"{scene_id}.mp3"
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        boundaries: list[dict[str, float | str]] = []
        try:
            communicator = edge_tts.Communicate(text, VOICE, rate=RATE)
            with output.open("wb") as audio_file:
                async for item in communicator.stream():
                    if item["type"] == "audio":
                        audio_file.write(item["data"])
                    elif item["type"] == "SentenceBoundary":
                        boundaries.append(
                            {
                                "text": item["text"],
                                "start": round(item["offset"] / 10_000_000, 3),
                                "duration": round(item["duration"] / 10_000_000, 3),
                            }
                        )
            if output.stat().st_size == 0:
                raise RuntimeError("received empty audio")
            return boundaries
        except Exception as error:  # Retry transient online TTS failures only.
            last_error = error
            output.unlink(missing_ok=True)
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(attempt)
    raise RuntimeError(f"{scene_id} synthesis failed after {MAX_ATTEMPTS} attempts: {last_error}")


def duration_seconds(path: Path) -> float:
    result = subprocess.run(
        [str(FFMPEG), "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"Duration:\s+(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError(f"Could not read duration for {path.name}: {result.stderr[-500:]}")
    return round(int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3)), 3)


def decode_check(path: Path) -> None:
    result = subprocess.run(
        [str(FFMPEG), "-v", "error", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0 or result.stderr.strip():
        raise RuntimeError(f"Decode check failed for {path.name}: {result.stderr.strip()}")


async def main() -> None:
    if not FFMPEG.is_file():
        raise RuntimeError(f"Required FFmpeg not found: {FFMPEG}")
    scenes = scene_texts()
    # A one-sentence request confirms the online voice before the full batch.
    await synthesize("_service_probe", "配音服务短句测试。")
    (HERE / "_service_probe.mp3").unlink(missing_ok=True)

    semaphore = asyncio.Semaphore(2)

    async def guarded(scene_id: str, text: str):
        async with semaphore:
            return scene_id, text, await synthesize(scene_id, text)

    generated = await asyncio.gather(*(guarded(scene_id, text) for scene_id, text in scenes.items()))
    manifest_scenes = []
    for scene_id, text, boundaries in generated:
        audio_path = HERE / f"{scene_id}.mp3"
        decode_check(audio_path)
        manifest_scenes.append(
            {
                "id": scene_id,
                "text": text,
                "src": f"audio/{scene_id}.mp3",
                "duration": duration_seconds(audio_path),
                "boundaries": boundaries,
            }
        )
    manifest = {
        "voice": VOICE,
        "rate": RATE,
        "provider": "Microsoft Edge TTS online service via edge-tts 7.2.8",
        "scenes": manifest_scenes,
    }
    (HERE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"sceneCount": len(manifest_scenes), "totalDuration": round(sum(s["duration"] for s in manifest_scenes), 3)}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise
