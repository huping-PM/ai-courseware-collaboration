"""Fit local project images within a size limit without stretching."""
import argparse
from pathlib import Path
import sys
from PIL import Image, ImageOps
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'video-workflow' / 'scripts'))
from common import load_project, local_path, new_output_dir, sha256, write_json


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project', required=True); ap.add_argument('--output', required=True)
    ap.add_argument('--max-edge', type=int, default=1280); ap.add_argument('--quality', type=int, default=85)
    a = ap.parse_args()
    if not 128 <= a.max_edge <= 8192 or not 1 <= a.quality <= 95: raise ValueError('Invalid image conversion parameters')
    project_path = Path(a.project).resolve(); p = load_project(project_path)
    sources = [(page['id'], local_path(project_path.parent, page['image'])) for page in p['pages'] if page.get('image')]
    if any(not source.is_file() for _, source in sources): raise ValueError('Referenced image missing')
    out = new_output_dir(a.output); rows = []
    for pid, source in sources:
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image); image.thumbnail((a.max_edge, a.max_edge))
            transparent = 'A' in image.getbands() or 'transparency' in image.info
            extension = '.png' if transparent else '.jpg'; dest = out / (pid + extension)
            if transparent: image.convert('RGBA').save(dest, optimize=True)
            else: image.convert('RGB').save(dest, quality=a.quality, optimize=True)
            rows.append({'page_id': pid, 'file': dest.name, 'source_sha256': sha256(source), 'width': image.width, 'height': image.height})
    write_json(out / 'assets-manifest.json', {'schema_version': 1, 'project_sha256': sha256(project_path), 'images': rows,
        'note': 'Update project image paths explicitly, then rebuild timeline; visual meaning/OCR not checked.'})
    print(out / 'assets-manifest.json')

if __name__ == '__main__': main()
