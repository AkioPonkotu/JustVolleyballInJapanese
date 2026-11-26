import contextlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import catalog
from build_patch import inject, json_pointer
from pck import Pack, encrypt_blob
from patch_game import prepare


class PackTests(unittest.TestCase):
    def test_encrypted_append_and_checksum(self):
        key = bytes(range(32))
        header = bytearray(112)
        struct.pack_into('<6IQQ', header, 0, 0x43504447, 4, 4, 7, 1, 3, 112, 112)
        empty = bytes(header) + struct.pack('<I', 0) + encrypt_blob(b'', key, 'empty')
        with tempfile.TemporaryDirectory() as temp:
            first, second = Path(temp) / 'first.pck', Path(temp) / 'second.pck'
            original = Pack(empty, key)
            original.write_patched(first, {'a.txt': b'unchanged', 'b.txt': b'old'})
            before = Pack(first.read_bytes(), key)
            before.write_patched(second, {'b.txt': '日本語'.encode(), 'c.json': b'{"new":true}'})
            after = Pack(second.read_bytes(), key)
            self.assertEqual(after.read('a.txt'), b'unchanged')
            self.assertEqual(after.read('b.txt'), '日本語'.encode())
            self.assertEqual(after.read('c.json'), b'{"new":true}')
            self.assertEqual(after.entries['a.txt'], before.entries['a.txt'])
            bad = bytearray(second.read_bytes())
            bad[after.file_base + after.entries['b.txt'].offset + 40] ^= 1
            with self.assertRaises(ValueError):
                Pack(bytes(bad), key).read('b.txt')
            with self.assertRaises(ValueError):
                Pack(second.read_bytes(), bytes(32))

    def test_wrong_build_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'volleyball.exe').write_bytes(b'wrong executable')
            (root / 'volleyball.pck').write_bytes(b'wrong pack')
            (root / 'manifest.json').write_text(json.dumps({
                'original_exe_sha256': '0' * 64, 'original_pck_sha256': '0' * 64}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Unsupported game build'):
                prepare(root, root)
            self.assertFalse((root / 'volleyball.pck.ja-backup').exists())
            self.assertEqual((root / 'volleyball.pck').read_bytes(), b'wrong pack')


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_root = catalog.ROOT
        catalog.ROOT = Path(self.temp.name)

    def tearDown(self):
        catalog.ROOT = self.old_root
        self.temp.cleanup()

    def test_reimport_preserves_human_work(self):
        with contextlib.redirect_stdout(io.StringIO()):
            catalog.import_seed('ui', {'play': 'プレイ'})
        path = catalog.ROOT / 'translations/ja/ui.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        ident = catalog.stable_id('ui', 'play')
        data['entries'][ident].update(ja='遊ぶ', status='reviewed', note='人による修正')
        catalog.save(path, data)
        with contextlib.redirect_stdout(io.StringIO()):
            catalog.import_seed('ui', {'play': '上書きしない', 'back': '戻る'})
        updated = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(updated['entries'][ident], data['entries'][ident])
        self.assertEqual(list(updated['entries'])[0], ident)

    def test_placeholder_loss_and_order_are_rejected(self):
        for source, ja in [('{kb:jump}', 'ジャンプ'), ('%s %d', '%d %s')]:
            with self.subTest(source=source):
                with contextlib.redirect_stdout(io.StringIO()):
                    catalog.import_seed('check', {source: ja})
                with self.assertRaises(ValueError):
                    catalog.load_catalogs()
                (catalog.ROOT / 'translations/ja/check.json').unlink()

    def test_source_mutation_is_rejected(self):
        with contextlib.redirect_stdout(io.StringIO()):
            catalog.import_seed('ui', {'play': 'プレイ'})
        path = catalog.ROOT / 'translations/ja/ui.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        next(iter(data['entries'].values()))['source'] = 'changed'
        catalog.save(path, data)
        with self.assertRaises(ValueError):
            catalog.load_catalogs()

    def test_duplicate_json_key_is_rejected(self):
        path = catalog.ROOT / 'duplicate.json'
        path.write_text('{"ja":"first","ja":"second"}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            catalog.read_catalog(path)

    def test_context_disambiguates_identical_sources(self):
        self.assertNotEqual(catalog.stable_id('howto', 'setting', '/a'),
                            catalog.stable_id('howto', 'setting', '/b'))


class BindingTests(unittest.TestCase):
    def test_injected_statement_cannot_join_next_line(self):
        source = 'func fill():\n\tr.clear()\n'
        patched = inject(source, r'^func fill\([^\n]+\n?', 'text = tr(text)')
        self.assertIn('\ttext = tr(text)\n\tr.clear()', patched)
        with self.assertRaises(ValueError):
            inject(source + source, r'^func fill\([^\n]+\n?', 'pass')

    def test_guide_pointer_preserves_ids(self):
        source = {'categories': [{'sid': '1.1', 'body': ['English']}]}
        node, key = json_pointer(source, '/categories/0/body/0')
        node[key] = '日本語'
        self.assertEqual(source['categories'][0]['sid'], '1.1')
        self.assertEqual(source['categories'][0]['body'], ['日本語'])


if __name__ == '__main__':
    unittest.main()
