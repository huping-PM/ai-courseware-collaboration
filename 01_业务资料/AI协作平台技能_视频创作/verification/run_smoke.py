"""Offline smoke fixture. The sine-wave audio is TEST AUDIO, never TTS or a business sample."""
import argparse
import array
import json
import math
from pathlib import Path
import subprocess
import sys
import wave
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--browser', required=True)
    ap.add_argument('--ffmpeg', required=True)
    ap.add_argument('--engine', default='playwright')
    args = ap.parse_args(); out = args.output.resolve()
    if out.exists(): raise ValueError('Use a new smoke output directory')
    out.mkdir(parents=True); (out / 'source-audio').mkdir()
    image = Image.new('RGB', (600, 360), '#E8F7EF')
    draw = ImageDraw.Draw(image); draw.rounded_rectangle((90, 60, 510, 300), 28, fill='#34C77B'); image.save(out / 'illustration.png')
    project = {'schema_version': 1, 'title': '技术验证样例（非业务样片）', 'canvas': {'width': 1280, 'height': 720, 'fps': 25},
               'audio': {'sample_rate': 24000, 'pause': 0.1, 'tail': 0.3}, 'pages': []}
    for i in range(1, 3):
        page = {'id': f'p{i:02}', 'title': ['先确认版本，再开始修改', '各节点产物可追溯'][i-1], 'bullets': [], 'segments': [], 'source_refs': ['测试自建内容，非用户业务材料']}
        if i == 1: page['image'] = 'illustration.png'
        for j in range(1, 3):
            filename = f'source-audio/p{i:02}-s{j:02}.wav'
            samples = array.array('h', [int(2500 * math.sin(2 * math.pi * (220 + i * 70 + j * 40) * n / 24000)) for n in range(9600)])
            with wave.open(str(out / filename), 'wb') as audio:
                audio.setparams((1, 2, 24000, 0, 'NONE', 'not compressed')); audio.writeframes(samples.tobytes())
            page['segments'].append({'id': f's{j:02}', 'text': f'测试口播文字{i}-{j}，音频为测试提示音。', 'audio': filename})
            page['bullets'].append({'id': f'b{j:02}', 'text': ['检查输入文件版本', '把结果保存到新目录'][j-1], 'segment_id': f's{j:02}'})
        project['pages'].append(page)
    project_path = out / 'project.json'; project_path.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding='utf-8')
    source = out / 'source.md'; source.write_text('# 技术验证\n\n此素材仅用于工程检查，不是业务课程。', encoding='utf-8')
    commands = [
        [sys.executable, str(ROOT/'video-source-read/scripts/extract_source.py'), '--input', str(source), '--output', str(out/'extracted.md')],
        [sys.executable, str(ROOT/'video-script-plan/scripts/validate_project.py'), '--project', str(project_path), '--require-images', '--require-audio'],
        [sys.executable, str(ROOT/'video-image-assets/scripts/prepare_images.py'), '--project', str(project_path), '--output', str(out/'prepared')],
        [sys.executable, str(ROOT/'video-ppt-build/scripts/build_ppt.py'), '--project', str(project_path), '--output', str(out/'sample.pptx')],
        [sys.executable, str(ROOT/'video-voice-timeline/scripts/build_timeline.py'), '--project', str(project_path), '--output', str(out/'voice')],
        [sys.executable, str(ROOT/'video-animation-build/scripts/build_animation.py'), '--project', str(project_path), '--timeline', str(out/'voice/timeline.json'), '--output', str(out/'animation')],
        ['node', str(ROOT/'video-frame-render/scripts/render_frames.js'), '--manifest', str(out/'animation/pages-manifest.json'), '--output', str(out/'frames'), '--browser', args.browser, '--engine', args.engine],
        [sys.executable, str(ROOT/'video-compose/scripts/compose_video.py'), '--manifest', str(out/'frames/frames-manifest.json'), '--output', str(out/'video'), '--ffmpeg', args.ffmpeg],
        [args.ffmpeg, '-v', 'error', '-i', str(out/'video/final.mp4'), '-f', 'null', '-'],
    ]
    results = []
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
        results.append({'command': command, 'returncode': result.returncode, 'stdout': result.stdout[-6000:], 'stderr': result.stderr[-6000:]})
        (out / 'smoke-results.json').write_text(json.dumps({'audio': 'synthetic_test_tone_not_tts', 'results': results}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(Path(command[1]).name if len(command) > 1 else command[0], result.returncode)
        if result.returncode: print(result.stderr); raise SystemExit(result.returncode)
    print('SMOKE PASSED: local production/decode only; no TTS, FFprobe or business approval claimed.')

if __name__ == '__main__': main()
