"""Read-only padding check for trainer party banks."""
from pc_env import workspace
from pathlib import Path

root = workspace()
for name, path in (
    ('jp', root / 'Pocket Monsters - Crystal Version (Japan).gbc'),
    ('baseline', root / 'work/pokekuristaru_rgbds_history.gbc'),
    ('stock_ue', root / 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc'),
    ('perfect_ue', root / 'work/perfect_crystal_ue_patched.gbc'),
):
    rom = path.read_bytes()
    for bank_number in (0x0e, 0x0f):
        bank = rom[bank_number * 0x4000:(bank_number + 1) * 0x4000]
        last = max(i for i, value in enumerate(bank) if value != 0)
        print(name, f'bank_{bank_number:02x}', 'last_nonzero', f'{last:04x}',
              'padding', 0x3fff - last)
