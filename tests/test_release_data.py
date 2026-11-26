import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import patch_app
import release_data


class ReleaseDataTests(unittest.TestCase):
    def test_snapshot_matches_sources_and_payload_hashes(self):
        release_data.verify_snapshot()

    def test_corrupt_missing_and_escaping_payloads_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'payload').mkdir()
            (root / 'payload/test.bin').write_bytes(b'changed')
            for payload, error in [('payload/test.bin', ValueError),
                                   ('payload/missing.bin', FileNotFoundError),
                                   ('../outside.bin', ValueError)]:
                with self.subTest(payload=payload):
                    (root / 'manifest.json').write_text(json.dumps({'files': [{
                        'path': 'resource', 'payload': payload,
                        'payload_sha256': hashlib.sha256(b'expected').hexdigest(),
                    }]}), encoding='utf-8')
                    with self.assertRaises(error):
                        release_data.verified_payloads(root)

    def test_stale_sources_are_rejected(self):
        with patch.object(release_data, 'source_hashes', return_value={'changed': 'hash'}):
            with self.assertRaisesRegex(ValueError, 'stale'):
                release_data.verify_snapshot()

    def test_frozen_app_uses_embedded_data_not_exe_directory(self):
        with patch.object(sys, 'frozen', True, create=True), \
                patch.object(sys, '_MEIPASS', 'C:/embedded', create=True), \
                patch.object(sys, 'executable', 'C:/elsewhere/JustVolleyballJA.exe'):
            self.assertEqual(patch_app.package_directory(), Path('C:/embedded/patch-data'))


if __name__ == '__main__':
    unittest.main()
