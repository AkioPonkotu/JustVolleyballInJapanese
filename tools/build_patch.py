"""Build a distributable patch from human-edited catalogs and locally recovered data."""
import argparse
import ast
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

import bsdiff4
from catalog import ROOT, TOKENS, load_catalogs, save
from pck import Pack, sha256

TOKEN = re.compile(r'\#[^\n]*|"""(?:.|\n)*?"""|\x27\x27\x27(?:.|\n)*?\x27\x27\x27|"(?:\\.|[^"\\])*"|\x27(?:\\.|[^\x27\\])*\x27')


def json_pointer(root, pointer):
    node = root
    parts = pointer.split('/')[1:]
    for part in parts[:-1]:
        part = part.replace('~1', '/').replace('~0', '~')
        node = node[int(part)] if isinstance(node, list) else node[part]
    key = parts[-1].replace('~1', '/').replace('~0', '~')
    return node, int(key) if isinstance(node, list) else key


def inject(text, signature, statement):
    matches = list(re.finditer(signature, text, re.M))
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one injection point: {signature}')
    point = matches[0].end()
    return text[:point] + '\n\t' + statement + '\n' + text[point:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir', type=Path, default=Path('F:/SteamLibrary/steamapps/common/just volleyball'))
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/just-volleyball-ja')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'dist'):
        raise ValueError('Build output must be inside the repository dist directory')
    output.mkdir(parents=True, exist_ok=True)
    messages, entries = load_catalogs()
    baseline = json.loads((ROOT / 'evidence/installed-build.json').read_text(encoding='utf-8-sig'))
    hashes = {item['name']: item['sha256'].lower() for item in baseline['files']}
    original = (args.game_dir / 'volleyball.pck').read_bytes()
    exe = (args.game_dir / 'volleyball.exe').read_bytes()
    if sha256(original) != hashes['volleyball.pck'] or sha256(exe) != hashes['volleyball.exe']:
        raise ValueError('Game build differs from the analyzed build; refusing to build')
    pack = Pack(original, exe[81005808:81005840])
    recovered = ROOT / 'work/recovered'
    staging = ROOT / 'work/build/scripts'
    staging.mkdir(parents=True, exist_ok=True)
    changed = {}
    bindings = []
    # Format strings must be localized before interpolation, while UI translation
    # handles ordinary strings without modifying IDs, comparisons or user input.
    for path in sorted((recovered / 'game').rglob('*.gd')):
        text = path.read_text(encoding='utf-8')
        rel = path.relative_to(recovered).as_posix()
        def replace(match):
            literal = match.group()
            if literal.startswith('#'):
                return literal
            try:
                source = ast.literal_eval(literal)
            except (ValueError, SyntaxError):
                return literal
            if source not in messages or not re.search(r'%(?:[-+ #0]*\d*(?:\.\d+)?)[sdifuxXocgeEFG]', source):
                return literal
            bindings.append({'path': rel, 'line': text.count('\n', 0, match.start()) + 1,
                             'source': source, 'kind': 'format-before-interpolation'})
            return json.dumps(messages[source], ensure_ascii=False)
        patched = TOKEN.sub(replace, text)
        if rel == 'game/ui/boot/gpu_notice.gd':
            source = "if a launch command doesn't help, try updating (or rolling back) your graphics drivers:\n"
            def prefix(match):
                if match.group().startswith('#'):
                    return match.group()
                try:
                    value = ast.literal_eval(match.group())
                except (ValueError, SyntaxError):
                    return match.group()
                return json.dumps(messages[source], ensure_ascii=False) if value == source else match.group()
            patched = TOKEN.sub(prefix, patched)
        if rel == 'game/core/game_config.gd':
            anchor = 'TranslationServer.set_locale("en")'
            if patched.count(anchor) != 1:
                raise ValueError('English locale initialization changed')
            patched = patched.replace(anchor, 'load("res://jvja/bootstrap.gd").install()')
        if rel == 'game/guide/guide_tokens.gd':
            patched = inject(patched, r'^static func fill\([^\n]+\n?', 'if r.can_auto_translate():\n\t\ttext = TranslationServer.translate(text)')
        if rel == 'game/ui/tutorial_overlay.gd':
            patched = inject(patched, r'^func _fill_rich\([^\n]+\n?', 'text = TranslationServer.translate(text)')
        if rel == 'game/ui/menu.gd':
            for expression, expected in [('OUTFIT_LABELS.get(_outfit, _outfit)', 2),
                                         ('BALL_LABELS.get(_ball_skin, _ball_skin)', 2)]:
                if patched.count(expression) != expected:
                    raise ValueError(f'Menu enum expression changed: {expression}')
                patched = patched.replace(expression, 'tr(String(' + expression + '))')
            stage_line = '\t_stage_btn.text = ' + json.dumps(messages['stage: %s'], ensure_ascii=False) + ' % t'
            if patched.count(stage_line) != 1:
                raise ValueError('Stage label expression changed')
            patched = patched.replace(stage_line, stage_line[:-1] + 'tr(t)')
        if rel == 'game/titles/title_catalog.gd':
            anchor = '\t\t_items.append(item)'
            if patched.count(anchor) != 1:
                raise ValueError('Title catalog insertion point changed')
            patched = patched.replace(anchor, '\t\titem.text = String(TranslationServer.translate(item.text, &"titles"))\n' + anchor)
        if patched != text:
            target = staging / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(patched, encoding='utf-8')
            changed[rel.removesuffix('.gd') + '.gdc'] = target

    compiled_dir = ROOT / 'work/build/compiled'
    compiled_dir.mkdir(parents=True, exist_ok=True)
    if len({path.name for path in changed.values()}) != len(changed):
        raise ValueError('Duplicate script basenames; compile these in separate directories')
    command = [str(ROOT / '.local/gdre/gdre_tools.exe'), '--headless', '--bytecode=4.5.0', '--output=' + str(compiled_dir)]
    command += ['--compile=' + str(path) for path in changed.values()]
    for path in changed.values():
        target = compiled_dir / path.with_suffix('.gdc').name
        target.unlink(missing_ok=True)
    process = subprocess.run(command, capture_output=True, cwd=compiled_dir)
    (ROOT / 'work/build/compile.log').write_bytes(process.stdout + process.stderr)
    if process.returncode != 0:
        raise ValueError('Bytecode compilation failed; inspect work/build/compile.log')
    for path in changed.values():
        if not (compiled_dir / path.with_suffix('.gdc').name).exists():
            raise ValueError(f'No compiled output for {path}')

    guide = json.loads(pack.read('game/ui/how_to_text.json').decode('utf-8'))
    guide_count = 0
    for ident, entry in entries.items():
        if not ident.startswith('howto.'):
            continue
        node, key = json_pointer(guide, entry['context'])
        if node[key] != entry['source']:
            raise ValueError(f'Guide source changed at {entry["context"]}')
        node[key] = entry['ja']
        guide_count += 1
    if guide_count != 203:
        raise ValueError('This build expects every one of the 203 guide display fields')
    replacements = {path: (compiled_dir / source.with_suffix('.gdc').name).read_bytes() for path, source in changed.items()}
    replacements['game/ui/how_to_text.json'] = json.dumps(guide, ensure_ascii=False, indent=1).encode()
    runtime_messages = {'': messages, 'titles': {entry['source']: entry['ja'] for ident, entry in entries.items() if ident.startswith('titles.')}}
    additions = {
        'jvja/bootstrap.gd': (ROOT / 'mod/bootstrap.gd').read_bytes(),
        'jvja/messages.json': json.dumps(runtime_messages, ensure_ascii=False, sort_keys=True).encode(),
        'jvja/JVVolleyballJP-SemiBold.ttf': (ROOT / 'assets/fonts/JVVolleyballJP-SemiBold.ttf').read_bytes(),
        'jvja/JVVolleyballJP-ExtraBold.ttf': (ROOT / 'assets/fonts/JVVolleyballJP-ExtraBold.ttf').read_bytes(),
    }
    manifest = {'schema_version': 1, 'locale': 'ja', 'game_build_id': '26937150',
                'original_pck_sha256': sha256(original), 'original_exe_sha256': sha256(exe),
                'key_offset': 81005808, 'catalog_entries': len(entries), 'unique_messages': sum(len(group) for group in runtime_messages.values()),
                'message_context_counts': {context or 'default': len(group) for context, group in runtime_messages.items()},
                'guide_display_fields': guide_count, 'files': []}
    payload_dir = output / 'payload'
    payload_dir.mkdir(exist_ok=True)
    for path, contents in sorted((replacements | additions).items()):
        item = {'path': path, 'mode': 'add' if path in additions else 'bsdiff', 'result_sha256': sha256(contents)}
        if path in additions:
            payload = contents
        else:
            source = pack.read(path)
            payload = bsdiff4.diff(source, contents)
            if bsdiff4.patch(source, payload) != contents:
                raise ValueError('Binary delta roundtrip failed')
            item['source_sha256'] = sha256(source)
        name = 'payload/' + sha256(path.encode())[:16] + ('.bin' if path in additions else '.bsdiff')
        (output / name).write_bytes(payload)
        item.update(payload=name, payload_sha256=sha256(payload))
        manifest['files'].append(item)
    save(output / 'manifest.json', manifest)
    for name in ['patch_game.py', 'pck.py']:
        shutil.copyfile(ROOT / 'tools' / name, output / name)
    shutil.copyfile(ROOT / 'requirements.txt', output / 'requirements.txt')
    shutil.copyfile(ROOT / 'assets/fonts/OFL.txt', output / 'OFL.txt')
    shutil.copyfile(ROOT / 'assets/fonts/NOTICE.txt', output / 'FONT-NOTICE.txt')
    for name in ['Install.ps1', 'Restore.ps1']:
        shutil.copyfile(ROOT / 'packaging' / name, output / name)
    shutil.copyfile(ROOT / 'docs/patch-user-guide.md', output / 'README.md')
    save(ROOT / 'work/analysis/applied-bindings.json', bindings)
    save(ROOT / 'evidence/patch-build.json', {key: value for key, value in manifest.items() if key != 'key_offset'})
    archive = output.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        # Only include files listed by this build, not stale payloads from old builds.
        include = ['manifest.json', 'patch_game.py', 'pck.py', 'requirements.txt', 'OFL.txt', 'FONT-NOTICE.txt',
                   'Install.ps1', 'Restore.ps1', 'README.md'] + [item['payload'] for item in manifest['files']]
        for name in sorted(include):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, (output / name).read_bytes())
    print(f'Built {archive}: {len(entries)} entries, {len(changed)} scripts, {guide_count} guide fields')


if __name__ == '__main__':
    main()
