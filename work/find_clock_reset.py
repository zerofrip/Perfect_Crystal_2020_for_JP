"""Read-only anchor scan of title-screen clock-reset logic."""
from pc_env import workspace
from pathlib import Path

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
baseline = (root / 'work/pokekuristaru_rgbds_history.gbc').read_bytes()
for offset, length in ((0x6315, 8), (0x6317, 10), (0x6321, 10),
                       (0x6325, 10), (0x6332, 9)):
    needle = baseline[offset:offset + length]
    positions = []
    cursor = 0
    while True:
        found = stock.find(needle, cursor)
        if found < 0:
            break
        positions.append(found)
        cursor = found + 1
    print(f'{offset:06x}', [f'{position:06x}' for position in positions])
