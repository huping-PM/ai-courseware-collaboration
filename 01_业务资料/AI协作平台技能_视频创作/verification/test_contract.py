import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'video-workflow' / 'scripts'))
from common import load_project, local_path, new_output_dir, validate_timeline, sha256


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.p = self.root / 'project.json'
        self.data = {'schema_version': 1, 'title': '测试', 'pages': [
            {'id': 'p01', 'title': '标题', 'bullets': [{'id': 'b1', 'text': '要点', 'segment_id': 's1'}],
             'segments': [{'id': 's1', 'text': '讲解。'}]}]}
        self.save()

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        self.p.write_text(json.dumps(self.data), encoding='utf-8')

    def test_defaults_and_arbitrary_page_count(self):
        for i in range(2, 17):
            page = copy.deepcopy(self.data['pages'][0]); page['id'] = f'p{i:02}'
            self.data['pages'].append(page)
        self.save()
        result = load_project(self.p)
        self.assertEqual(16, len(result['pages']))
        self.assertEqual(25, result['canvas']['fps'])

    def test_bad_mapping_rejected(self):
        self.data['pages'][0]['bullets'][0]['segment_id'] = 'missing'
        self.save()
        with self.assertRaises(ValueError): load_project(self.p)

    def test_duplicate_page_rejected(self):
        self.data['pages'].append(copy.deepcopy(self.data['pages'][0])); self.save()
        with self.assertRaises(ValueError): load_project(self.p)

    def test_paths_confined(self):
        for value in ['../secret', 'C:/secret', 'https://example.com/a', '/tmp/a']:
            with self.assertRaises(ValueError): local_path(self.root, value)

    def test_nonempty_output_rejected(self):
        with self.assertRaises(ValueError): new_output_dir(self.root)

    def test_stale_timeline_rejected(self):
        t = self.root / 'timeline.json'
        t.write_text(json.dumps({'schema_version': 1, 'project_sha256': 'old', 'pages': []}), encoding='utf-8')
        with self.assertRaises(ValueError): validate_timeline(self.p, t)

    def test_nan_configuration_rejected(self):
        self.data['audio'] = {'tail': float('nan')}; self.save()
        with self.assertRaises(ValueError): load_project(self.p)

if __name__ == '__main__': unittest.main()
