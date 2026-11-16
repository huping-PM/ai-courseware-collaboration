"""Independently verify the generated audio and synchronization manifest."""

import json
import re
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
FFMPEG = Path(r"C:\Users\Administrator\AppData\Local\Temp\video-skill-verification-runtime\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe")


def probe(path: Path) -> float:
    decoded = subprocess.run([str(FFMPEG), "-v", "error", "-i", str(path), "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if decoded.returncode or decoded.stderr.strip():
        raise RuntimeError(f"Decode failure: {path.name}: {decoded.stderr.strip()}")
    metadata = subprocess.run([str(FFMPEG), "-i", str(path), "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    match = re.search(r"Duration:\s+(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)", metadata.stderr)
    if not match:
        raise RuntimeError(f"Duration missing: {path.name}")
    return round(int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3]), 3)


manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
records = []
for scene in manifest["scenes"]:
    file_path = HERE / f"{scene['id']}.mp3"
    actual = probe(file_path)
    if actual != scene["duration"]:
        raise RuntimeError(f"Duration mismatch: {scene['id']}: {actual} vs {scene['duration']}")
    if scene["boundaries"] and scene["boundaries"][-1]["start"] + scene["boundaries"][-1]["duration"] > actual + 0.15:
        raise RuntimeError(f"Boundary outside audio: {scene['id']}")
    records.append({"id": scene["id"], "file": file_path.name, "bytes": file_path.stat().st_size, "duration": actual, "decode": "passed"})

report = {"ffmpeg": str(FFMPEG), "checkedScenes": len(records), "allPassed": True, "scenes": records}
(HERE / "decode-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"checkedScenes": len(records), "allPassed": True}, ensure_ascii=False))
