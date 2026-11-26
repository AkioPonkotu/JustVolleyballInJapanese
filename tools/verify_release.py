"""Verify release integrity and install/restore against a disposable game copy."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from fontTools.ttLib import TTFont
from catalog import ROOT, load_catalogs, save
from pck import Pack, sha256


def main():
    game = Path('F:/SteamLibrary/steamapps/common/just volleyball')
    archive = ROOT / 'dist/just-volleyball-ja.zip'
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert 'JustVolleyballJA.exe' in names
        assert not any(name.endswith(('.py', '.ps1')) or name == 'requirements.txt' for name in names)
        manifest = json.loads(z.read('manifest.json'))
    messages, entries = load_catalogs()
    original = (game / 'volleyball.pck').read_bytes()
    exe = (game / 'volleyball.exe').read_bytes()
    assert sha256(original) == manifest['original_pck_sha256']
    assert sha256(exe) == manifest['original_exe_sha256']
    needed = {ord(c) for entry in entries.values() for c in entry['ja'] if 0x3000 <= ord(c) <= 0x9fff}
    missing = []
    for style in ['SemiBold', 'ExtraBold']:
        with TTFont(ROOT / f'assets/fonts/JVVolleyballJP-{style}.ttf') as font:
            cmap = font.getBestCmap()
            missing.extend(sorted(needed - cmap.keys()))
            assert 'fvar' not in font
            assert not missing, f'Font is missing codepoints: {missing}'
    with tempfile.TemporaryDirectory(prefix='install-validation-', dir=ROOT / 'work') as directory:
        scratch = Path(directory).resolve()
        assert scratch.is_relative_to((ROOT / 'work').resolve())
        package = scratch / '配布パッチ'
        with zipfile.ZipFile(archive) as z:
            z.extractall(package)
        shutil.copyfile(game / 'volleyball.exe', scratch / 'volleyball.exe')
        shutil.copyfile(game / 'volleyball.pck', scratch / 'volleyball.pck')
        base = [str(package / 'JustVolleyballJA.exe'), '--game-dir', str(scratch)]
        # Run the distributed EXE with no Python/uv on PATH, a different working
        # directory, and a Japanese package path. Dependencies must be bundled.
        env = os.environ.copy()
        env['PATH'] = str(Path(os.environ['SystemRoot']) / 'System32')
        for key in list(env):
            if key.startswith(('PYTHON', 'UV_')):
                del env[key]
        def run(flag, succeeds=True):
            result = subprocess.run(base + [flag], capture_output=True, cwd=scratch, env=env, timeout=180)
            assert (result.returncode == 0) == succeeds, result.stdout.decode('utf-8', errors='replace') + result.stderr.decode('utf-8', errors='replace')
        (scratch / 'volleyball.exe').write_bytes(exe + b'updated')
        run('--install', succeeds=False)
        assert not (scratch / 'volleyball.pck.ja-backup').exists()
        assert (scratch / 'volleyball.pck').read_bytes() == original
        (scratch / 'volleyball.exe').write_bytes(exe)
        run('--install')
        assert sha256((scratch / 'volleyball.pck.ja-backup').read_bytes()) == sha256(original)
        data = (scratch / 'volleyball.pck').read_bytes()
        patched = Pack(data, exe[81005808:81005840])
        old = Pack(original, patched.key)
        changed = {item['path'] for item in manifest['files']}
        unchanged_count = 0
        for path, entry in old.entries.items():
            if path not in changed:
                assert patched.entries[path] == entry, path
                unchanged_count += 1
        for item in manifest['files']:
            assert sha256(patched.read(item['path'])) == item['result_sha256'], item['path']
        # Reinstall, tampered PCK, and an updated EXE must all fail without losing backup.
        run('--install', succeeds=False)
        altered = bytearray(data)
        altered[-1] ^= 1
        (scratch / 'volleyball.pck').write_bytes(altered)
        run('--restore', succeeds=False)
        (scratch / 'volleyball.pck').write_bytes(data)
        (scratch / 'volleyball.exe').write_bytes(exe + b'updated')
        run('--restore', succeeds=False)
        (scratch / 'volleyball.exe').write_bytes(exe)
        run('--restore')
        assert (scratch / 'volleyball.pck').read_bytes() == original
        assert not (scratch / 'volleyball.pck.ja-backup').exists()
        assert not (scratch / 'volleyball-ja-receipt.json').exists()
    assert (game / 'volleyball.pck').read_bytes() == original
    report = {
        'build_id': '26937150', 'catalog_entries': len(entries), 'runtime_messages': manifest['unique_messages'],
        'message_context_counts': manifest['message_context_counts'],
        'guide_display_fields': 203, 'required_japanese_codepoints': len(needed), 'missing_font_codepoints': missing,
        'install_restore_roundtrip': 'passed; original PCK restored byte for byte in disposable directory',
        'release_exe_without_python_uv_on_path': 'passed',
        'japanese_package_path_and_different_working_directory': 'passed',
        'unsupported_build_install_rejection': 'passed',
        'reinstall_rejection': 'passed', 'tampered_pck_restore_rejection': 'passed',
        'updated_exe_restore_rejection': 'passed', 'unchanged_original_resource_entries': unchanged_count,
        'changed_resource_hashes': 'all verified', 'installed_game_modified': False,
        'release_zip_sha256': sha256((ROOT / 'dist/just-volleyball-ja.zip').read_bytes())
    }
    save(ROOT / 'evidence/patch-validation.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
