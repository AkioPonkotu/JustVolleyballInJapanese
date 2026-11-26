"""Index recovered text and font coverage without executing game scripts.

Run with: uv run --with fonttools==4.69.1 python tools/analyze_localization.py
Full extracted strings stay in the ignored work directory.
"""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from fontTools.ttLib import TTFont


TOKEN = re.compile(
    r'\#[^\n]*|"""(?:.|\n)*?"""|\x27\x27\x27(?:.|\n)*?\x27\x27\x27'
    r'|"(?:\\.|[^"\\])*"|\x27(?:\\.|[^\x27\\])*\x27'
)
DISPLAY = re.compile(
    r'\b(?:text|tooltip_text|placeholder_text|title|dialog_text)\s*='
    r'|\b(?:_tab|_label|_button|_heading|_para|_type|_toggle|_slider|_section|_choice|add_item|add_message)\s*\('
)
MARKERS = re.compile(
    r'TranslationServer|\btr\s*\(|\btr_n\s*\(|auto_translate_mode|'
    r'\bdraw_(?:multiline_)?string\s*\(|\bfallbacks\b|\ballow_system_fallback\b'
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('work/recovered'))
    parser.add_argument('--raw', type=Path, default=Path('work/raw'))
    parser.add_argument('--output', type=Path, default=Path('work/analysis'))
    args = parser.parse_args()
    if not (args.root / 'project.godot').exists():
        parser.error('Recovery must finish first (project.godot missing).')

    strings, references, markers = [], [], []
    counts = Counter()
    for path in sorted(args.root.rglob('*')):
        if not path.is_file() or '.godot' in path.relative_to(args.root).parts:
            continue
        counts[path.suffix.lower()] += 1
        if path.suffix.lower() not in {'.gd', '.tscn', '.tres', '.godot', '.json'}:
            continue
        text = path.read_text(encoding='utf-8-sig', errors='replace')
        rel = path.relative_to(args.root).as_posix()
        lines = text.splitlines()
        for match in TOKEN.finditer(text):
            literal = match.group()
            if literal.startswith('#'):
                continue
            line = text.count('\n', 0, match.start()) + 1
            try:
                value = ast.literal_eval(literal)
            except (ValueError, SyntaxError):
                value = literal[1:-1]
            if not isinstance(value, str) or not value:
                continue
            if re.search(r'\.(?:ttf|otf)(?:$|\")', value, re.I):
                references.append({'path': rel, 'line': line, 'font': value})
            if not re.search('[A-Za-z]', value):
                continue
            context = lines[line - 1].strip()
            excluded = bool(re.match(r'(?:res|user|uid)://|https?://', value))
            reason = None
            if not excluded and DISPLAY.search(context):
                reason = 'display_assignment_or_helper_candidate'
            elif not excluded and re.search(r'[A-Za-z]+\s+[A-Za-z]+', value):
                reason = 'phrase_candidate'
            strings.append({'path': rel, 'line': line, 'text': value,
                            'candidate_reason': reason, 'context': context})
        for index, line_text in enumerate(lines, 1):
            if not line_text.lstrip().startswith('#') and MARKERS.search(line_text):
                markers.append({'path': rel, 'line': index, 'context': line_text.strip()})

    fonts = []
    for path in sorted(args.root.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in {'.ttf', '.otf'}:
            continue
        with TTFont(path) as font:
            cmap = font.getBestCmap() or {}
            def family_name(name_id):
                for record in font['name'].names:
                    if record.nameID == name_id:
                        return record.toUnicode()
                return None
            fonts.append({
                'path': path.relative_to(args.root).as_posix(),
                'family': family_name(1), 'subfamily': family_name(2),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'mapped_codepoints': len(cmap),
                'hiragana_codepoints': sum(0x3040 <= cp <= 0x309f for cp in cmap),
                'katakana_codepoints': sum(0x30a0 <= cp <= 0x30ff for cp in cmap),
                'cjk_unified_codepoints': sum(0x4e00 <= cp <= 0x9fff for cp in cmap),
                'sample_glyphs': {char: ord(char) in cmap for char in '日本語設定あいうアイウABC123'},
            })

    candidates = [entry for entry in strings if entry['candidate_reason']]
    by_file = Counter(entry['path'] for entry in candidates)
    raw_files = [p for p in args.raw.rglob('*') if p.is_file()]
    resource_map = []
    for path in raw_files:
        if path.suffix not in {'.remap', '.import'}:
            continue
        remap = re.search(r'^path="([^"]+)"', path.read_text(encoding='utf-8', errors='replace'), re.M)
        if remap:
            resource_map.append({'source': 'res://' + path.relative_to(args.raw).as_posix().rsplit('.', 1)[0],
                                 'packed_path': remap[1]})

    guide_entries = []
    guide_path = args.root / 'game/ui/how_to_text.json'
    guide = json.loads(guide_path.read_text(encoding='utf-8'))
    def walk_guide(value, pointer='', field=None):
        if isinstance(value, dict):
            for key, item in value.items():
                walk_guide(item, pointer + '/' + key.replace('~', '~0').replace('/', '~1'), key)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk_guide(item, pointer + '/' + str(index), field)
        elif isinstance(value, str) and value and field in {'name', 'title', 'body', 'table'}:
            guide_entries.append({'pointer': pointer, 'text': value, 'field': field})
    walk_guide(guide)
    summary = {
        'method': 'Static quoted-string inventory; candidates need manual review and are not a final translation count.',
        'raw_file_count': len(raw_files),
        'recovered_file_extensions': dict(sorted(counts.items())),
        'english_literal_occurrences': len(strings),
        'candidate_occurrences': len(candidates),
        'candidate_unique_strings': len({entry['text'] for entry in candidates}),
        'candidate_files': len(by_file),
        'top_candidate_files': [{'path': path, 'occurrences': count} for path, count in by_file.most_common(25)],
        'raw_translation_files': [p.relative_to(args.raw).as_posix() for p in raw_files
                                  if p.suffix.lower() in {'.csv', '.po', '.mo', '.translation'}],
        'fonts': fonts,
        'font_reference_count': len(references),
        'guide': {'path': 'game/ui/how_to_text.json', 'categories': len(guide['categories']),
                  'sections': sum(len(group['sections']) for category in guide['categories'] for group in category['groups']),
                  'display_string_occurrences': len(guide_entries)},
    }
    for name, value in [('all-english-literals.json', strings), ('text-candidates.json', candidates),
                        ('font-references.json', references), ('localization-markers.json', markers),
                        ('resource-map.json', resource_map), ('how-to-display-strings.json', guide_entries),
                        ('summary.json', summary)]:
        write_json(args.output / name, value)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
