"""Compare indexed mart item IDs in local Japanese and 2020-patched ROMs."""
from pc_env import workspace
from pathlib import Path
import sys

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
reference = (root / 'work/perfect_crystal_ue_patched.gbc').read_bytes()
partial = (root / 'work/development_only_jp_partial.gbc').read_bytes()

def marts(rom, table):
    result = []
    for index in range(34):
        address = int.from_bytes(rom[table + index * 2:table + index * 2 + 2], 'little')
        assert 0x4000 <= address < 0x8000
        offset = 0x14000 + address - 0x4000
        count = rom[offset]
        assert rom[offset + count + 1] == 0xff
        result.append((offset, bytes(rom[offset:offset + count + 2])))
    return result

for index, ((jp_offset, jp_record), (ue_offset, ue_record)) in enumerate(
    zip(marts(stock, 0x164c3), marts(reference, 0x160a9))
):
    if jp_record != ue_record:
        print(index, f'jp={jp_offset:06x}', f'ue={ue_offset:06x}',
              'jp_count', jp_record[0], 'ue_count', ue_record[0],
              'ue_item_ids', list(ue_record[1:-1]))

partial_marts = marts(partial, 0x164c3)
reference_marts = marts(reference, 0x160a9)
differences = [i for i, ((_, jp), (_, ue)) in enumerate(zip(partial_marts, reference_marts)) if jp != ue]
print('partial_vs_2020_different_marts', differences)
assert not differences
if '--include-reference-build' in sys.argv:
    built = (root / 'pokekuristaru/pokekuristaru.gbc').read_bytes()
    built_marts = marts(built, 0x160a9)
    built_differences = [i for i, ((_, candidate), (_, ue)) in enumerate(zip(built_marts, reference_marts))
                         if candidate != ue]
    print('built_source_vs_2020_different_marts', built_differences)
    assert not built_differences
