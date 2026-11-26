from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from steam_game import find_game_directory, _values


class SteamGameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'Steam'
        (self.root / 'steamapps').mkdir(parents=True)

    def install(self, library, folder='just volleyball', appid='5037200'):
        apps = library / 'steamapps'
        apps.mkdir(parents=True, exist_ok=True)
        (apps / 'appmanifest_5037200.acf').write_text(
            f'"AppState" {{ "appid" "{appid}" "installdir" "{folder}" }}', encoding='utf-8')
        game = apps / 'common' / folder
        game.mkdir(parents=True)
        for name in ('volleyball.exe', 'volleyball.pck'):
            (game / name).touch()
        return game

    def test_primary_library_without_library_metadata(self):
        game = self.install(self.root)
        with patch('steam_game.steam_directory', return_value=self.root):
            self.assertEqual(find_game_directory(), game)

    def test_secondary_library_with_unicode_and_spaces(self):
        library = Path(self.temp.name) / '別ドライブ Steam Library'
        game = self.install(library, 'custom install folder')
        escaped = str(library).replace('\\', '\\\\')
        (self.root / 'steamapps/libraryfolders.vdf').write_text(
            f'"libraryfolders" {{ "1" {{ "path" "{escaped}" }} }}', encoding='utf-8-sig')
        self.assertEqual(find_game_directory(self.root), game)

    def test_missing_pck_is_not_detected(self):
        game = self.install(self.root)
        (game / 'volleyball.pck').unlink()
        self.assertIsNone(find_game_directory(self.root))

    def test_wrong_appid_is_not_detected(self):
        self.install(self.root, appid='123')
        self.assertIsNone(find_game_directory(self.root))

    def test_unavailable_steam(self):
        with patch('steam_game.steam_directory', return_value=None):
            self.assertIsNone(find_game_directory())

    def test_invalid_metadata(self):
        (self.root / 'steamapps/libraryfolders.vdf').write_bytes(b'\xff\xfe')
        for content in ('invalid', '"appid" "5037200" "installdir" "../outside"',
                        '"appid" "5037200" "installdir" ""'):
            with self.subTest(content=content):
                (self.root / 'steamapps/appmanifest_5037200.acf').write_text(content)
                self.assertIsNone(find_game_directory(self.root))

    def test_vdf_windows_path_escaping(self):
        self.assertEqual(_values(r'"path" "F:\\SteamLibrary"', 'path'), ['F:\\SteamLibrary'])


if __name__ == '__main__':
    unittest.main()
