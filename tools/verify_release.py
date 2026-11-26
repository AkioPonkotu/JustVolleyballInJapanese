"""Verify release integrity and install/restore against a disposable game copy."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from fontTools.ttLib import TTFont
from catalog import ROOT, load_catalogs, save
from pck import Pack, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=ROOT / 'dist/just-volleyball-ja/JustVolleyballJA.exe')
    args = parser.parse_args()
    game = Path('F:/SteamLibrary/steamapps/common/just volleyball')
    manifest = json.loads((ROOT / 'packaging/patch-data/manifest.json').read_text(encoding='utf-8'))
    messages, entries = load_catalogs()
    installed_before = sha256((game / 'volleyball.pck').read_bytes())
    original_path = game / 'volleyball.pck'
    if installed_before != manifest['original_pck_sha256']:
        original_path = game / 'volleyball.pck.ja-backup'
    original = original_path.read_bytes()
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
        package.mkdir()
        # Only the EXE is copied. No external manifest, payloads, or Python.
        shutil.copyfile(args.exe, package / 'JustVolleyballJA.exe')
        shutil.copyfile(game / 'volleyball.exe', scratch / 'volleyball.exe')
        (scratch / 'volleyball.pck').write_bytes(original)
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
        # Stray files beside the EXE must not replace the embedded data.
        (package / 'manifest.json').write_text('{}', encoding='utf-8')
        result = subprocess.run([base[0], '--verify-package'], cwd=scratch, env=env,
                                capture_output=True, timeout=180)
        assert result.returncode == 0, result.stderr
        (package / 'manifest.json').unlink()
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
        # Reinstall automatically restores the original before applying the patch.
        run('--install')
        data = (scratch / 'volleyball.pck').read_bytes()
        assert sha256((scratch / 'volleyball.pck.ja-backup').read_bytes()) == sha256(original)
        state = json.loads((scratch / 'volleyball-ja-receipt.json').read_text(encoding='utf-8'))
        assert state['patched_sha256'] == sha256(data)
        # Tampered PCK and an updated EXE must fail without losing the backup.
        altered = bytearray(data)
        altered[-1] ^= 1
        (scratch / 'volleyball.pck').write_bytes(altered)
        run('--install', succeeds=False)
        run('--restore', succeeds=False)
        assert (scratch / 'volleyball.pck').read_bytes() == altered
        assert (scratch / 'volleyball.pck.ja-backup').read_bytes() == original
        (scratch / 'volleyball.pck').write_bytes(data)
        (scratch / 'volleyball.exe').write_bytes(exe + b'updated')
        run('--install', succeeds=False)
        run('--restore', succeeds=False)
        assert (scratch / 'volleyball.pck').read_bytes() == data
        assert (scratch / 'volleyball.pck.ja-backup').read_bytes() == original
        (scratch / 'volleyball.exe').write_bytes(exe)
        run('--restore')
        assert (scratch / 'volleyball.pck').read_bytes() == original
        assert not (scratch / 'volleyball.pck.ja-backup').exists()
        assert not (scratch / 'volleyball-ja-receipt.json').exists()
    assert sha256((game / 'volleyball.pck').read_bytes()) == installed_before
    report = {
        'build_id': '26937150', 'catalog_entries': len(entries), 'runtime_messages': manifest['unique_messages'],
        'message_context_counts': manifest['message_context_counts'],
        'guide_display_fields': 203, 'required_japanese_codepoints': len(needed), 'missing_font_codepoints': missing,
        'install_restore_roundtrip': 'passed; original PCK restored byte for byte in disposable directory',
        'release_exe_without_python_uv_on_path': 'passed',
        'standalone_exe_without_external_patch_files': 'passed',
        'japanese_package_path_and_different_working_directory': 'passed',
        'unsupported_build_install_rejection': 'passed',
        'automatic_restore_and_reinstall': 'passed',
        'tampered_pck_reinstall_rejection': 'passed', 'updated_exe_reinstall_rejection': 'passed',
        'tampered_pck_restore_rejection': 'passed',
        'updated_exe_restore_rejection': 'passed', 'unchanged_original_resource_entries': unchanged_count,
        'changed_resource_hashes': 'all verified', 'installed_game_modified': False,
        'release_exe_sha256': sha256(args.exe.read_bytes())
    }
    save(ROOT / 'evidence/patch-validation.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
