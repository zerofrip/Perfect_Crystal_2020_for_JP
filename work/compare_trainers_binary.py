"""Map existing trainer parties across Japanese and released-2020 ROMs."""
from pc_env import workspace
from collections import Counter
from pathlib import Path
import re

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
reference = (root / 'work/perfect_crystal_ue_patched.gbc').read_bytes()
english = (root / 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
pointer_source = (root / 'pokekuristaru/trainers/trainer_pointers.asm').read_text()
groups = re.findall(r'^\s*dw\s+(\w+Group)\s*$', pointer_source, flags=re.M)
assert len(groups) == 67

def group_offsets(rom, table):
    offsets = []
    for index in range(len(groups)):
        pointer = int.from_bytes(rom[table + 2 * index:table + 2 * index + 2], 'little')
        assert 0x4000 <= pointer < 0x8000
        offsets.append(0x38000 + pointer - 0x4000)
    for index, (a, b) in enumerate(zip(offsets, offsets[1:])):
        if not a < b:
            print('nonmonotonic', index, groups[index], f'{a:06x}', f'{b:06x}')
    return offsets

def parse_group(rom, begin, end):
    records = []
    position = begin
    while position < end:
        name_end = rom.find(b'\x50', position, min(position + 16, end))
        assert name_end >= 0, (f'{position:06x}', f'{end:06x}', 'name')
        type_offset = name_end + 1
        kind = rom[type_offset]
        assert kind in (0, 1, 2, 3), (f'{type_offset:06x}', kind)
        width = 2 + (1 if kind & 2 else 0) + (4 if kind & 1 else 0)
        party = []
        cursor = type_offset + 1
        while rom[cursor] != 0xFF:
            member = bytes(rom[cursor:cursor + width])
            assert 1 <= member[0] <= 100 and member[1] != 0
            party.append(member)
            cursor += width
            assert len(party) <= 6
        assert party
        records.append((position, type_offset, kind, tuple(party)))
        position = cursor + 1
    assert position == end, (f'{position:06x}', f'{end:06x}')
    return records

jp_offsets = group_offsets(stock, 0x399BA)
ue_offsets = group_offsets(reference, 0x3999E)
en_offsets = group_offsets(english, 0x39999)
assert jp_offsets[62] == 0x3B63F and ue_offsets[62] == 0x3BA0A
jp_bounds = jp_offsets + [0x3B700]
ue_bounds = ue_offsets + [0x3BAE1]
en_bounds = en_offsets + [0x3BA67]
stats = Counter()
for index, name in enumerate(groups):
    jp = parse_group(stock, jp_bounds[index], jp_bounds[index + 1])
    ue = parse_group(reference, ue_bounds[index], ue_bounds[index + 1])
    en = parse_group(english, en_bounds[index], en_bounds[index + 1])
    stats['jp_trainers'] += len(jp)
    stats['ue_trainers'] += len(ue)
    stats['en_trainers'] += len(en)
    if len(jp) != len(ue):
        print(name, 'trainer_count', len(jp), len(ue))
        stats['groups_with_count_difference'] += 1
    for trainer_index, (jp_record, ue_record) in enumerate(zip(jp, ue), start=1):
        en_record = en[trainer_index - 1]
        jp_kind, jp_party = jp_record[2:]
        ue_kind, ue_party = ue_record[2:]
        en_kind, en_party = en_record[2:]
        if (jp_kind, jp_party) != (en_kind, en_party):
            stats['jp_en_baseline_differences'] += 1
            print('jp_en_baseline_difference', name, trainer_index,
                  'kind', jp_kind, en_kind, 'party_count', len(jp_party), len(en_party))
        if (jp_kind, jp_party) != (ue_kind, ue_party):
            stats['different_trainers'] += 1
            if len(jp_party) != len(ue_party) or jp_kind != ue_kind:
                stats['structural_differences'] += 1
                print(name, trainer_index, 'kind', jp_kind, ue_kind,
                      'party_count', len(jp_party), len(ue_party))
            else:
                stats['same_shape_differences'] += 1
        if (en_kind, en_party) != (ue_kind, ue_party):
            stats['2020_changed_trainers'] += 1
            if en_kind == ue_kind == jp_kind and len(en_party) == len(ue_party) == len(jp_party):
                stats['2020_same_shape_trainers'] += 1
                for jp_member, en_member, ue_member in zip(jp_party, en_party, ue_party):
                    for jp_byte, en_byte, ue_byte in zip(jp_member, en_member, ue_member):
                        if en_byte != ue_byte:
                            stats['2020_changed_fields'] += 1
                            if jp_byte == en_byte:
                                stats['2020_fields_with_matching_jp_preimage'] += 1
                            elif jp_byte == ue_byte:
                                stats['2020_fields_already_jp'] += 1
                            else:
                                stats['2020_fields_jp_conflict'] += 1
            else:
                stats['2020_structural_trainers'] += 1
                if (jp_kind, jp_party) == (en_kind, en_party):
                    stats['2020_structural_with_exact_jp_preimage'] += 1
print('summary', dict(stats))
