"""Check every rebuilt trainer against Japanese names and 2020 battle data.

RC4 changes only Red's six level bytes (group 63 trainer 1).  That record is
still a 2020 battle record for the purpose of counting, but its levels are
allowed to differ.
"""
from pc_env import workspace
from pathlib import Path
from trainer_party_layout import trainer_groups

root = workspace()
japanese = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
english = (root / 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
reference = (root / 'work/perfect_crystal_ue_patched.gbc').read_bytes()
partial = (root / 'work/development_only_jp_partial.gbc').read_bytes()

jp_groups = trainer_groups(japanese, 0x399BA, 0x3B700)
en_groups = trainer_groups(english, 0x39999, 0x3BA67)
ue_groups = trainer_groups(reference, 0x3999E, 0x3BAE1)
new_groups = trainer_groups(partial, 0x399BA, 0x3B775)

changed = preserved = names = 0
red_location = (62, 0)  # group 63, trainer 1
for group_index, (jp_group, en_group, ue_group, new_group) in enumerate(
    zip(jp_groups, en_groups, ue_groups, new_groups)
):
    assert len(jp_group) == len(en_group) == len(ue_group) == len(new_group)
    for trainer_index, (jp, en, ue, new) in enumerate(
        zip(jp_group, en_group, ue_group, new_group)
    ):
        def parts(rom, entry):
            start, type_offset, kind, width, members = entry
            name = rom[start:type_offset]
            battle = bytes((kind,)) + b''.join(
                rom[member:member + width] for member in members
            ) + b'\xff'
            return name, battle

        jp_name, jp_battle = parts(japanese, jp)
        _, en_battle = parts(english, en)
        _, ue_battle = parts(reference, ue)
        new_name, new_battle = parts(partial, new)
        assert new_name == jp_name
        names += 1
        if en_battle != ue_battle:
            assert jp_battle == en_battle
            if (group_index, trainer_index) == red_location:
                # Red's species/items/moves/DVs match 2020; only levels changed.
                assert len(ue_battle) == len(new_battle), (
                    f"Red battle record length changed: {len(ue_battle)} -> {len(new_battle)}"
                )
                assert new_battle[0] == ue_battle[0]
                width = 7  # Red is kind 3
                level_positions = list(range(1, len(ue_battle) - 1, width))
                for pos in level_positions:
                    assert new_battle[pos + 1] == ue_battle[pos + 1]
                    assert new_battle[pos + 2] == ue_battle[pos + 2]
                    assert new_battle[pos + 3:pos + 7] == ue_battle[pos + 3:pos + 7]
                assert all(new_battle[pos] == 100 for pos in level_positions)
            else:
                assert new_battle == ue_battle
            changed += 1
        else:
            assert new_battle == jp_battle
            preserved += 1
assert (names, changed, preserved) == (541, 212, 329)
print('japanese_names_preserved', names)
print('released_2020_battle_records', changed)
print('unchanged_japanese_battle_records', preserved)
print('red_level_100_verified', True)
