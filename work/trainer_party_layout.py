"""Read the indexed trainer-party layout without interpreting visible names."""

GROUP_COUNT = 67


def trainer_groups(rom, pointer_table, final_end):
    offsets = []
    for group in range(GROUP_COUNT):
        entry = pointer_table + 2 * group
        pointer = int.from_bytes(rom[entry:entry + 2], 'little')
        assert 0x4000 <= pointer < 0x8000
        offsets.append(0x38000 + pointer - 0x4000)
    assert all(a <= b for a, b in zip(offsets, offsets[1:]))
    assert offsets[-1] < final_end

    result = []
    for begin, end in zip(offsets, offsets[1:] + [final_end]):
        trainers = []
        cursor = begin
        while cursor < end:
            name_end = rom.find(b'\x50', cursor, min(cursor + 16, end))
            assert name_end >= 0
            kind_offset = name_end + 1
            kind = rom[kind_offset]
            assert kind in (0, 1, 2, 3)
            width = 2 + (1 if kind & 2 else 0) + (4 if kind & 1 else 0)
            members = []
            position = kind_offset + 1
            while rom[position] != 0xFF:
                assert 1 <= rom[position] <= 100 and rom[position + 1] != 0
                members.append(position)
                position += width
                assert len(members) <= 6
            assert members
            trainers.append((cursor, kind_offset, kind, width, tuple(members)))
            cursor = position + 1
        assert cursor == end
        result.append(tuple(trainers))
    assert sum(map(len, result)) == 541
    return tuple(result)


def rebuilt_2020_japanese_trainers(japanese, english, updated):
    """Return relocated groups using Japanese names and released-2020 parties."""
    jp_groups = trainer_groups(japanese, 0x399BA, 0x3B700)
    en_groups = trainer_groups(english, 0x39999, 0x3BA67)
    ue_groups = trainer_groups(updated, 0x3999E, 0x3BAE1)
    start = 0x39A40
    assert jp_groups[0][0][0] == start
    old_data = bytearray()
    new_data = bytearray()
    pointers = bytearray()
    changed_trainers = 0
    for jp_group, en_group, ue_group in zip(jp_groups, en_groups, ue_groups):
        assert len(jp_group) == len(en_group) == len(ue_group)
        address = 0x4000 + start + len(new_data) - 0x38000
        assert 0x4000 <= address < 0x8000
        pointers.extend(address.to_bytes(2, 'little'))
        for jp_trainer, en_trainer, ue_trainer in zip(jp_group, en_group, ue_group):
            jp_start, jp_type, jp_kind, jp_width, jp_members = jp_trainer
            _, _, en_kind, en_width, en_members = en_trainer
            _, _, ue_kind, ue_width, ue_members = ue_trainer
            japanese_name = japanese[jp_start:jp_type]
            assert japanese_name.endswith(b'\x50')

            def battle_data(rom, kind, width, members):
                return bytes((kind,)) + b''.join(
                    rom[member:member + width] for member in members
                ) + b'\xff'

            jp_battle = battle_data(japanese, jp_kind, jp_width, jp_members)
            en_battle = battle_data(english, en_kind, en_width, en_members)
            ue_battle = battle_data(updated, ue_kind, ue_width, ue_members)
            old_data.extend(japanese_name + jp_battle)
            if en_battle != ue_battle:
                assert jp_battle == en_battle
                new_battle = ue_battle
                changed_trainers += 1
            else:
                new_battle = jp_battle
            new_data.extend(japanese_name + new_battle)
    assert len(pointers) == GROUP_COUNT * 2
    assert bytes(old_data) == japanese[start:0x3B700]
    assert changed_trainers == 212
    assert len(new_data) - len(old_data) == 117
    assert start + len(new_data) == 0x3B775
    return bytes(pointers), bytes(new_data), changed_trainers
