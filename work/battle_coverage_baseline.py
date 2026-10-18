"""Read-only source audit against the identified original upstream snapshot.

The output is a source-candidate inventory. The supplied 2020 ROM, not either
source revision, determines whether a candidate belongs in the port.
"""
from pc_env import workspace
from pathlib import Path
import difflib
import json
import subprocess

ROOT = workspace()
BASE = '51bad5a606d7b2e8f72638a3c688e9792ca60944'
IMPORT = 'ee6828e'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(ROOT/repo), *args], text=True)


def normal(text):
    return [' '.join(line.split(';')[0].split()).replace('jp [hl]', 'jp hl')
            for line in text.splitlines() if line.split(';')[0].strip()]


reports = []
inventory = []
paths = git('perfect_crystal_source', 'ls-tree', '-r', '--name-only', IMPORT,
            'battle', 'items').splitlines()
for path in paths:
    if not path.endswith('.asm'):
        continue
    baseline = git('pokecrystal', 'show', BASE+':'+path)
    initial = git('perfect_crystal_source', 'show', IMPORT+':'+path)
    final = (ROOT/'perfect_crystal_source'/path).read_text()
    for stage, revised in [('initial', initial), ('latest_source', final)]:
        before, after = normal(baseline), normal(revised)
        if before == after:
            continue
        patch = list(difflib.unified_diff(before, after,
                     fromfile=path+' baseline', tofile=path+' '+stage, n=5))
        changed = sum(line.startswith(('+', '-')) and
                      not line.startswith(('+++', '---')) for line in patch)
        inventory.append({'path': path, 'stage': stage, 'changed_lines': changed})
        reports.extend(patch)
        print(stage, path, changed)
(ROOT/'work/battle_coverage_baseline.patch').write_text('\n'.join(reports)+'\n')
(ROOT/'work/battle_coverage_baseline.json').write_text(json.dumps({
    'baseline': BASE, 'initial': IMPORT, 'changes': inventory}, indent=2)+'\n')
