from pc_env import workspace
from pathlib import Path

rom = (workspace() / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
for start in range(0x54000, 0x58000):
    if rom[start] != 0 or (start > 0x54000 and rom[start - 1] == 0):
        continue
    end = start
    while end < 0x58000 and rom[end] == 0:
        end += 1
    if end - start >= 16:
        print(f'{start:06x}', f'{end:06x}', end - start)
