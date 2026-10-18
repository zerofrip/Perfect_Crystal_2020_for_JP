"""Read-only matching of source-build mart records in stock Japanese ROM."""
from pc_env import workspace
from pathlib import Path

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
baseline = (root / 'work/pokekuristaru_rgbds_history.gbc').read_bytes()
for name, source_offset, length in (
    ('Mart0', 0x160ed, 6),
    ('Mart1', 0x160f3, 7),
    ('Mart2', 0x160fa, 12),
    ('Mart5', 0x16118, 9),
    ('Mart23', 0x161b9, 9),
    ('Mart25', 0x161ce, 7),
    ('Mart26', 0x161d5, 5),
):
    needle = baseline[source_offset:source_offset + length]
    positions = []
    start = 0x14000
    while True:
        offset = stock.find(needle, start, 0x18000)
        if offset < 0:
            break
        positions.append(offset)
        start = offset + 1
    print(name, needle.hex(), [f'{offset:06x}' for offset in positions])
