"""Compare source-built map script bytes with original Japanese ROM."""
from pc_env import workspace
from pathlib import Path

root = workspace()
jp = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
built = (root / 'work/pokekuristaru_rgbds_history.gbc').read_bytes()
ue = (root / 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
perfect = (root / 'work/perfect_crystal_ue_patched.gbc').read_bytes()

for label, offset in [('goldenrod', 0x60f94), ('red', 0x18c603)]:
    for name, rom in [('built', built), ('jp', jp), ('ue', ue), ('perfect', perfect)]:
        print(label, name, f'{offset:06x}', rom[offset:offset + 96].hex(' '))

for label, begin, size in [('goldenrod_mobile', 0x60f94, 5),
                           ('red_prefix', 0x18c603, 5)]:
    needle = built[begin:begin + size]
    positions = []
    offset = 0
    while True:
        offset = jp.find(needle, offset)
        if offset < 0:
            break
        positions.append(f'{offset:06x}')
        offset += 1
    print(label, needle.hex(), positions[:100], 'count', len(positions))

for offset in (0x56940, 0x56955):
    print('jp_gold_trigger', f'{offset:06x}', jp[offset:offset + 100].hex(' '))
