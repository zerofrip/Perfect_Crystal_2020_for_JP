"""Build a local, development-only partial Japanese port with strict anchors."""
from pc_env import workspace
from hashlib import sha1, sha256
from pathlib import Path
import sys
from trainer_party_layout import rebuilt_2020_japanese_trainers

root = workspace()
original = (root / "Pocket Monsters - Crystal Version (Japan).gbc").read_bytes()
assert sha1(original).hexdigest() == "95127b901bbce2407daf43cce9f45d4c27ef635d"
patched_ue = (root / "work/perfect_crystal_ue_patched.gbc").read_bytes()
english_stock = (root / "Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc").read_bytes()
assert sha1(english_stock).hexdigest() == "f2f52230b536214ef7c9924f483392993e226cfb"
assert len(original) == len(patched_ue) == len(english_stock) == 2 * 1024 * 1024
output = bytearray(original)

def unique_offset(haystack, needle, low=0, high=None):
    if high is None:
        high = len(haystack)
    first = haystack.find(needle, low, high)
    assert first >= 0 and haystack.find(needle, first + 1, high) < 0, "missing or ambiguous anchor"
    return first

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
    unique_offset(patched_ue, after, 0x40000, 0x44000)
    output[jp_offset:jp_offset + 3] = after
    print(name, "JP_offset", f"{jp_offset:06x}")

# The released 2020 IPS moves each signature move from the level-1 slot to
# level 22, leaving the other level-up moves intact.  Both complete records
# have unique Japanese and English anchors within the evolution-data bank.
for name, jp_offset, ue_offset, old_record, new_record in (
    ("LUGIA", 0x43DBE, 0x43C1C,
     bytes.fromhex("0001b10bdb1610"), bytes.fromhex("0001100bdb16b1")),
    ("HO_OH", 0x43DD4, 0x43C32,
     bytes.fromhex("0001dd0bdb1610"), bytes.fromhex("0001100bdb16dd")),
):
    assert unique_offset(original, old_record, 0x40000, 0x44000) == jp_offset
    assert unique_offset(english_stock, old_record, 0x40000, 0x44000) == ue_offset
    assert patched_ue[ue_offset:ue_offset + len(new_record)] == new_record
    assert original[jp_offset:jp_offset + len(old_record)] == old_record
    output[jp_offset:jp_offset + len(new_record)] = new_record
    print("signature_move", name, "JP_offset", f"{jp_offset:06x}")

# The released 2020 Hall of Fame script grants 41 decoration flags after it
# sets EVENT_BEAT_ELITE_FOUR.  The original Japanese decoration attribute table
# is byte-identical to the stock English one, so these IDs refer to the same
# Japanese decorations.  Hook the Japanese Script_setevent call in bank $25
# and execute the original action before awarding the additional flags.
hall_script_flag_offset = 0x181475
assert patched_ue[hall_script_flag_offset:hall_script_flag_offset + 3] == bytes.fromhex("334400")
hall_decorations = [flag for flag in range(0x2A4, 0x2D2)
                    if flag not in (0x2B7, 0x2B9, 0x2BC, 0x2CD, 0x2CF)]
assert len(hall_decorations) == 41
for index, flag in enumerate(hall_decorations, 1):
    offset = hall_script_flag_offset + index * 3
    assert patched_ue[offset:offset + 3] == bytes((0x33, flag & 0xFF, flag >> 8))
assert patched_ue[hall_script_flag_offset + 42 * 3:hall_script_flag_offset + 43 * 3] == bytes.fromhex("337c07")
decoration_table_bytes = 6 * 53
assert original[0x26D63:0x26D63 + decoration_table_bytes] == (
    english_stock[0x26A4F:0x26A4F + decoration_table_bytes]
)
setevent_original = bytes.fromhex("cd97265fcd9726570601cd412ec9")
assert unique_offset(original, setevent_original, 0x94000, 0x98000) == 0x97965
hook_call_offset = 0x9796F
assert original[hook_call_offset:hook_call_offset + 3] == bytes.fromhex("cd412e")
hook_rom = (root / "work/hall_decorations_hook.gb").read_bytes()
hook_offset = 0x97F92
hook_size = 0x3D
hook_code = hook_rom[hook_offset:hook_offset + hook_size]
assert len(hook_code) == hook_size and hook_code[:4] == bytes.fromhex("7aa72036")
assert hook_code[-3:] == bytes.fromhex("c3412e")
assert original[hook_offset:hook_offset + hook_size] == bytes(hook_size)
output[hook_call_offset:hook_call_offset + 3] = bytes.fromhex("cd927f")
output[hook_offset:hook_offset + hook_size] = hook_code
print("hall_decoration_hook", "JP_call", f"{hook_call_offset:06x}",
      "code", f"{hook_offset:06x}", "flags", len(hall_decorations))

# The original Japanese ROM has two XY trigger scripts for the GS Ball event.
# Both start with the Japanese mobile-event check, followed by iffalse and the
# original EVENT_GOT_GS_BALL guard. The released English 2020 script substitutes
# EVENT_OPENED_MT_SILVER ($074f) for the mobile-event check. Script jumps in a
# verified bank-$15 cave preserve all original Japanese dialogue and grant flow.
gs_prefix = bytes.fromhex("150b0f8600")
gs_original = (
    (0x56940, bytes.fromhex("089769314003099769"), 0x6945),
    (0x56955, bytes.fromhex("089769314003099769"), 0x695A),
)
gs_cave = 0x57EEB
assert original[gs_cave:gs_cave + 12] == bytes(12)
assert patched_ue[0x60F94:0x60F99] == bytes.fromhex("150b0f8600")
assert patched_ue[0x60F99:0x60F9C] == bytes.fromhex("314f07")
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

# Red's Japanese map object is unique by sprite, position, script pointer,
# and event flag $0762. Follow that *original ROM* pointer to his post-battle
# script, then add the five released-2020 rewards after Red disappears.
red_person = bytes.fromhex("060e0d0700ffff8000ad4b6207")
assert unique_offset(original, red_person, 0x70000, 0x74000) == 0x70C23
red_script_offset = 0x70000 + int.from_bytes(red_person[9:11], "little") - 0x4000
assert red_script_offset == 0x70BAD
red_postbattle = bytes.fromhex("0f33006d028a0f0f32008a1e0f1b004800a19000")
assert original[0x70BCE:0x70BCE + len(red_postbattle)] == red_postbattle
red_reward_flags = (0x2CD, 0x2BC, 0x2B9, 0x2B7, 0x2CF)
assert patched_ue[0x18C629:0x18C629 + 15] == b"".join(
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

# The stock Japanese item-name table already supplies Japanese names for
# these items.  Relocate only the four changed mart inventories into blank
# bank 5 padding and repoint their existing mart-table entries.
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
    ue_pointer_offset = 0x160A9 + mart_id * 2
    ue_pointer = int.from_bytes(patched_ue[ue_pointer_offset:ue_pointer_offset + 2], "little")
    assert ue_pointer == expected_ue_offset - 0x14000 + 0x4000
    new_count = patched_ue[expected_ue_offset]
    record = patched_ue[expected_ue_offset:expected_ue_offset + new_count + 2]
    assert list(record[1:-1]) == expected_items and record[-1] == 0xFF
    assert original[mart_cursor:mart_cursor + len(record)] == bytes(len(record))
    output[mart_cursor:mart_cursor + len(record)] = record
    output[jp_pointer_offset:jp_pointer_offset + 2] = (
        mart_cursor - 0x14000 + 0x4000
    ).to_bytes(2, "little")
    print("mart", mart_id, "JP_offset", f"{mart_cursor:06x}", "items", new_count)
    mart_cursor += len(record)
assert mart_cursor == mart_cave + 50

# All 541 trainer records fit in the original bank.  Rebuild the block from
# original Japanese names and party data, replacing only the 212 battle
# records changed by the actual 2020 IPS.  The other 329 records, including
# the one Japanese-specific Pokefan party, stay Japanese-original.
trainer_pointer_anchor = bytes.fromhex("3f7669769476")
assert unique_offset(original, trainer_pointer_anchor, 0x38000, 0x3C000) == 0x39A36
trainer_pointers, trainer_data, changed_trainers = rebuilt_2020_japanese_trainers(
    original, english_stock, patched_ue
)
assert original[0x3B700:0x39A40 + len(trainer_data)] == bytes(
    0x39A40 + len(trainer_data) - 0x3B700
)
output[0x399BA:0x39A40] = trainer_pointers
output[0x39A40:0x39A40 + len(trainer_data)] = trainer_data
print("trainer_parties", "records", changed_trainers,
      "new_end", f"{0x39A40 + len(trainer_data):06x}")

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

from port_cerulean_cave import apply_cave_port
import json
cave_ranges = apply_cave_port(original, english_stock, patched_ue, output)
(root / 'work/cerulean_cave_ranges.json').write_text(
    json.dumps(cave_ranges, indent=2) + '\n')
print('cerulean_cave_maps', 3, 'localized_events', 3)

from port_clock_reset import apply_clock_reset
clock_ranges = apply_clock_reset(original, english_stock, patched_ue, output)
(root / 'work/clockreset_ranges.json').write_text(json.dumps(clock_ranges, indent=2) + '\n')
print('clock_reset', 'Japanese title confirmation and native RTC setup')

from port_battle_bugfixes import apply_battle_bugfixes
battle_ranges = apply_battle_bugfixes(original, english_stock, patched_ue, output)
(root / 'work/battlefix_ranges.json').write_text(json.dumps(battle_ranges, indent=2) + '\n')
print('battle_bugfixes', len(battle_ranges), 'validated write ranges')

from port_gym_rematches import apply_gym_rematches
gym_ranges = apply_gym_rematches(original, english_stock, patched_ue, output)
(root / 'work/gym_ranges.json').write_text(json.dumps(gym_ranges, indent=2) + '\n')
print('gym_rematches', 16, 'Japanese dialogue')

from port_misc_fixes import apply_misc_fixes
misc_ranges = apply_misc_fixes(original, english_stock, patched_ue, output)
(root / 'work/misc_ranges.json').write_text(json.dumps(misc_ranges, indent=2) + '\n')
print('misc_fixes', len(misc_ranges), 'validated write ranges')

from port_restored_sprites import apply_restored_sprites
sprite_ranges = apply_restored_sprites(original, english_stock, patched_ue, output)
(root / 'work/sprite_ranges.json').write_text(json.dumps(sprite_ranges, indent=2) + '\n')
print('restored_sprites', 'female swimmer, Jynx front and animation frames')

from port_dialogue_updates import apply_dialogue_updates
dialogue_ranges = apply_dialogue_updates(original, english_stock, patched_ue, output)
(root / 'work/dialogue_ranges.json').write_text(json.dumps(dialogue_ranges, indent=2) + '\n')
print('dialogue_updates', 6, 'Japanese explanations')

from port_item_attributes import apply_item_attributes
item_ranges = apply_item_attributes(original, english_stock, patched_ue, output)
(root / 'work/item_attribute_ranges.json').write_text(json.dumps(item_ranges, indent=2) + '\n')
print('item_attribute_updates', len(item_ranges), 'prices and held effects')

from port_remaining_features import apply_remaining_features
remaining_ranges = apply_remaining_features(original, english_stock, patched_ue, output)
(root / 'work/remaining_ranges.json').write_text(json.dumps(remaining_ranges, indent=2) + '\n')
print('remaining_features', 5, 'evolution scan, HP pixels, Red DVs, trade names and Silph dialogue')

# Preserve and verify the faithful RC1 result before applying requested fixes.
rc1_reference = bytearray(output)
rc1_reference[0x14D] = (-sum(rc1_reference[0x134:0x14D]) - 25) & 0xFF
rc1_sum = (sum(rc1_reference) - rc1_reference[0x14E] - rc1_reference[0x14F]) & 0xFFFF
rc1_reference[0x14E:0x150] = rc1_sum.to_bytes(2, 'big')
assert sha256(rc1_reference).hexdigest() == 'bdb8b08177dc6e5a549c5d3ed2499a9835ae7c7c01ad0acafda659072335805e'
(root / 'work/rc1_reference.gbc').write_bytes(rc1_reference)
from fix_requested_issues import apply_requested_fixes
requested_ranges = apply_requested_fixes(original, english_stock, patched_ue, output)
(root / 'work/requested_fix_ranges.json').write_text(json.dumps(requested_ranges, indent=2) + '\n')
print('requested_rc2_corrections', 4, 'validated write ranges', len(requested_ranges))

# Keep the exact verified RC2 baseline before the requested held-item cap fix.
rc2_reference = bytearray(output)
rc2_reference[0x14D] = (-sum(rc2_reference[0x134:0x14D]) - 25) & 0xFF
rc2_sum = (sum(rc2_reference) - rc2_reference[0x14E] - rc2_reference[0x14F]) & 0xFFFF
rc2_reference[0x14E:0x150] = rc2_sum.to_bytes(2, 'big')
assert sha256(rc2_reference).hexdigest() == '96b08ba49bc42096b2156a6795c86f1b47f40afe8786a6569da764d8c493163c'
(root / 'work/rc2_reference.gbc').write_bytes(rc2_reference)
from fix_held_item_stat_cap import apply_held_item_stat_cap_fix
cap_ranges = apply_held_item_stat_cap_fix(original, english_stock, patched_ue, output)
(root / 'work/held_item_stat_cap_ranges.json').write_text(json.dumps(cap_ranges, indent=2) + '\n')
print('requested_rc3_held_item_cap', 'validated write ranges', len(cap_ranges))

# Preserve the exact verified RC3 baseline before the RC4 corrections.
rc3_reference = bytearray(output)
rc3_reference[0x14D] = (-sum(rc3_reference[0x134:0x14D]) - 25) & 0xFF
rc3_sum = (sum(rc3_reference) - rc3_reference[0x14E] - rc3_reference[0x14F]) & 0xFFFF
rc3_reference[0x14E:0x150] = rc3_sum.to_bytes(2, 'big')
assert sha256(rc3_reference).hexdigest() == 'b6f6b73dc7e6d8f4d3223b398fb1202519efae0c0e36959ab7ac43cb8e5a4c21'
(root / 'work/rc3_reference.gbc').write_bytes(rc3_reference)

from apply_rc4_corrections import apply_rc4_corrections
rc4_ranges = apply_rc4_corrections(original, english_stock, patched_ue, output)
(root / 'work/rc4_correction_ranges.json').write_text(json.dumps(rc4_ranges, indent=2) + '\n')
print('requested_rc4_corrections', 'validated write ranges', len(rc4_ranges))

# Game Boy ROM header and global checksums.
output[0x14D] = (-sum(output[0x134:0x14D]) - 25) & 0xFF
global_sum = (sum(output) - output[0x14E] - output[0x14F]) & 0xFFFF
output[0x14E:0x150] = global_sum.to_bytes(2, "big")

rom_path = root / "work/development_only_jp_partial.gbc"
ips_path = root / "work/development_only_jp_partial.ips"
rom_path.write_bytes(output)

# Minimal IPS records, split at 65535 bytes if needed.
with ips_path.open("wb") as file:
    file.write(b"PATCH")
    index = 0
    while index < len(original):
        if original[index] == output[index]:
            index += 1
            continue
        start = index
        while index < len(original) and original[index] != output[index] and index - start < 65535:
            index += 1
        data = output[start:index]
        file.write(start.to_bytes(3, "big"))
        file.write(len(data).to_bytes(2, "big"))
        file.write(data)
    file.write(b"EOF")

# Reapply locally with the required lazy_ips reader and check exact output.
sys.path.insert(0, str(root / "lazy_ips"))
from lazy_ips.patch import ips
roundtrip = bytearray(original)
with ips_path.open("rb") as file:
    for record in ips.read_patch(file):
        roundtrip[record.offset:record.offset + len(record.data)] = record.data
assert bytes(roundtrip) == bytes(output)
print("development_rom_sha256", sha256(output).hexdigest())
print("development_ips_sha256", sha256(ips_path.read_bytes()).hexdigest())
print("changed_bytes", sum(a != b for a, b in zip(original, output)))
