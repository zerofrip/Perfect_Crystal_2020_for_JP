"""Read-only locations of the three remaining AI-only 25% checks."""
from pc_env import workspace
from pathlib import Path

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
for name, prefix in (
    ('cp_40', bytes.fromhex('cd712ffe4038')),
    ('cp_41', bytes.fromhex('cd712ffe4138')),
):
    positions = []
    cursor = 0x34000
    while True:
        offset = stock.find(prefix, cursor, 0x38000)
        if offset < 0:
            break
        positions.append(offset)
        cursor = offset + 1
    print(name, [f'{offset:06x}' for offset in positions])
