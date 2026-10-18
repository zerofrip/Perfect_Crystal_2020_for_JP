"""Read-only bank 5 padding scan."""
from pc_env import workspace
from pathlib import Path

root = workspace()
for name, path in (
    ('jp', root / 'Pocket Monsters - Crystal Version (Japan).gbc'),
    ('baseline', root / 'work/pokekuristaru_rgbds_history.gbc'),
    ('perfect_ue', root / 'work/perfect_crystal_ue_patched.gbc'),
):
    bank = path.read_bytes()[0x14000:0x18000]
    last = max(i for i, value in enumerate(bank) if value != 0)
    print(name, 'last_nonzero', f'{last:04x}', 'padding', 0x3fff - last)
