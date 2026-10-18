"""Retain the verified RC2 release metadata before packaging RC3."""
from pathlib import Path
import json
from hashlib import sha256

from pc_env import workspace

WORK=workspace()/'work'
release=WORK/'release'
manifest=json.loads((release/'manifest.json').read_text())
assert manifest['revision']=='RC2'
assert manifest['output_sha256']=='96b08ba49bc42096b2156a6795c86f1b47f40afe8786a6569da764d8c493163c'
assert sha256((WORK.parent/'Pokemon Perfect Crystal 2020 Japanese RC2.gbc').read_bytes()).hexdigest()==manifest['output_sha256']
assert sha256((release/manifest['ips_file']).read_bytes()).hexdigest()==manifest['ips_sha256']
archive=release/'RC2_metadata'
archive.mkdir(exist_ok=True)
for name in ('manifest.json','README_JP.md','PORTING_STATUS.md','rc2_cpu_verification.json'):
    data=(release/name).read_bytes()
    destination=archive/name
    if destination.exists():
        assert destination.read_bytes()==data, name
    else:
        with destination.open('xb') as stream: stream.write(data)
print('RC2 metadata archived; named RC2 ROM and IPS preserved')
