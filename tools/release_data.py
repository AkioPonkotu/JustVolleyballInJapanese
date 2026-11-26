"""Validate distributable patch payloads without requiring the original game."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PATCH_DATA = ROOT / 'packaging/patch-data'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verified_payloads(package):
    manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
    files = []
    for item in manifest['files']:
        path = (package / item['payload']).resolve()
        if not path.is_relative_to((package / 'payload').resolve()):
            raise ValueError('Payload path escapes payload directory')
        if digest(path) != item['payload_sha256']:
            raise ValueError(f'Corrupt patch payload: {item["path"]}')
        files.append(path)
    if not files:
        raise ValueError('Patch contains no payloads')
    return files


def source_hashes():
    files = [ROOT / 'tools/build_patch.py', ROOT / 'tools/catalog.py']
    for pattern in ('mod/*.gd', 'translations/ja/*.json', 'assets/fonts/*.ttf'):
        files.extend(ROOT.glob(pattern))
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(
        path.read_bytes() if path.suffix == '.ttf' else path.read_text(encoding='utf-8').encode('utf-8')
    ).hexdigest() for path in sorted(files)}


def verify_snapshot(package=PATCH_DATA):
    verified_payloads(package)
    inputs = json.loads((package / 'inputs.json').read_text(encoding='utf-8'))
    if inputs != source_hashes():
        raise ValueError('Patch data is stale. Run tools/build_patch.py with the original game, '
                         'then commit packaging/patch-data together with the translation/MOD changes.')


def export_snapshot(package):
    files = verified_payloads(package)
    PATCH_DATA.mkdir(parents=True, exist_ok=True)
    for path in [package / 'manifest.json', package / 'OFL.txt', package / 'FONT-NOTICE.txt', *files]:
        target = PATCH_DATA / path.relative_to(package)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    (PATCH_DATA / 'inputs.json').write_text(
        json.dumps(source_hashes(), indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    verify_snapshot()
    print('Patch payload hashes and source inputs verified.')
