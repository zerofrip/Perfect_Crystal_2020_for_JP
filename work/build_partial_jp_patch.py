"""Build a local, development-only partial Japanese port with strict anchors.

Historical integration builder: requires the private English stock and
released-2020 ROMs as reference cross-checks.  The default JP-only builder is
build_rc5_from_jp.py; both share the authored change layers in rc5_layers.py.
"""
from pc_env import workspace
from hashlib import sha1, sha256
from pathlib import Path
import sys

root = workspace()
original = (root / "Pocket Monsters - Crystal Version (Japan).gbc").read_bytes()
assert sha1(original).hexdigest() == "95127b901bbce2407daf43cce9f45d4c27ef635d"
patched_ue = (root / "work/perfect_crystal_ue_patched.gbc").read_bytes()
english_stock = (root / "Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc").read_bytes()
assert sha1(english_stock).hexdigest() == "f2f52230b536214ef7c9924f483392993e226cfb"
assert len(original) == len(patched_ue) == len(english_stock) == 2 * 1024 * 1024
output = bytearray(original)

from rc5_layers import (
    apply_ai_fixes, apply_badge_boosts, apply_b_button_run, apply_encounter_tables,
    apply_gs_ball, apply_hall_hook, apply_marts,
    apply_red_rewards, apply_reusable_tm, apply_signature_moves,
    apply_tm_quantity, apply_trade_evolutions, rebuild_trainers,
)

refs = (english_stock, patched_ue)
apply_encounter_tables(original, output, refs)
apply_trade_evolutions(original, output, refs)
apply_signature_moves(original, output, refs)
apply_hall_hook(original, output, refs)
apply_gs_ball(original, output, refs)
apply_red_rewards(original, output, refs)
apply_reusable_tm(original, output, refs)
apply_tm_quantity(original, output, refs)
apply_b_button_run(original, output, refs)
apply_marts(original, output, refs)
rebuild_trainers(original, output, refs)
apply_badge_boosts(original, output, refs)
apply_ai_fixes(original, output, refs)

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

# Preserve the exact verified RC4 baseline before restoring the
# Japanese-original graphics in RC5.
rc4_reference = bytearray(output)
rc4_reference[0x14D] = (-sum(rc4_reference[0x134:0x14D]) - 25) & 0xFF
rc4_sum = (sum(rc4_reference) - rc4_reference[0x14E] - rc4_reference[0x14F]) & 0xFFFF
rc4_reference[0x14E:0x150] = rc4_sum.to_bytes(2, 'big')
assert sha256(rc4_reference).hexdigest() == 'f7a0da3b9df33d4d010b05d82c8e6644d09ebd9c42320cc1ee89d4e2fd20ddd6'
(root / 'work/rc4_reference.gbc').write_bytes(rc4_reference)

from apply_japanese_original_sprites import apply_japanese_original_sprites
rc5_ranges = apply_japanese_original_sprites(original, english_stock, patched_ue, output)
(root / 'work/rc5_sprite_restore_ranges.json').write_text(json.dumps(rc5_ranges, indent=2) + '\n')
print('rc5_japanese_original_sprites', len(rc5_ranges), 'ranges restored to the Japanese originals')

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
