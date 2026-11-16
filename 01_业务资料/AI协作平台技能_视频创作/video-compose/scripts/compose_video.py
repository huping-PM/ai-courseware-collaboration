"""Compose strictly validated rendered frames and local page audio with ffmpeg."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-workflow" / "scripts"))
from common import local_path, new_output_dir, read_json, sha256, write_json


def png_size(path):
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n": raise ValueError(f"Not a PNG frame: {path}")
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def checked_pages(manifest_path):
    manifest = read_json(manifest_path)
    required = ["schema_version", "project_sha256", "timeline_sha256", "fps", "width", "height", "pages"]
    if any(key not in manifest for key in required) or manifest["schema_version"] != 1: raise ValueError("Invalid frames manifest")
    if not isinstance(manifest["pages"], list) or not manifest["pages"]: raise ValueError("frames manifest pages must be nonempty")
    seen, result = set(), []
    for page in manifest["pages"]:
        page_id, count = page.get("id"), page.get("frames")
        if not isinstance(page_id, str) or page_id in seen or type(count) is not int or count < 1: raise ValueError("Invalid page id or frame count")
        seen.add(page_id)
        directory = local_path(manifest_path.parent, page.get("directory")); audio = local_path(manifest_path.parent, page.get("audio"))
        if not directory.is_dir() or not audio.is_file(): raise ValueError(f"Page {page_id} frame directory or audio is missing")
        expected = [f"f{i:05d}.png" for i in range(count)]
        actual = sorted(item.name for item in directory.glob("*.png"))
        if actual != expected: raise ValueError(f"Page {page_id} frames must be strictly continuous f00000.png through f{count - 1:05d}.png")
        for name in expected:
            if png_size(directory / name) != (manifest["width"], manifest["height"]): raise ValueError(f"Page {page_id} frame size differs from manifest")
        result.append((page, directory, audio))
    return manifest, result


def run(command):
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode: raise ValueError(f"ffmpeg failed: {completed.stderr.strip()}")


def compose(manifest_path, output_path, ffmpeg):
    manifest_path = Path(manifest_path).resolve(); manifest, pages = checked_pages(manifest_path)
    if not ffmpeg or not shutil.which(ffmpeg): raise ValueError("ffmpeg is required and was not found")
    output = new_output_dir(output_path)
    pieces = []
    for index, (page, directory, audio) in enumerate(pages):
        piece = output / f"page-{index:03d}.mp4"; pieces.append(piece)
        run([ffmpeg, "-y", "-v", "error", "-framerate", str(manifest["fps"]), "-start_number", "0", "-i", str(directory / "f%05d.png"), "-i", str(audio), "-frames:v", str(page["frames"]), "-t", str(page["duration"]), "-filter:a", "apad", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(manifest["fps"]), "-c:a", "aac", "-movflags", "+faststart", str(piece)])
    listing = output / "concat.txt"
    listing.write_text("".join("file '" + str(piece.resolve()).replace("'", "'\\\\''") + "'\n" for piece in pieces), encoding="utf-8")
    final = output / "final.mp4"
    run([ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(final)])
    composition = {"schema_version": 1, "input_manifest_sha256": sha256(manifest_path), "project_sha256": manifest["project_sha256"], "timeline_sha256": manifest["timeline_sha256"], "fps": manifest["fps"], "width": manifest["width"], "height": manifest["height"], "frame_count": sum(page[0]["frames"] for page in pages), "output": "final.mp4", "output_sha256": sha256(final), "pages": len(pages), "checks": {"continuous_frames": True, "explicit_frame_limit": True, "per_page_h264_aac": True, "concat": "ffmpeg concat demuxer"}}
    write_json(output / "composition.json", composition)
    return composition


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--manifest", required=True); parser.add_argument("--output", required=True); parser.add_argument("--ffmpeg", required=True)
    args = parser.parse_args()
    try: compose(args.manifest, args.output, args.ffmpeg)
    except (OSError, ValueError, subprocess.SubprocessError) as exc: print(f"compose failed: {exc}", file=sys.stderr); return 2
    return 0


if __name__ == "__main__": raise SystemExit(main())
