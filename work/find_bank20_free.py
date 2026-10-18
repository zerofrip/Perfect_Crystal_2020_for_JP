"""Read-only scan of unused bank 20 padding in the local ROMs."""
from pc_env import workspace
from pathlib import Path

root = workspace()
for name, path in (
    ('jp', root / 'Pocket Monsters - Crystal Version (Japan).gbc'),
    ('baseline', root / 'work/pokekuristaru_rgbds_history.gbc'),
    ('perfect_ue', root / 'work/perfect_crystal_ue_patched.gbc'),
):
    bank = path.read_bytes()[0x80000:0x84000]
    for blank in (0x00, 0xff):
        last = max(i for i, value in enumerate(bank) if value != blank)
        print(name, f'last_non_{blank:02x}', f'{last:04x}', 'padding', 0x3fff - last)
