"""Read-only matching of badge boost routines in original Japanese ROM."""
from pc_env import workspace
from pathlib import Path

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
baseline = (root / 'work/pokekuristaru_rgbds_history.gbc').read_bytes()
for label, start, windows in (
    ('stat', 0x3ED45, ((0x13, 12), (0x20, 10), (0x30, 10))),
    ('type', 0xFBE24, ((0x00, 5), (0x0A, 6), (0x16, 5), (0x1C, 5), (0x20, 10))),
):
    for delta, size in windows:
        needle = baseline[start + delta:start + delta + size]
        positions = []
        cursor = 0
        while True:
            offset = stock.find(needle, cursor)
            if offset < 0:
                break
            positions.append(offset)
            cursor = offset + 1
        print(label, f'baseline={start + delta:06x}', needle.hex(),
              [f'{offset:06x}' for offset in positions[:12]], 'count', len(positions))
