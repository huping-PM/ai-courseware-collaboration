"""Read-only dependency inventory; never installs or contacts providers."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output')
    args = ap.parse_args()
    binaries = {x: shutil.which(x) for x in ['python', 'node', 'ffmpeg', 'ffprobe']}
    browsers = [Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Microsoft/Edge/Application/msedge.exe',
                Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Google/Chrome/Application/chrome.exe']
    node_modules = None
    if binaries['node']:
        result = subprocess.run([binaries['node'], '-e', "try{process.stdout.write(require.resolve('puppeteer-core'))}catch(e){process.exit(1)}"], capture_output=True, text=True)
        if result.returncode == 0: node_modules = result.stdout
    report = {'python': sys.executable, 'binaries': binaries,
              'python_packages': {name: importlib.util.find_spec(name) is not None for name in ['pptx', 'PIL', 'docx', 'pdfplumber', 'edge_tts', 'imageio_ffmpeg']},
              'browsers': [str(p) for p in browsers if p.is_file()], 'puppeteer_core': node_modules,
              'external_services': 'not_checked', 'fonts': 'must_check_actual_render',
              'note': 'Presence only; does not prove compatibility, API availability or rendering success.'}
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        p = Path(args.output)
        if p.exists(): raise ValueError('Refusing to overwrite existing report')
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(output + '\n', encoding='utf-8')
    print(output)

if __name__ == '__main__': main()
