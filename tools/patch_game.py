"""Install or remove the locally generated Japanese patch, with strict build checks."""
import argparse
import json
import os
from pathlib import Path
import subprocess

import bsdiff4
from pck import Pack, sha256


def game_not_running():
    if os.name == 'nt':
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq volleyball.exe', '/FO', 'CSV', '/NH'],
                                capture_output=True, creationflags=0x08000000)
        if b'volleyball.exe' in result.stdout.lower():
            raise ValueError('Close Just Volleyball before installing or restoring the patch')


def prepare(game, package):
    manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
    original = (game / 'volleyball.pck').read_bytes()
    exe = (game / 'volleyball.exe').read_bytes()
    if sha256(original) != manifest['original_pck_sha256'] or sha256(exe) != manifest['original_exe_sha256']:
        raise ValueError('Unsupported game build. No files were changed. Rebuild for the new version.')
    key = exe[manifest['key_offset']:manifest['key_offset'] + 32]
    pack = Pack(original, key)
    replacements = {}
    for item in manifest['files']:
        payload_path = (package / item['payload']).resolve()
        if not payload_path.is_relative_to(package.resolve()):
            raise ValueError('Payload path escapes package directory')
        payload = payload_path.read_bytes()
        if sha256(payload) != item['payload_sha256']:
            raise ValueError(f'Corrupt patch payload: {item["path"]}')
        if item['mode'] == 'bsdiff':
            source = pack.read(item['path'])
            if sha256(source) != item['source_sha256']:
                raise ValueError(f'Unexpected original resource: {item["path"]}')
            contents = bsdiff4.patch(source, payload)
        elif item['mode'] == 'add' and item['path'] not in pack.entries:
            contents = payload
        else:
            raise ValueError('Unsupported patch operation')
        if sha256(contents) != item['result_sha256']:
            raise ValueError(f'Patched resource checksum mismatch: {item["path"]}')
        replacements[item['path']] = contents
    return manifest, pack, replacements


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir', type=Path, required=True)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output', type=Path, help='Generate a patched PCK without installing it')
    group.add_argument('--install', action='store_true')
    group.add_argument('--restore', action='store_true')
    args = parser.parse_args(argv)
    game = args.game_dir.resolve()
    live = game / 'volleyball.pck'
    backup = game / 'volleyball.pck.ja-backup'
    receipt = game / 'volleyball-ja-receipt.json'
    if args.restore:
        game_not_running()
        state = json.loads(receipt.read_text(encoding='utf-8'))
        if (sha256(live.read_bytes()) != state['patched_sha256']
                or sha256(backup.read_bytes()) != state['original_sha256']
                or sha256((game / 'volleyball.exe').read_bytes()) != state['exe_sha256']):
            raise ValueError('Game was updated or changed; refusing to restore an old build')
        os.replace(backup, live)
        receipt.unlink()
        print('Original PCK restored.')
        return
    if args.install:
        game_not_running()
        if backup.exists() or receipt.exists():
            raise ValueError('Backup/receipt already exists. Restore before applying a new patch.')
    manifest, pack, replacements = prepare(game, args.package)
    output = args.output.resolve() if args.output else game / 'volleyball.pck.ja-tmp'
    if output in {live, backup} or output.exists():
        raise ValueError('Output must be a new file, separate from the game and backup')
    output.parent.mkdir(parents=True, exist_ok=True)
    pack.write_patched(output, replacements)
    check = Pack(output.read_bytes(), pack.key)
    for path, expected in replacements.items():
        if check.read(path) != expected:
            raise ValueError(f'Written resource verification failed: {path}')
    if args.install:
        state = {'original_sha256': manifest['original_pck_sha256'], 'exe_sha256': manifest['original_exe_sha256'],
                 'patched_sha256': sha256(output.read_bytes())}
        # A receipt is written first; a failed swap rolls back and removes it.
        receipt.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
        try:
            os.replace(live, backup)
            try:
                os.replace(output, live)
            except BaseException:
                os.replace(backup, live)
                raise
        except BaseException:
            receipt.unlink(missing_ok=True)
            raise
        print('Japanese patch installed. Original PCK kept as volleyball.pck.ja-backup.')
    else:
        print(f'Generated and verified: {output}')


if __name__ == '__main__':
    main()
