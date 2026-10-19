"""Shared authored change layers for the RC5 integration build.

Every layer is driven by authored machine instructions and semantic
definitions (rc5_defs) plus the user's original Japanese ROM.  Reference
ROMs are never required: the optional ``refs`` tuple (english_stock,
patched_ue) only enables the historical cross-checks against the English
stock and released-2020 ROMs used by build_partial_jp_patch.py.
"""
from trainer_party_layout import rebuilt_japanese_trainers, rebuilt_2020_japanese_trainers
from rc5_defs import encounters as encounter_defs
from rc5_defs import trainers as trainer_defs
from rc5_defs import hall_hook

JOHTO_GRASS_RECORDS = 61
JOHTO_WATER_RECORDS = 38
KANTO_GRASS_RECORDS = 30


def unique_offset(haystack, needle, low=0, high=None):
    if high is None:
        high = len(haystack)
    first = haystack.find(needle, low, high)
    assert first >= 0 and haystack.find(needle, first + 1, high) < 0, "missing or ambiguous anchor"
    return first


def _grass_record(data, offset):
    """47 bytes: 2 map ids, three rates, 7 (level, species) slots per period."""
    b = data[offset:offset + 47]
    return (b[0], b[1], b[2], b[3], b[4],
            tuple((b[5 + 2 * i], b[6 + 2 * i]) for i in range(7)),
            tuple((b[19 + 2 * i], b[20 + 2 * i]) for i in range(7)),
            tuple((b[33 + 2 * i], b[34 + 2 * i]) for i in range(7)))


def _water_record(data, offset):
    """9 bytes: 2 map ids, one rate, three (level, species) slots."""
    b = data[offset:offset + 9]
    return (b[0], b[1], b[2],
            tuple((b[3 + 2 * i], b[4 + 2 * i]) for i in range(3)))


def _serialize_grass(record):
    out = bytearray(record[:5])
    for period in record[5:]:
        for level, species in period:
            out.extend((level, species))
    assert len(out) == 47
    return bytes(out)


def _serialize_water(record):
    out = bytearray(record[:3])
    for level, species in record[3]:
        out.extend((level, species))
    assert len(out) == 9
    return bytes(out)


def apply_encounter_tables(original, output, refs=None):
    """Johto grass/water encounter overrides; the extended Kanto tables are
    written later by the Cerulean Cave layer."""
    if refs is not None:
        english_stock, patched_ue = refs
        for title, english_offset, length, record_size in (
            ("johto_grass", 0x02A5E9, 61 * 47, 47),
            ("johto_water", 0x02B11D, 38 * 9, 9),
            ("kanto_grass_existing", 0x02B274, 30 * 47, 47),
        ):
            jp_offset = unique_offset(original, english_stock[english_offset:english_offset + 16])
            assert jp_offset // 0x4000 == english_offset // 0x4000
            assert original[jp_offset:jp_offset+length] == english_stock[english_offset:english_offset+length]
            for index in range(length // record_size):
                jp_id = original[jp_offset + index * record_size:jp_offset + index * record_size + 2]
                ue_id = patched_ue[english_offset + index * record_size:english_offset + index * record_size + 2]
                assert jp_id == ue_id, f"{title} map ID mismatch at {index}"
            output[jp_offset:jp_offset + length] = patched_ue[english_offset:english_offset + length]
            print(title, "JP_offset", f"{jp_offset:06x}", "records", length // record_size)
        # The historical path wrote the full released tables (including the
        # Kanto grass table the Cerulean Cave layer rewrites).
        return
    grass_changes = {i: rec for i, rec in encounter_defs.JOHTO_GRASS_CHANGES}
    water_changes = {i: rec for i, rec in encounter_defs.JOHTO_WATER_CHANGES}
    for index, record in encounter_defs.JOHTO_GRASS_CHANGES:
        offset = encounter_defs.JOHTO_GRASS_OFFSET + 47 * index
        assert _grass_record(original, offset) != record, 'encounter override is a no-op'
        output[offset:offset + 47] = _serialize_grass(record)
    for index, record in encounter_defs.JOHTO_WATER_CHANGES:
        offset = encounter_defs.JOHTO_WATER_OFFSET + 9 * index
        assert _water_record(original, offset) != record, 'encounter override is a no-op'
        output[offset:offset + 9] = _serialize_water(record)
    print("johto_encounters", "grass", len(grass_changes),
          "water", len(water_changes),
          "records", JOHTO_GRASS_RECORDS, JOHTO_WATER_RECORDS)


def apply_trade_evolutions(original, output, refs=None):
    refs_ue = refs[1] if refs is not None else None
    for name, old_item, stone_item, species in (
        ("POLITOED", 0x52, 0x08, 186),
        ("ALAKAZAM", 0xFF, 0x08, 65),
        ("MACHAMP", 0xFF, 0xA9, 68),
        ("GOLEM", 0xFF, 0xA9, 76),
        ("SLOWKING", 0x52, 0x18, 199),
        ("GENGAR", 0xFF, 0x08, 94),
        ("STEELIX", 0x8F, 0xA9, 208),
        ("KINGDRA", 0x97, 0x18, 230),
        ("SCIZOR", 0x8F, 0x22, 212),
        ("PORYGON2", 0xAC, 0x17, 233),
    ):
        before = bytes((3, old_item, species))
        after = bytes((2, stone_item, species))
        jp_offset = unique_offset(original, before, 0x40000, 0x44000)
        if refs_ue is not None:
            unique_offset(refs_ue, after, 0x40000, 0x44000)
        output[jp_offset:jp_offset + 3] = after
        print(name, "JP_offset", f"{jp_offset:06x}")


def apply_signature_moves(original, output, refs=None):
    # The released 2020 IPS moves each signature move from the level-1 slot to
    # level 22, leaving the other level-up moves intact.  Both complete records
    # have unique Japanese anchors within the evolution-data bank.
    refs_en = refs[0] if refs is not None else None
    refs_ue = refs[1] if refs is not None else None
    for name, jp_offset, ue_offset, old_record, new_record in (
        ("LUGIA", 0x43DBE, 0x43C1C,
         bytes.fromhex("0001b10bdb1610"), bytes.fromhex("0001100bdb16b1")),
        ("HO_OH", 0x43DD4, 0x43C32,
         bytes.fromhex("0001dd0bdb1610"), bytes.fromhex("0001100bdb16dd")),
    ):
        assert unique_offset(original, old_record, 0x40000, 0x44000) == jp_offset
        if refs_en is not None:
            assert unique_offset(refs_en, old_record, 0x40000, 0x44000) == ue_offset
        if refs_ue is not None:
            assert refs_ue[ue_offset:ue_offset + len(new_record)] == new_record
        assert original[jp_offset:jp_offset + len(old_record)] == old_record
        output[jp_offset:jp_offset + len(new_record)] = new_record
        print("signature_move", name, "JP_offset", f"{jp_offset:06x}")


def apply_hall_hook(original, output, refs=None):
    # The original Japanese decoration attribute table matches the released
    # 2020 decoration IDs byte for byte.  Hook the Japanese Script_setevent
    # call in bank $25 and execute the original action before awarding the
    # additional flags.  The hook bytes are authored in rc5_defs.hall_hook,
    # mirroring work/hall_decorations_hook.asm instruction for instruction.
    refs_en = refs[0] if refs is not None else None
    hall_decorations = [flag for flag in range(0x2A4, 0x2D2)
                        if flag not in (0x2B7, 0x2B9, 0x2BC, 0x2CD, 0x2CF)]
    assert len(hall_decorations) == 41
    decoration_table_bytes = 6 * 53
    if refs_en is not None:
        assert original[0x26D63:0x26D63 + decoration_table_bytes] == (
            refs_en[0x26A4F:0x26A4F + decoration_table_bytes]
        )
    setevent_original = bytes.fromhex("cd97265fcd9726570601cd412ec9")
    assert unique_offset(original, setevent_original, 0x94000, 0x98000) == 0x97965
    hook_call_offset = 0x9796F
    assert original[hook_call_offset:hook_call_offset + 3] == bytes.fromhex("cd412e")
    hook_offset = hall_hook.CAVE_OFFSET
    hook_size = hall_hook.HOOK_SIZE
    hook_code = hall_hook.hall_hook_code()
    assert len(hook_code) == hook_size and hook_code[:4] == bytes.fromhex("7aa72036")
    assert hook_code[-3:] == bytes.fromhex("c3412e")
    assert original[hook_offset:hook_offset + hook_size] == bytes(hook_size)
    output[hook_call_offset:hook_call_offset + 3] = bytes.fromhex("cd927f")
    output[hook_offset:hook_offset + hook_size] = hook_code
    print("hall_decoration_hook", "JP_call", f"{hook_call_offset:06x}",
          "code", f"{hook_offset:06x}", "flags", len(hall_decorations))


def apply_gs_ball(original, output, refs=None):
    # The original Japanese ROM has two XY trigger scripts for the GS Ball event.
    # Both start with the Japanese mobile-event check, followed by iffalse and the
    # original EVENT_GOT_GS_BALL guard. The released English 2020 script substitutes
    # EVENT_OPENED_MT_SILVER ($074f) for the mobile-event check. Script jumps in a
    # verified bank-$15 cave preserve all original Japanese dialogue and grant flow.
    refs_ue = refs[1] if refs is not None else None
    gs_prefix = bytes.fromhex("150b0f8600")
    gs_original = (
        (0x56940, bytes.fromhex("089769314003099769"), 0x6945),
        (0x56955, bytes.fromhex("089769314003099769"), 0x695A),
    )
    gs_cave = 0x57EEB
    assert original[gs_cave:gs_cave + 12] == bytes(12)
    if refs_ue is not None:
        assert refs_ue[0x60F94:0x60F99] == bytes.fromhex("150b0f8600")
        assert refs_ue[0x60F99:0x60F9C] == bytes.fromhex("314f07")
    for index, (offset, suffix, resume_address) in enumerate(gs_original):
        assert original[offset:offset + 14] == gs_prefix + suffix
        assert original[offset + 8:offset + 11] == bytes.fromhex("314003")
        cave_offset = gs_cave + index * 6
        cave_address = 0x7EEB + index * 6
        output[offset:offset + 5] = bytes((3, cave_address & 0xff, cave_address >> 8, 0, 0))
        output[cave_offset:cave_offset + 6] = bytes((0x31, 0x4f, 0x07, 3,
                                                     resume_address & 0xff,
                                                     resume_address >> 8))
    print("gs_ball_mt_silver_conditions", [f"{offset:06x}" for offset, _, _ in gs_original])


def apply_red_rewards(original, output, refs=None):
    # Red's Japanese map object is unique by sprite, position, script pointer,
    # and event flag $0762. Follow that *original ROM* pointer to his post-battle
    # script, then add the five released-2020 rewards after Red disappears.
    refs_ue = refs[1] if refs is not None else None
    red_person = bytes.fromhex("060e0d0700ffff8000ad4b6207")
    assert unique_offset(original, red_person, 0x70000, 0x74000) == 0x70C23
    red_script_offset = 0x70000 + int.from_bytes(red_person[9:11], "little") - 0x4000
    assert red_script_offset == 0x70BAD
    red_postbattle = bytes.fromhex("0f33006d028a0f0f32008a1e0f1b004800a19000")
    assert original[0x70BCE:0x70BCE + len(red_postbattle)] == red_postbattle
    red_reward_flags = (0x2CD, 0x2BC, 0x2B9, 0x2B7, 0x2CF)
    if refs_ue is not None:
        assert refs_ue[0x18C629:0x18C629 + 15] == b"".join(
            bytes((0x33, flag & 0xff, flag >> 8)) for flag in red_reward_flags)
    red_hook_offset = 0x70BD3
    red_cave_offset = 0x73F7E
    red_cave = b"".join(bytes((0x33, flag & 0xff, flag >> 8))
                        for flag in red_reward_flags)
    red_cave += bytes.fromhex("8a0f0f320003d84b")
    assert len(red_cave) == 23
    assert original[red_cave_offset:red_cave_offset + len(red_cave)] == bytes(len(red_cave))
    assert original[red_hook_offset:red_hook_offset + 3] == bytes.fromhex("8a0f0f")
    output[red_hook_offset:red_hook_offset + 3] = bytes.fromhex("037e7f")
    output[red_cave_offset:red_cave_offset + len(red_cave)] = red_cave
    print("red_decoration_rewards", "JP_script", f"{red_script_offset:06x}",
          "flags", len(red_reward_flags))


def apply_reusable_tm(original, output, refs=None):
    # TeachTMHM calls ConsumeTM after the happiness update.  The source-build
    # routine and its Japanese counterpart share the same control flow, while
    # their addresses differ.  Keep the original instruction size and branch.
    tm_context = bytes.fromhex("d80e0521587b3e01cfcd025d1807a7c9")
    tm_context_offset = unique_offset(original, tm_context, 0x2C000, 0x30000)
    assert tm_context_offset == 0x2DA22
    assert original[0x2DD02:0x2DD02 + 16] == bytes.fromhex("cd2159fa96d23d214cd806004f097ea7")
    tm_call_offset = tm_context_offset + 9
    assert original[tm_call_offset:tm_call_offset + 3] == bytes.fromhex("cd025d")
    output[tm_call_offset:tm_call_offset + 3] = b"\x00\x00\x00"
    print("reusable_tm_call", "JP_offset", f"{tm_call_offset:06x}")


def apply_tm_quantity(original, output, refs=None):
    # Skip the old TM quantity display.  The pocket loop reaches this block
    # after popping HL and BC; its old path pushed BC and popped it at $2DC55.
    # Jump to POP DE at $2DC56 to keep the stack balanced.
    tm_display_context = bytes.fromhex("e1c179c5fe3330180108000936f1233ef6")
    tm_display_offset = unique_offset(original, tm_display_context, 0x2C000, 0x30000)
    assert tm_display_offset == 0x2DC35
    tm_display_branch = tm_display_offset + 2
    assert original[tm_display_branch:tm_display_branch + 2] == b"\x79\xC5"
    assert original[tm_display_branch + 0x1F:tm_display_branch + 0x24] == bytes.fromhex("d1e1152085")
    output[tm_display_branch:tm_display_branch + 2] = b"\x18\x1D"
    print("hide_tm_quantity", "JP_offset", f"{tm_display_branch:06x}")


def apply_b_button_run(original, output, refs=None):
    # Bank 20's original TryStep routine calls BikeCheck at $418D, then branches
    # to Walk at $41AE or continues at $4192.  Redirect those five bytes to a
    # 28-byte trampoline in verified zero padding.  The trampoline checks B
    # while in PLAYER_NORMAL, then preserves the original BikeCheck path.
    run_hook = bytes.fromhex("cdca43201c21bbdbcb56280e")
    run_hook_offset = unique_offset(original, run_hook, 0x80000, 0x84000)
    assert run_hook_offset == 0x8018D
    assert original[0x801A7:0x801A9] == bytes.fromhex("3e02")  # fast
    assert original[0x801AE:0x801B0] == bytes.fromhex("3e01")  # walk
    assert original[0x80192:0x80195] == bytes.fromhex("21bbdb")  # bike flags
    run_cave_offset = 0x82000
    run_cave = bytes.fromhex(
        "cd0f60"    # call RunCheck at $600F
        "caa741"    # jp z, $41A7 (fast)
        "cdca43"    # call BikeCheck
        "c2ae41"    # jp nz, $41AE (walk)
        "c39241"    # jp $4192 (normal bike checks)
        "fa50d9"    # RunCheck: ld a, [PlayerState]
        "fe00"      # cp PLAYER_NORMAL
        "c0"        # ret nz
        "f0a4"      # ld a, [hJoypadDown]
        "e602"      # and B_BUTTON
        "fe02"      # cp B_BUTTON
        "c9"        # ret
    )
    assert len(run_cave) == 28
    assert original[run_cave_offset:run_cave_offset + len(run_cave)] == bytes(len(run_cave))
    output[run_hook_offset:run_hook_offset + 5] = bytes.fromhex("c300600000")
    output[run_cave_offset:run_cave_offset + len(run_cave)] = run_cave
    print("b_button_run_hook", "JP_offset", f"{run_hook_offset:06x}")
    print("b_button_run_cave", "JP_offset", f"{run_cave_offset:06x}")


def apply_marts(original, output, refs=None):
    # The stock Japanese item-name table already supplies Japanese names for
    # these items.  Relocate only the four changed mart inventories into blank
    # bank 5 padding and repoint their existing mart-table entries.
    refs_ue = refs[1] if refs is not None else None
    mart_table_anchor = bytes.fromhex("07650d65146520652b653265")
    mart_table = unique_offset(original, mart_table_anchor, 0x14000, 0x18000)
    assert mart_table == 0x164C3
    mart_cave = 0x17E00
    mart_cursor = mart_cave
    for mart_id, expected_jp_offset, expected_ue_offset, expected_items in (
        (5, 0x16532, 0x16118, [18, 17, 9, 13, 12, 10, 11, 8, 169, 24, 22, 34, 23]),
        (23, 0x165D3, 0x161BF, [18, 17, 16, 15, 39, 42, 43, 65, 21, 63, 64]),
        (25, 0x165E8, 0x161D8, [201, 202, 208, 209, 229, 200]),
        (26, 0x165EF, 0x161E0, [37, 184, 181, 163, 75, 170, 96, 180, 60, 30, 146, 3]),
    ):
        jp_pointer_offset = mart_table + mart_id * 2
        jp_pointer = int.from_bytes(original[jp_pointer_offset:jp_pointer_offset + 2], "little")
        assert jp_pointer == expected_jp_offset - 0x14000 + 0x4000
        old_count = original[expected_jp_offset]
        assert original[expected_jp_offset + old_count + 1] == 0xFF
        if refs_ue is not None:
            ue_pointer_offset = 0x160A9 + mart_id * 2
            ue_pointer = int.from_bytes(refs_ue[ue_pointer_offset:ue_pointer_offset + 2], "little")
            assert ue_pointer == expected_ue_offset - 0x14000 + 0x4000
            ue_count = refs_ue[expected_ue_offset]
            assert list(refs_ue[expected_ue_offset + 1:expected_ue_offset + ue_count + 1]) == expected_items
            assert refs_ue[expected_ue_offset + ue_count + 1] == 0xFF
        record = bytes([len(expected_items), *expected_items, 0xFF])
        assert original[mart_cursor:mart_cursor + len(record)] == bytes(len(record))
        output[mart_cursor:mart_cursor + len(record)] = record
        output[jp_pointer_offset:jp_pointer_offset + 2] = (
            mart_cursor - 0x14000 + 0x4000
        ).to_bytes(2, "little")
        print("mart", mart_id, "JP_offset", f"{mart_cursor:06x}", "items", len(expected_items))
        mart_cursor += len(record)
    assert mart_cursor == mart_cave + 50


def rebuild_trainers(original, output, refs=None):
    # All 541 trainer records fit in the original bank.  Rebuild the block from
    # original Japanese names and party data, replacing only the 212 battle
    # records changed by the actual 2020 IPS.  The other 329 records, including
    # the one Japanese-specific Pokefan party, stay Japanese-original.
    trainer_pointer_anchor = bytes.fromhex("3f7669769476")
    assert unique_offset(original, trainer_pointer_anchor, 0x38000, 0x3C000) == 0x39A36
    if refs is not None:
        english_stock, patched_ue = refs
        trainer_pointers, trainer_data, changed_trainers = rebuilt_2020_japanese_trainers(
            original, english_stock, patched_ue
        )
    else:
        changed_by_slot = {}
        for g, i, kind, members in trainer_defs.CHANGED_BATTLES:
            assert (g, i) not in changed_by_slot, ('duplicate trainer change', g, i)
            changed_by_slot[(g, i)] = (kind, members)
        trainer_pointers, trainer_data, changed_trainers = rebuilt_japanese_trainers(
            original, changed_by_slot
        )
        assert changed_trainers == 212
        assert 0x39A40 + len(trainer_data) == 0x3B775
    assert original[0x3B700:0x39A40 + len(trainer_data)] == bytes(
        0x39A40 + len(trainer_data) - 0x3B700
    )
    output[0x399BA:0x39A40] = trainer_pointers
    output[0x39A40:0x39A40 + len(trainer_data)] = trainer_data
    print("trainer_parties", "records", changed_trainers,
          "new_end", f"{0x39A40 + len(trainer_data):06x}")


def apply_badge_boosts(original, output, refs=None):
    # Perfect Crystal disables both badge stat boosts and badge type boosts.
    # Replacing the entry instruction with RET preserves registers/flags and is
    # equivalent to skipping every call site, including far-call dispatchers.
    for name, anchor, low, high, expected in (
        ("badge_stat_boosts", bytes.fromhex("fadcc2a7c0fab4cfa7c0fa4ad857e604"),
         0x3C000, 0x40000, 0x3ED57),
        ("badge_type_boosts", bytes.fromhex("fadcc2a7c0fab4cfa7c0f0e4a7c0d5c5"),
         0xF8000, 0xFC000, 0xFBF93),
    ):
        position = unique_offset(original, anchor, low, high)
        assert position == expected
        output[position] = 0xC9
        print(name, "JP_offset", f"{position:06x}")


def apply_ai_fixes(original, output, refs=None):
    # One of the AI-only random-failure helpers can be neutralized in place.
    # XOR A clears carry, so its caller's JR C branch never treats the status
    # move as a random failure, matching the 2020 source's removed check.
    ai_fail_anchor = bytes.fromhex("f0e4a72819fadcc2a72013")
    ai_fail_offset = unique_offset(original, ai_fail_anchor, 0x34000, 0x38000)
    assert ai_fail_offset == 0x35ECE
    output[ai_fail_offset:ai_fail_offset + 2] = bytes.fromhex("afc9")
    print("ai_status_random_fail_helper", "JP_offset", f"{ai_fail_offset:06x}")

    # The other three 25% AI-only checks are inline in poison, stat-down and
    # paralysis effects.  Their seven-byte RNG/carry branches are removed in
    # the 2020 source.  NOP each whole sequence without moving nearby jumps.
    for name, sequence, expected in (
        ("ai_poison_random_fail", bytes.fromhex("cd712ffe40382f"), 0x35F82),
        ("ai_stat_down_random_fail", bytes.fromhex("cd712ffe403845"), 0x36331),
        ("ai_paralyze_random_fail", bytes.fromhex("cd712ffe403844"), 0x36E58),
    ):
        offset = unique_offset(original, sequence, 0x34000, 0x38000)
        assert offset == expected
        output[offset:offset + len(sequence)] = bytes(len(sequence))
        print(name, "JP_offset", f"{offset:06x}")
