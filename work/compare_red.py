"""Read-only comparison of Red's stock and released-2020 trainer battle data."""
from pc_env import workspace
from pathlib import Path

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
reference = (root / 'work/perfect_crystal_ue_patched.gbc').read_bytes()
partial = (root / 'work/development_only_jp_partial.gbc').read_bytes()

def parse(rom, group_offset):
    name_end = rom.index(0x50, group_offset, group_offset + 16)
    type_offset = name_end + 1
    kind = rom[type_offset]
    assert kind in (1, 3)
    width = 6 if kind == 1 else 7
    records = []
    pos = type_offset + 1
    while rom[pos] != 0xFF:
        record = rom[pos:pos + width]
        records.append((record[0], record[1], None if kind == 1 else record[2],
                        tuple(record[-4:])))
        pos += width
    assert len(records) == 6
    return kind, records, pos + 1

jp_kind, jp_party, jp_end = parse(stock, 0x3B63F)
ue_kind, ue_party, ue_end = parse(reference, 0x3BA0A)
print('jp_type', jp_kind, 'ue_type', ue_kind, 'party_count', len(jp_party))
for index, (jp, ue) in enumerate(zip(jp_party, ue_party), start=1):
    print(index, 'jp_level_species_moves', (jp[0], jp[1], jp[3]),
          'ue_level_species_item_moves', ue)
assert all((jp[0], jp[1], jp[3]) == (ue[0], ue[1], ue[3]) for jp, ue in zip(jp_party, ue_party))
print('original_red_record_size', jp_end - 0x3B63F)
print('reference_red_record_size', ue_end - 0x3BA0A)
red_pointer = int.from_bytes(partial[0x39A36:0x39A38], 'little')
red_offset = 0x38000 + red_pointer - 0x4000
partial_kind, partial_party, partial_end = parse(partial, red_offset)
assert partial[red_offset:red_offset + 4] == stock[0x3B63F:0x3B643]
assert partial_kind == ue_kind and partial_party == ue_party
print('partial_red_matches_2020_battle_data', True)
