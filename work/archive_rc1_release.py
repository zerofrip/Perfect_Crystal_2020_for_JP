"""Keep RC1 metadata before the latest release files become RC2."""
from pathlib import Path
import json

from pc_env import workspace

WORK = workspace() / 'work'
release = WORK / 'release'
manifest = json.loads((release / 'manifest.json').read_text())
archive = release / 'RC1_metadata'
if manifest['ips_file'] == 'Perfect_Crystal_2020_Japanese_RC1.ips':
    archive.mkdir(exist_ok=True)
    for name in ('manifest.json', 'README_JP.md', 'PORTING_STATUS.md'):
        source = (release / name).read_bytes()
        target = archive / name
        if target.exists():
            assert target.read_bytes() == source, f'existing RC1 archive differs: {name}'
        else:
            with target.open('xb') as f:
                f.write(source)
    print('RC1 metadata archived; named RC1 IPS and ROM retained')
else:
    assert (archive / 'manifest.json').exists(), 'RC1 archive missing'
    print('RC1 metadata archive already exists')
