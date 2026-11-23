#!/usr/bin/env python3
"""SMuFL-Glyphs4 data -> organized FontLab 8/9 .enc menus, add-only.

Source: github.com/Shinianqi/SMuFL-Glyphs4 (Apache-2.0)
Only the data files are downloaded; no third-party code is executed.
Requires Python 3.9+. NEVER modifies, removes, renames, or backs up existing files.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

BASE = 'https://raw.githubusercontent.com/Shinianqi/SMuFL-Glyphs4/main/'
INPUTS = {
    'glyphnames': 'data/upstream/glyphnames.json',
    'classes': 'data/upstream/classes.json',
    'ranges': 'data/upstream/ranges.json',
    'layout': 'data/layout/legacy.json',
}
FILE_PREFIX = 'SMuFL-Organized-v2-'
CODEPOINT_RE = re.compile(r'U\+[0-9A-Fa-f]{4,6}\Z')
MAX_DOWNLOAD = 3_000_000

# Each label in FontLab has ONE real parent (its %%GROUP: header).
# Using functional groups instead of duplicating the source's A-Z indexes.
GROUP_ORDER = [
    'SMuFL Quick',
    'SMuFL Common',
    'SMuFL Staff & Clefs',
    'SMuFL Notes & Rests',
    'SMuFL Rhythm & Time',
    'SMuFL Accidentals',
    'SMuFL Microtonal',
    'SMuFL World Music',
    'SMuFL Articulation',
    'SMuFL Dynamics',
    'SMuFL Ornaments',
    'SMuFL Techniques',
    'SMuFL Percussion',
    'SMuFL Instruments',
    'SMuFL Chords',
    'SMuFL Theory',
    'SMuFL Medieval',
    'SMuFL Tablature',
    'SMuFL Special Notation',
    'SMuFL Text & Signs',
    'SMuFL Graphics',
    'SMuFL Supplements',
    'SMuFL Miscellaneous',
]

# Source language section name -> functional FontLab group.
LANGUAGE_SECTION_GROUPS = {
    'Staff Structure': 'SMuFL Staff & Clefs',
    'Clefs & Octaves': 'SMuFL Staff & Clefs',
    'Notes & Rests': 'SMuFL Notes & Rests',
    'Accidentals': 'SMuFL Accidentals',
    'Time Signatures': 'SMuFL Rhythm & Time',
    'Articulations': 'SMuFL Articulation',
    'Repetitions': 'SMuFL Rhythm & Time',
    'Ornaments': 'SMuFL Ornaments',
    'Techniques': 'SMuFL Techniques',
    'Pictograms': 'SMuFL Percussion',
    'Symbols for Specific Instruments': 'SMuFL Instruments',
    'Chord Symbols': 'SMuFL Chords',
    'Analytics': 'SMuFL Theory',
    'Medieval & Renaissance Notations': 'SMuFL Medieval',
    'Special Notations': 'SMuFL Special Notation',
    'Graphics': 'SMuFL Graphics',
    'Lute & Organ Tablatures': 'SMuFL Tablature',
    'Texts & Signs': 'SMuFL Text & Signs',
    'Controllers': 'SMuFL Staff & Clefs',
    'All Supplements': 'SMuFL Supplements',
}


def download_json(relative):
    req = urllib.request.Request(BASE + relative, headers={
        'User-Agent': 'SMuFL-Organized-FontLab-AddOnly/2.0',
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=40) as response:
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise ValueError('Download too large: ' + relative)
    return json.loads(data.decode('utf-8-sig'))


def load_sources(source_dir=None):
    data = {}
    for name, path in INPUTS.items():
        if source_dir:
            data[name] = json.loads((Path(source_dir).expanduser() / path).read_text(encoding='utf-8-sig'))
        else:
            data[name] = download_json(path)
    return data


def validate_sources(source, test_mode=False):
    glyphs = source['glyphnames']
    classes = source['classes']
    ranges = source['ranges']
    layout = source['layout']
    if not all(isinstance(v, dict) for v in (glyphs, classes, ranges, layout)):
        raise ValueError('Unexpected JSON structure')
    if not test_mode and (not 2800 <= len(glyphs) <= 3200 or
                          not 80 <= len(classes) <= 110 or
                          not 125 <= len(ranges) <= 155):
        raise ValueError('Unexpected source size. Refusing to install.')
    if not isinstance(layout.get('categories'), list) or not isinstance(layout.get('languages'), list):
        raise ValueError('Missing Glyphs4 layout categories/languages')
    categories = {x.get('name'): x for x in layout['categories'] if isinstance(x, dict)}
    if 'SMuFL Common Glyphs' not in categories or 'SMuFL Glyphs' not in categories:
        raise ValueError('Not the expected official layout')
    codepoints = {}
    for name, obj in glyphs.items():
        if not isinstance(name, str) or not isinstance(obj, dict):
            raise ValueError('Invalid glyph metadata')
        code = obj.get('codepoint')
        if not isinstance(code, str) or not CODEPOINT_RE.fullmatch(code):
            raise ValueError('Invalid glyph codepoint: ' + name)
        cp = int(code[2:], 16)
        if cp > 0x10FFFF or 0xD800 <= cp <= 0xDFFF:
            raise ValueError('Invalid Unicode scalar value')
        codepoints[name] = cp
    for name, members in classes.items():
        if not isinstance(name, str) or not isinstance(members, list):
            raise ValueError('Invalid class')
    for name, obj in ranges.items():
        if not isinstance(name, str) or not isinstance(obj, dict) or not isinstance(obj.get('glyphs'), list):
            raise ValueError('Invalid range')
    return codepoints


def fontlab_name(cp):
    return f'uni{cp:04X}' if cp <= 0xFFFF else f'u{cp:05X}'


def clean(s):
    return re.sub(r'\s+', ' ', str(s).replace('\u200b', '')).strip()


def extract_leaf_sections(node, source_type=None):
    for child in node.get('children', []):
        if 'class' in child:
            yield 'class', child['class'], clean(child['name'])
        elif 'range' in child:
            yield 'range', child['range'], clean(child['name'])
        elif 'list' in child:
            yield 'list', child['name'], clean(child['name'])
        else:
            yield from extract_leaf_sections(child)


def language_homes(layout):
    """One preferred parent per original source reference (except special overrides)."""
    homes = {}
    for language in layout['languages']:
        for section in language.get('children', []):
            parent = LANGUAGE_SECTION_GROUPS.get(clean(section['name']))
            if not parent:
                continue
            for kind, key, _ in extract_leaf_sections(section):
                if kind != 'list':
                    homes.setdefault((kind, key), parent)
    return homes


def choose_group(kind, key, name, homes):
    """Explicit semantic priority avoids accidental catch-all classifications."""
    k = (key + ' ' + name).lower()
    if 'supplement' in k:
        return 'SMuFL Supplements'
    if key.startswith('tf_'):
        return 'SMuFL Chords' if 'chord' in k else 'SMuFL Text & Signs'
    if 'tablature' in k or 'organGerman' in key:
        return 'SMuFL Tablature'
    if 'medieval' in k or 'renaissance' in k or 'plainchant' in k or 'prolation' in k:
        return 'SMuFL Medieval'
    if any(x in k for x in ('daseian', 'kievan', 'kodály', 'kodaly', 'kahnotation', 'simplified music')):
        return 'SMuFL Special Notation'
    if any(x in k for x in ('sagittal', 'helmholtz', 'wyschnegradsky', 'johnston', '72-edo', '72edo', 'sims accidentals', 'steIn zimmermann'.lower())):
        return 'SMuFL Microtonal'
    if ('accidental' in k and any(x in k for x in ('arabic', 'persian', 'turkish', 'arel', 'a-e-u', 'aeu'))):
        return 'SMuFL World Music'
    if 'accidental' in k:
        return 'SMuFL Accidentals'
    if any(x in k for x in ('pictogram', 'percussion', 'beater', 'gong', 'cymbal', 'drum', 'shaker', 'rattle', 'chime')):
        if 'electronic' in k:
            return 'SMuFL Special Notation'
        return 'SMuFL Percussion'
    if any(x in k for x in ('technique', 'bowing', 'chop notation', 'wind technique', 'string technique')):
        return 'SMuFL Techniques'
    if any(x in k for x in ('chord symbol', 'chord diagram')):
        return 'SMuFL Chords'
    if any(x in k for x in ('figured bass', 'function theory', 'scale degree', 'analytics')):
        return 'SMuFL Theory' if ('function theory' in k or 'scale degree' in k or 'analytics' in k) else 'SMuFL Text & Signs'
    if any(x in k for x in ('ornament', 'wiggle', 'trill', 'mordent', 'arpeggiato', 'vibrato')):
        return 'SMuFL Ornaments'
    if any(x in k for x in ('notehead', 'note head', 'note cluster', 'individual note', 'beamed group', 'stem decoration', 'stems', 'rests', 'flags')):
        return 'SMuFL Notes & Rests'
    if any(x in k for x in ('articulation', 'pause', 'hold', 'fermata')):
        return 'SMuFL Articulation'
    if any(x in k for x in ('time signature', 'tuplet', 'tremolo', 'repeat', 'rhythm')):
        return 'SMuFL Rhythm & Time'
    if any(x in k for x in ('dynamics', 'dynamic', 'hairpin')):
        return 'SMuFL Dynamics'
    if any(x in k for x in ('clef', 'octave', 'barline', 'staves', 'staff ', 'staffbracket', 'staffdivider', 'beam', 'slur')):
        return 'SMuFL Staff & Clefs'
    if any(x in k for x in ('guitar', 'accordion', 'handbell', 'harp pedal', 'organ pedal')):
        return 'SMuFL Instruments'
    if any(x in k for x in ('arrow', 'multi-segment', 'graphic')):
        return 'SMuFL Graphics'
    if any(x in k for x in ('fingering', 'metronome', 'text ', 'lyric', 'symbol', 'conductor')) or key.startswith('tf_'):
        return 'SMuFL Text & Signs'
    return homes.get((kind, key), 'SMuFL Miscellaneous')


def short_title(group, title):
    """Remove words that are already in the parent title, not meaningful qualifiers."""
    title = clean(title).replace('Text · ', '')
    if group == 'SMuFL Medieval':
        title = re.sub(r'^Medieval (?:&|and) Renaissance\s*', '', title, flags=re.I)
    if group == 'SMuFL Tablature':
        title = re.sub(r'\s+Tablature$', '', title, flags=re.I)
    if group == 'SMuFL Accidentals':
        title = re.sub(r'^Accidentals\s+', '', title, flags=re.I)
    if group == 'SMuFL Microtonal':
        title = re.sub(r'^Accidentals\s+', '', title, flags=re.I)
    if group == 'SMuFL World Music':
        title = re.sub(r'\s+Accidentals$', '', title, flags=re.I)
    if group == 'SMuFL Ornaments':
        title = re.sub(r'^Wiggles\s+', '', title, flags=re.I)
    if group == 'SMuFL Percussion':
        title = re.sub(r'\s+Pictograms$', '', title, flags=re.I)
    if group == 'SMuFL Techniques':
        title = re.sub(r'\s+Techniques$', '', title, flags=re.I)
    if group == 'SMuFL Supplements':
        title = re.sub(r'\s+Supplement$', '', title, flags=re.I) + ' (supp.)'
    return title


def make_catalog(data, codepoints):
    classes, ranges, layout = data['classes'], data['ranges'], data['layout']
    categories = {entry['name']: entry for entry in layout['categories']}
    language = next((x for x in layout['languages'] if x.get('name') == 'SMuFL'), None)
    if language is None:
        raise ValueError('SMuFL language layout is missing')
    homes = language_homes(layout)
    indexed = categories['SMuFL Glyphs']['children']
    class_index = next(x for x in indexed if x['name'] == 'Classes A-Z')
    range_index = next(x for x in indexed if x['name'] == 'Ranges A-Z')
    # Sorted by actual Unicode point, exactly as in source, not canonical name.
    def sorted_known(names):
        return sorted(set(n for n in names if n in codepoints), key=lambda n: (codepoints[n], n))

    def resolve(node):
        if 'range' in node:
            key = node['range']
            if key not in ranges:
                raise ValueError('Unknown range: ' + key)
            return sorted_known(ranges[key]['glyphs'])
        if 'class' in node:
            key = node['class']
            if key not in classes:
                raise ValueError('Unknown class: ' + key)
            return sorted_known(classes[key])
        if 'list' in node:
            return sorted_known(node['list'])
        return sorted_known(n for ch in node.get('children', []) for n in resolve(ch))

    def find_named(node, name):
        matches = [node] if clean(node.get('name')) == name else []
        for child in node.get('children', []):
            matches += find_named(child, name)
        return matches

    def named_leaves(node, name):
        matching = []
        for child in node.get('children', []):
            if clean(child.get('name')) == name and 'children' not in child:
                matching += resolve(child)
            matching += named_leaves(child, name)
        return matching

    entries = []
    seen_signatures = {}  # only in detailed catalog (not Quick/Common)
    seen_labels = set()
    aliases = []
    missing = []
    def add(group, label, names, origin, detail=False):
        names = sorted_known(names)
        if not names:
            missing.append((group, label, origin))
            return
        glyph_names = tuple(dict.fromkeys(fontlab_name(codepoints[n]) for n in names))
        if detail and glyph_names in seen_signatures:
            aliases.append((origin, seen_signatures[glyph_names]))
            return
        base = short_title(group, label) if detail else clean(label)
        if not base:
            raise ValueError('Empty encoding title')
        title = base
        i = 2
        while (group.casefold(), title.casefold()) in seen_labels:
            suffix = 'range' if origin.startswith('range:') else 'class' if origin.startswith('class:') else 'variant'
            title = f'{base} ({suffix})' if i == 2 else f'{base} ({suffix} {i})'
            i += 1
        seen_labels.add((group.casefold(), title.casefold()))
        entries.append((group, title, glyph_names, origin))
        if detail:
            seen_signatures[glyph_names] = group + ' / ' + title

    # Source's five precreate entries: preserve counts and meanings.
    for preset in language.get('precreate', []):
        origin = preset.get('from', '')
        if origin == 'all':
            names = sorted_known(codepoints.keys())
        elif origin.startswith('category:'):
            names = resolve(categories[origin.split(':', 1)[1]])
        elif origin.startswith('basics:'):
            name = origin.split(':', 1)[1]
            nodes = find_named(categories['SMuFL Common Glyphs'], name)
            if not nodes:
                raise ValueError('Unknown basic preset: ' + name)
            names = resolve(nodes[0])
        elif origin.startswith('name:'):
            name = origin.split(':', 1)[1]
            names = []
            for node in layout['categories'] + language.get('children', []):
                names += named_leaves(node, name)
        else:
            raise ValueError('Unexpected preset: ' + origin)
        preset_name = clean(preset['name'])
        if preset_name == 'SMuFL Glyphs':
            preset_name = 'All glyphs'
        if preset_name == 'SMuFL Common Glyphs':
            preset_name = 'Common glyphs'
        add('SMuFL Quick', preset_name, names, 'preset:' + origin)

    # The 12 ergonomic Common headings are the ONLY topical overviews.
    for category in categories['SMuFL Common Glyphs'].get('children', []):
        add('SMuFL Common', clean(category['name']), resolve(category), 'common:' + category['name'])

    # Each source range is used once, grouped by semantics and taxonomy.
    for kind, index, lookup in (('range', range_index, ranges), ('class', class_index, classes)):
        used_keys = set()
        for key_kind, key, label in extract_leaf_sections(index):
            if key_kind != kind or key in used_keys:
                continue
            used_keys.add(key)
            if key not in lookup:
                raise ValueError('Index refers to missing ' + kind + ': ' + key)
            group = choose_group(kind, key, label, homes)
            members = lookup[key]['glyphs'] if kind == 'range' else lookup[key]
            add(group, label, members, kind + ':' + key, detail=True)
        if used_keys != set(lookup):
            missing_keys = set(lookup) - used_keys
            # Source metadata may include additional keys not present in A-Z layout:
            # retain ALL of them, giving readable deterministic titles.
            for key in sorted(missing_keys):
                group = choose_group(kind, key, key, homes)
                label = re.sub(r'(?<!^)(?=[A-Z])', ' ', key).title()
                members = lookup[key]['glyphs'] if kind == 'range' else lookup[key]
                add(group, label, members, kind + ':' + key, detail=True)

    # Don't ever silently lose entries. Store full catalog for reporting only.
    entries.sort(key=lambda x: (GROUP_ORDER.index(x[0]) if x[0] in GROUP_ORDER else len(GROUP_ORDER), x[1].casefold()))
    return entries, aliases, missing


def file_content(group, title, names):
    return ('%%FONTLAB ENCODING: -1; ' + title + '\n' +
            '%%GROUP:' + group + '\n' + '\n'.join(names) + '\n').encode('utf-8')


def filename(group, title):
    g = re.sub('[^A-Za-z0-9]+', '-', group.removeprefix('SMuFL').strip()).strip('-') or 'Quick'
    t = re.sub('[^A-Za-z0-9]+', '-', title).strip('-')[:45] or 'List'
    digest = hashlib.sha256((group + '\0' + title).encode()).hexdigest()[:10]
    return f'{FILE_PREFIX}{g}-{t}-{digest}.enc'


def encoding_files(catalog):
    files = {}
    for group, title, names, origin in catalog:
        path = filename(group, title)
        if path in files:
            raise ValueError('New filenames conflict: ' + path)
        files[path] = file_content(group, title, names)
    return files


def targets():
    base = Path.home() / 'Library' / 'Application Support' / 'FontLab'
    return [('FontLab 8', base / 'FontLab 8' / 'Encoding'),
            ('FontLab 9', base / 'FontLab 9' / 'Encoding')]


def verify_directory(folder):
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError('Missing or symlinked Encoding folder: ' + str(folder))
    if any(parent.is_symlink() for parent in folder.parents):
        raise ValueError('Symlink in Encoding folder path: ' + str(folder))


def install(files, dirs, preview):
    # Validate BOTH before writing even a single file.
    for _, folder in dirs:
        verify_directory(folder)
    for label, folder in dirs:
        casefolded = {x.name.casefold() for x in folder.iterdir()}
        added = skipped = 0
        for name, content in files.items():
            if name.casefold() in casefolded:
                skipped += 1
                continue
            if preview:
                added += 1
                continue
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, 'O_NOFOLLOW'):
                flags |= os.O_NOFOLLOW
            try:
                fd = os.open(folder / name, flags, 0o644)
            except FileExistsError:
                skipped += 1
                continue
            with os.fdopen(fd, 'wb') as output:
                output.write(content)
            added += 1
            casefolded.add(name.casefold())
        status = 'would add' if preview else 'added'
        print(f'  {label}: {added} {status}; {skipped} existing files skipped')
        print('    ' + str(folder))


def main():
    parser = argparse.ArgumentParser(description='SMuFL organized add-only encodings for FontLab 8 and 9')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--preview', action='store_true')
    group.add_argument('--add', action='store_true')
    parser.add_argument('--source-dir', help='Offline source repository root (for debugging)')
    parser.add_argument('--target-root', help=argparse.SUPPRESS)  # fixture tests only
    parser.add_argument('--test-source', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    print('Reading official SMuFL-Glyphs4 source definitions...')
    data = load_sources(args.source_dir)
    cp = validate_sources(data, test_mode=args.test_source)
    catalog, aliases, missing = make_catalog(data, cp)
    files = encoding_files(catalog)
    print(f'Source: {len(cp)} glyphs, {len(data["classes"])} classes, {len(data["ranges"])} ranges')
    print(f'Organized menu: {len(files)} entries across {len(set(x[0] for x in catalog))} sections')
    for name in GROUP_ORDER:
        subset = [x for x in catalog if x[0] == name]
        if subset:
            sample = ', '.join(x[1] for x in subset[:4])
            print(f'  {name}: {len(subset)} lists | {sample}')
    print(f'Identical detail lists consolidated: {len(aliases)}')
    if missing:
        print(f'WARNING: {len(missing)} empty data sets skipped')
    if not files or len(files) < 15:
        raise ValueError('Too few encodings generated, no files installed')
    dirs = targets()
    if args.target_root:
        root = Path(args.target_root)
        dirs = [('FontLab 8 (test)', root / 'FontLab 8' / 'Encoding'),
                ('FontLab 9 (test)', root / 'FontLab 9' / 'Encoding')]
    install(files, dirs, args.preview)
    if args.preview:
        print('PREVIEW: no files changed or added.')
    else:
        print('ADD COMPLETE: existing files untouched; no backups or deletions.')

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'ERROR ({type(exc).__name__}): {exc}', file=sys.stderr)
        print('No old files are intentionally modified or deleted. Copy the error above for diagnosis.', file=sys.stderr)
        sys.exit(1)
