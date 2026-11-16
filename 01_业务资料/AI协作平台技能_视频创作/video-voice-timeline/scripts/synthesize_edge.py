"""Explicit online edge-tts bridge. Produces real per-sentence MP3 and a new project file."""
import argparse
import asyncio
import shutil
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'video-workflow' / 'scripts'))
from common import load_project, local_path, new_output_dir, write_json


async def synthesize(source, output, voice, rate):
    import edge_tts
    project = load_project(source)
    images = [(p, local_path(source.parent, p['image'])) for p in project['pages'] if p.get('image')]
    if any(not image.is_file() for _, image in images): raise ValueError('Project image missing')
    out = new_output_dir(output)
    (out / 'segments').mkdir(); (out / 'assets').mkdir()
    for p, image in images:
        relative = 'assets/' + p['id'] + image.suffix.lower()
        shutil.copyfile(image, out / relative); p['image'] = relative
    for page in project['pages']:
        for seg in page['segments']:
            relative = f"segments/{page['id']}-{seg['id']}.mp3"
            await asyncio.wait_for(edge_tts.Communicate(seg['text'], voice, rate=rate).save(str(out / relative)), timeout=120)
            if not (out / relative).is_file() or (out / relative).stat().st_size == 0:
                raise ValueError('TTS returned empty audio')
            seg['audio'] = relative
            print(f"Created {page['id']}/{seg['id']}")
    project['voice_provenance'] = {'provider': 'edge-tts', 'voice': voice, 'rate': rate, 'human_listening': 'required'}
    write_json(out / 'project.json', project)
    print(out / 'project.json')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--voice', required=True, help='Explicit provider voice identifier')
    ap.add_argument('--rate', default='+0%')
    args = ap.parse_args()
    asyncio.run(synthesize(args.project.resolve(), args.output.resolve(), args.voice, args.rate))

if __name__ == '__main__': main()
