"""Maintain stable translation IDs; importing sources never overwrites human edits."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TOKENS = re.compile(r'%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[sdifuxXocgeEFG]|%%|\{[A-Za-z_][A-Za-z_0-9]*(?::[A-Za-z_0-9]+)?\}|\[/?(?:b|i|u|color(?:=[^\]]+)?|url(?:=[^\]]+)?|font(?:=[^\]]+)?|font_size(?:=[^\]]+)?|center|img(?:=[^\]]+)?)\]')


def stable_id(domain, source, context=''):
    return domain + '.' + hashlib.sha256((source + ('\0' + context if context else '')).encode()).hexdigest()[:16]


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_catalog(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key in {path}: {key}')
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_pairs)


def import_seed(domain, seed):
    path = ROOT / 'translations/ja' / (domain + '.json')
    data = read_catalog(path) if path.exists() else {
        'schema_version': 1, 'locale': 'ja', 'domain': domain, 'entries': {}}
    added = 0
    for source, japanese in seed.items():
        ident = stable_id(domain, source)
        if ident in data['entries']:
            if data['entries'][ident]['source'] != source:
                raise ValueError('Translation ID collision')
            continue
        data['entries'][ident] = {'source': source, 'ja': japanese, 'status': 'draft', 'note': ''}
        added += 1
    # Keep existing insertion order: upstream additions do not reorder edited entries.
    save(path, data)
    print(f'{domain}: added {added}, retained {len(data["entries"]) - added} existing entries')


def load_catalogs():
    messages, entries = {}, {}
    for path in sorted((ROOT / 'translations/ja').glob('*.json')):
        data = read_catalog(path)
        if data['schema_version'] != 1 or data['locale'] != 'ja':
            raise ValueError(f'Unsupported catalog: {path}')
        for ident, entry in data['entries'].items():
            source, japanese = entry['source'], entry['ja']
            if ident != stable_id(data['domain'], source, entry.get('context', '')) or ident in entries:
                raise ValueError(f'Changed source/ID or duplicate ID: {ident}')
            if entry['status'] not in {'draft', 'reviewed', 'obsolete'}:
                raise ValueError(f'Invalid status: {ident}')
            if entry['status'] == 'obsolete':
                continue
            if not japanese.strip():
                raise ValueError(f'Empty translation: {ident}')
            if Counter(TOKENS.findall(source)) != Counter(TOKENS.findall(japanese)):
                raise ValueError(f'Placeholders or markup differ: {ident}: {source!r}')
            if [t for t in TOKENS.findall(source) if t.startswith('%')] != [t for t in TOKENS.findall(japanese) if t.startswith('%')]:
                raise ValueError(f'Positional format arguments changed order: {ident}')
            if data['domain'] not in {'howto', 'titles'}:
                if source in messages and messages[source] != japanese:
                    raise ValueError(f'Conflicting translations for shared message: {source!r}')
                messages[source] = japanese
            entries[ident] = entry
    return messages, entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    seed = subs.add_parser('import')
    seed.add_argument('--domain', required=True)
    seed.add_argument('--seed', type=Path, required=True)
    subs.add_parser('validate')
    subs.add_parser('sync')
    args = parser.parse_args()
    if args.command == 'import':
        if not re.fullmatch('[a-z][a-z0-9_-]*', args.domain):
            parser.error('Domain must contain lowercase letters, digits, hyphens or underscores')
        import_seed(args.domain, json.loads(args.seed.read_text(encoding='utf-8')))
    else:
        messages, entries = load_catalogs()
        print(f'Validated {len(entries)} entries / {len(messages)} unique messages')
        if args.command == 'sync':
            inventory = json.loads((ROOT / 'work/analysis/all-english-literals.json').read_text(encoding='utf-8'))
            by_source = {}
            for row in inventory:
                by_source.setdefault(row['text'], []).append({'path': row['path'], 'line': row['line']})
            locations = {}
            for ident, entry in entries.items():
                locations[ident] = ([{'path': 'game/ui/how_to_text.json', 'pointer': entry['context']}]
                                    if ident.startswith('howto.') else by_source.get(entry['source'], []))
                if ident.startswith('titles.'):
                    locations[ident] = [row for row in locations[ident] if row['path'].startswith('game/titles/items/')]
            save(ROOT / 'translations/source-locations.json', locations)
            candidates = json.loads((ROOT / 'work/analysis/text-candidates.json').read_text(encoding='utf-8'))
            pending = [row for row in candidates if row['text'] not in messages
                       and row['path'].startswith(('game/ui/', 'game/drills/', 'game/character/'))
                       and row['path'] != 'game/ui/how_to_text.json']
            save(ROOT / 'work/analysis/untranslated-candidates.json', pending)
            print(f'Refreshed source references; {len(pending)} heuristic candidates need triage. Human translations unchanged.')


if __name__ == '__main__':
    main()
