"""Shared local data checks. No network or side effects on import."""
import hashlib
import json
import math
from pathlib import Path, PureWindowsPath
import re


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def local_path(base, relative):
    if not isinstance(relative, str) or not relative or '\x00' in relative:
        raise ValueError('Expected a nonempty relative file path')
    if ':' in relative or PureWindowsPath(relative).is_absolute() or relative.startswith(('/', '\\')):
        raise ValueError(f'Only local relative paths are allowed: {relative}')
    base = Path(base).resolve()
    path = (base / relative.replace('\\', '/')).resolve()
    if not path.is_relative_to(base): raise ValueError(f'Path leaves its project: {relative}')
    return path


def new_output_dir(path):
    path = Path(path).resolve()
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise ValueError(f'Output must be a new or empty directory: {path}')
    path.mkdir(parents=True, exist_ok=True)
    return path


def _text(value, label):
    if not isinstance(value, str) or not value.strip(): raise ValueError(f'{label}: nonempty string required')
    return value


def _number(value, label, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{label}: finite number in [{low},{high}] required')


def _ids(items, label):
    if not isinstance(items, list) or not items: raise ValueError(f'{label}: nonempty list required')
    values = []
    for item in items:
        if not isinstance(item, dict): raise ValueError(f'{label}: objects required')
        value = item.get('id')
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', value):
            raise ValueError(f'{label}: invalid id {value!r}')
        values.append(value)
    if len(set(values)) != len(values): raise ValueError(f'{label}: duplicate ids')
    return values


def load_project(path):
    data = read_json(path)
    if not isinstance(data, dict) or data.get('schema_version') != 1: raise ValueError('schema_version must be 1')
    _text(data.get('title'), 'title')
    data['canvas'] = {'width': 1280, 'height': 720, 'fps': 25, **data.get('canvas', {})}
    c = data['canvas']
    if c['width'] != 1280 or c['height'] != 720: raise ValueError('Basic template requires 1280x720')
    if type(c['fps']) is not int or not 1 <= c['fps'] <= 60: raise ValueError('fps must be integer 1..60')
    data['style'] = {'font': 'Microsoft YaHei', 'background': '#F7FBF8', 'foreground': '#0F3D2E', 'accent': '#34C77B', **data.get('style', {})}
    _text(data['style']['font'], 'style.font')
    for key in ['background', 'foreground', 'accent']:
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', str(data['style'][key])): raise ValueError(f'Invalid style.{key}')
    data['audio'] = {'sample_rate': 24000, 'pause': 0.25, 'tail': 0.3, **data.get('audio', {})}
    a = data['audio']
    if type(a['sample_rate']) is not int or a['sample_rate'] not in [16000, 22050, 24000, 44100, 48000]:
        raise ValueError('Unsupported audio sample_rate')
    _number(a['pause'], 'audio.pause', 0, 5)
    _number(a['tail'], 'audio.tail', 0.05, 5)
    _ids(data.get('pages'), 'pages')
    for p in data['pages']:
        _text(p.get('title'), 'page.title')
        sids = _ids(p.get('segments'), f"{p['id']}.segments")
        _ids(p.get('bullets'), f"{p['id']}.bullets")
        if len(p['bullets']) > 5: raise ValueError('Basic template supports at most 5 bullets; split page')
        for s in p['segments']:
            _text(s.get('text'), 'segment.text')
            if 'audio' in s: local_path(Path(path).parent, s['audio'])
        for b in p['bullets']:
            _text(b.get('text'), 'bullet.text')
            if b.get('segment_id') not in sids: raise ValueError(f"{p['id']}: unknown segment_id")
        if 'image' in p: local_path(Path(path).parent, p['image'])
    return data


def validate_timeline(project_path, timeline_path):
    project = load_project(project_path)
    tl = read_json(timeline_path)
    if tl.get('schema_version') != 1 or tl.get('project_sha256') != sha256(project_path):
        raise ValueError('Timeline belongs to another project revision; rebuild it')
    if tl.get('fps') != project['canvas']['fps'] or tl.get('sample_rate') != project['audio']['sample_rate']:
        raise ValueError('Timeline frame/sample rate mismatch')
    if tl.get('tail') != project['audio']['tail']: raise ValueError('Timeline tail mismatch')
    if _ids(tl.get('pages'), 'timeline.pages') != [p['id'] for p in project['pages']]:
        raise ValueError('Timeline page order mismatch')
    for p, t in zip(project['pages'], tl['pages']):
        if _ids(t.get('segments'), 'timeline.segments') != [s['id'] for s in p['segments']]:
            raise ValueError('Timeline segment order mismatch')
        previous = 0
        for source, seg in zip(p['segments'], t['segments']):
            if seg.get('text') != source['text']: raise ValueError('Timeline text mismatch')
            _number(seg.get('start'), 'start', 0, 86400)
            _number(seg.get('end'), 'end', 0, 86400)
            if seg['start'] < previous - 1e-6 or seg['end'] <= seg['start']: raise ValueError('Overlapping/empty segment')
            previous = seg['end']
        for field in ['audio_duration', 'narration_end', 'duration']:
            _number(t.get(field), field, 0, 86400)
        if abs(t['narration_end'] - previous) > 1e-5 or abs(t['audio_duration'] - previous) > 1e-5:
            raise ValueError('Audio end does not match final segment')
        expected = math.ceil((t['audio_duration'] + tl['tail']) * tl['fps'])
        if type(t.get('frames')) is not int or t['frames'] != expected or abs(t['duration'] - expected / tl['fps']) > 1e-6:
            raise ValueError('Timeline frame budget mismatch')
        if not local_path(Path(timeline_path).parent, t.get('audio')).is_file(): raise ValueError('Page audio missing')
    return project, tl
