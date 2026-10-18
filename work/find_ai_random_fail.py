"""Read-only search for the AI's extra status-failure routine."""
from pc_env import workspace
from pathlib import Path

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
baseline = (root / 'work/pokekuristaru_rgbds_history.gbc').read_bytes()
for name, source_offset, lengths in (
    ('status_fail', 0x35ECE, (5, 8, 10)),
    ('status_fail_tail', 0x35EE4, (6, 9)),
):
    for length in lengths:
        needle = baseline[source_offset:source_offset + length]
        offsets = []
        cursor = 0
        while True:
            found = stock.find(needle, cursor)
            if found < 0:
                break
            offsets.append(found)
            cursor = found + 1
        print(name, length, [f'{offset:06x}' for offset in offsets[:20]], len(offsets))
