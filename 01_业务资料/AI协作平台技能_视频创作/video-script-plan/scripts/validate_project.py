import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'video-workflow' / 'scripts'))
from common import load_project, local_path, sha256


def main():
    ap = argparse.ArgumentParser(description='Validate video project data; no generation or business approval.')
    ap.add_argument('--project', required=True)
    ap.add_argument('--require-images', action='store_true')
    ap.add_argument('--require-audio', action='store_true')
    args = ap.parse_args()
    p = Path(args.project).resolve(); data = load_project(p)
    warnings = []
    for page in data['pages']:
        if not page.get('source_refs'): warnings.append(f"{page['id']}: source_refs missing; content review required")
        if len(page['title']) > 30 or any(len(b['text']) > 60 for b in page['bullets']):
            warnings.append(f"{page['id']}: dense text; split or visually verify")
        if args.require_images and page.get('image') and not local_path(p.parent, page['image']).is_file():
            raise ValueError(f"{page['id']}: image missing")
        if args.require_audio:
            for s in page['segments']:
                if not s.get('audio') or not local_path(p.parent, s['audio']).is_file(): raise ValueError(f"{page['id']}/{s['id']}: audio missing")
    print(json.dumps({'status': 'valid', 'pages': len(data['pages']), 'sha256': sha256(p), 'warnings': warnings,
                      'business_approval': 'not_checked'}, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
