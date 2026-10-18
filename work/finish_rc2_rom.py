"""Apply the final RC2 IPS locally, retaining this task's earlier candidate."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from pc_env import workspace

SOURCE_DIR = Path(__file__).resolve().parent
WORK = workspace() / 'work'
ROOT = workspace()
target = ROOT / 'Pokemon Perfect Crystal 2020 Japanese RC2.gbc'
manifest = json.loads((WORK / 'release/manifest.json').read_text())
expected = manifest['output_sha256']
assert manifest['revision'] == 'RC2'
if target.exists():
    existing = sha256(target.read_bytes()).hexdigest()
    if existing == expected:
        print('Final RC2 already exists and matches the verified manifest')
        raise SystemExit
    # This is the candidate generated in this task before the low-stat fix.
    assert existing == '5c109d7d3cb77a748e599a9ee38186af045ef36bff61f9a26fc2ba3f0b180b7f', 'unknown output: preserve it'
    archive = WORK / 'rc2_before_lowstat_guard.gbc'
    assert not archive.exists(), 'candidate archive already exists; preserve both files'
    target.rename(archive)
subprocess.run([sys.executable, str(SOURCE_DIR / 'apply_jp_patch.py'),
                str(ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc'),
                '--output', str(target)], check=True)
assert sha256(target.read_bytes()).hexdigest() == expected
