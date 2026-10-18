"""Search code windows, without modifying or exposing ROM content."""
from pc_env import workspace
from collections import defaultdict
from pathlib import Path

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
baseline = (root / 'work/pokekuristaru_rgbds_history.gbc').read_bytes()
index = defaultdict(list)
width = 6
for position in range(len(stock) - width + 1):
    index[stock[position:position + width]].append(position)
hits = []
for position in range(0x2C867, 0x2C8B8):
    candidates = index.get(baseline[position:position + width], [])
    if len(candidates) <= 5:
        hits.append((position, candidates))
for position, candidates in hits:
    if candidates:
        print(f'{position:06x}', ','.join(f'{candidate:06x}' for candidate in candidates))
print('unique_windows', sum(len(candidates) == 1 for _, candidates in hits))
