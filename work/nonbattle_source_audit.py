"""Compare local source HEAD with the identified pre-import pret baseline.

This generates source candidates only; actual released ROM bytes determine
whether a candidate belongs in the port. CRLF differences are normalized.
"""
from pc_env import workspace
from pathlib import Path
import difflib
import json
import subprocess

ROOT = workspace()
BASE = '51bad5a606d7b2e8f72638a3c688e9792ca60944'


def git(repo, *args, data=None):
    return subprocess.check_output(['git', '-C', str(ROOT / repo), *args], input=data)


def asm_tree(repo, ref):
    tree = {}
    for row in git(repo, 'ls-tree', '-r', ref).decode().splitlines():
        metadata, name = row.split('\t', 1)
        if name.endswith('.asm') and not name.startswith(('battle/', 'items/', 'gfx/', 'audio/')):
            tree[name] = metadata.split()[2]
    objects = list(dict.fromkeys(tree.values()))
    raw = git(repo, 'cat-file', '--batch', data=('\n'.join(objects) + '\n').encode())
    content = {}
    offset = 0
    for obj in objects:
        end = raw.index(b'\n', offset)
        size = int(raw[offset:end].split()[2])
        content[obj] = raw[end + 1:end + 1 + size].decode().splitlines()
        offset = end + 2 + size
    assert offset == len(raw)
    return {name: content[obj] for name, obj in tree.items()}


def main():
    old = asm_tree('pokecrystal', BASE)
    head = git('perfect_crystal_source', 'rev-parse', 'HEAD').decode().strip()
    new = asm_tree('perfect_crystal_source', head)
    changes, patch = [], []
    for name in sorted(old.keys() | new.keys()):
        before, after = old.get(name, []), new.get(name, [])
        if before == after:
            continue
        diff = list(difflib.unified_diff(before, after, fromfile='baseline/' + name,
                                        tofile='perfect/' + name, n=3))
        count = sum(line.startswith(('+', '-')) and not line.startswith(('+++', '---'))
                    for line in diff)
        changes.append({'path': name, 'changed_lines': count,
                        'status': 'added' if name not in old else 'removed' if name not in new else 'modified'})
        patch.extend(diff)
    report = {'baseline': BASE, 'perfect_head': head,
              'baseline_assembly_files': len(old), 'perfect_assembly_files': len(new),
              'note': 'Source-only candidates; excludes battle/items/gfx/audio; no ROM inference.',
              'changes': changes}
    (ROOT / 'work/nonbattle_source_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    (ROOT / 'work/nonbattle_source_audit.patch').write_text('\n'.join(patch) + '\n')
    print('baseline', BASE, 'perfect_head', head)
    print('assembly_files', len(old), len(new), 'changed', len(changes))
    for row in changes:
        print(row['changed_lines'], row['status'], row['path'])


if __name__ == '__main__':
    main()
