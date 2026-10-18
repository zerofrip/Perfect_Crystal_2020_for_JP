"""Read-only source-build code anchor scan against stock Japanese ROM."""
from pc_env import workspace
from pathlib import Path

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
baseline = (root / 'work/pokekuristaru_rgbds_history.gbc').read_bytes()
for start, length in ((0x2C8A0, 8), (0x2C8A0, 6), (0x2C8A6, 8),
                      (0x2C8AC, 8), (0x2C8B0, 8), (0x2C8B3, 6),
                      (0x2CA4F, 8), (0x2CA50, 8), (0x2CA51, 7),
                      (0x2CA6C, 8)):
    needle = baseline[start:start + length]
    positions = []
    pos = stock.find(needle)
    while pos >= 0:
        positions.append(pos)
        pos = stock.find(needle, pos + 1)
    print(f'{start:06x}', needle.hex(), [f'{x:06x}' for x in positions[:20]], 'total', len(positions))
