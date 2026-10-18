"""Locate actual ROM references to Red's event flag and battle script."""
from pc_env import workspace
from pathlib import Path

root = workspace()
for label, path in (
    ('jp', root / 'Pocket Monsters - Crystal Version (Japan).gbc'),
    ('ue2020', root / 'work/perfect_crystal_ue_patched.gbc'),
):
    rom = path.read_bytes()
    for needle in (bytes.fromhex('33fa02'), bytes.fromhex('6e02'),
                   bytes.fromhex('33cd02'), bytes.fromhex('33b902')):
        hits = []
        pos = 0
        while True:
            pos = rom.find(needle, pos)
            if pos < 0:
                break
            hits.append(f'{pos:06x}')
            pos += 1
        print(label, needle.hex(), hits[:40], len(hits))
