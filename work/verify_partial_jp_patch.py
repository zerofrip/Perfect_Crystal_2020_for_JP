"""Check the local development patch's hashes, checksums and change ranges."""
from pc_env import workspace
from pathlib import Path
from hashlib import sha1
from trainer_party_layout import rebuilt_2020_japanese_trainers

root = workspace()
stock = (root / "Pocket Monsters - Crystal Version (Japan).gbc").read_bytes()
patched = (root / "work/development_only_jp_partial.gbc").read_bytes()
english = (root / "Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc").read_bytes()
reference = (root / "work/perfect_crystal_ue_patched.gbc").read_bytes()
assert sha1(stock).hexdigest() == "95127b901bbce2407daf43cce9f45d4c27ef635d"
assert len(stock) == len(patched) == 2 * 1024 * 1024
header = (-sum(patched[0x134:0x14D]) - 25) & 0xFF
global_checksum = (sum(patched) - patched[0x14E] - patched[0x14F]) & 0xFFFF
assert patched[0x14D] == header
assert int.from_bytes(patched[0x14E:0x150], "big") == global_checksum

allowed = [
    (0x02A60C, 61 * 47),
    (0x02B140, 38 * 9),
    (0x02B297, 30 * 47),
    (0x02B81A, 24 * 9),
    (0x02DA2B, 3),
    (0x02DC37, 2),
    (0x08018D, 5),
    (0x082000, 28),
    (0x0164CD, 2),
    (0x0164F1, 2),
    (0x0164F5, 2),
    (0x0164F7, 2),
    (0x017E00, 50),
    (0x0399BA, 67 * 2),
    (0x039A40, 0x03B775 - 0x039A40),
    (0x03ED57, 1),
    (0x0FBF93, 1),
    (0x035ECE, 2),
    (0x035F82, 7),
    (0x036331, 7),
    (0x036E58, 7),
    (0x42E2F, 3),
    (0x42E5D, 3),
    (0x42EA5, 3),
    (0x42F5E, 3),
    (0x42FC9, 3),
    (0x430F6, 3),
    (0x43125, 3),
    (0x43317, 3),
    (0x4339A, 3),
    (0x434BD, 3),
    (0x43DBE, 7),
    (0x43DD4, 7),
    (0x9796F, 3),
    (0x97F92, 0x3D),
    (0x56940, 5),
    (0x56955, 5),
    (0x57EEB, 12),
    (0x70BD3, 3),
    (0x73F7E, 23),
    (0x2BE2, 1),
    (0x2C13, 1),
    (0x95666, 1),
    (0x95669, 2),
    (0x9252A, 45),
    (0x93FEB, 14),
    (0x90FC3, 11),
    (0x90FD0, 11),
    (0x91B1F, 11),
    (0x91B2C, 11),
    (0xABB73, 360),
    (0xAAAA7, 180),
    (0x2B297, 1552),
    (0x2BD04, 235),
    (0x2A03D, 2),
    (0x2A21B, 2),
    (0x180000, 0x8000),
    (0x14D, 3),
]
trainer_pointers, trainer_data, changed_trainers = rebuilt_2020_japanese_trainers(
    stock, english, reference
)
from port_clock_reset import apply_clock_reset
from port_battle_bugfixes import apply_battle_bugfixes
from port_gym_rematches import apply_gym_rematches
from port_misc_fixes import apply_misc_fixes
from port_restored_sprites import apply_restored_sprites
from port_dialogue_updates import apply_dialogue_updates
from port_item_attributes import apply_item_attributes
from port_remaining_features import apply_remaining_features
from fix_requested_issues import apply_requested_fixes
from fix_held_item_stat_cap import apply_held_item_stat_cap_fix
probe = bytearray(stock)
# The builder installs these ten evolution changes before feature modules.
# Seed that verified state so Moon Ball can inspect the complete RC1 table.
for offset, before, after in (
    (0x42E2F, '0352ba', '0208ba'), (0x42E5D, '03ff41', '020841'),
    (0x42EA5, '03ff44', '02a944'), (0x42F5E, '03ff4c', '02a94c'),
    (0x42FC9, '0352c7', '0218c7'), (0x430F6, '03ff5e', '02085e'),
    (0x43125, '038fd0', '02a9d0'), (0x43317, '0397e6', '0218e6'),
    (0x4339A, '038fd4', '0222d4'), (0x434BD, '03ace9', '0217e9'),
):
    assert stock[offset:offset+3] == bytes.fromhex(before)
    probe[offset:offset+3] = bytes.fromhex(after)
    assert patched[offset:offset+3] == probe[offset:offset+3]
feature_ranges = []
for feature in (apply_clock_reset, apply_battle_bugfixes, apply_gym_rematches, apply_misc_fixes, apply_restored_sprites, apply_dialogue_updates, apply_item_attributes, apply_remaining_features, apply_requested_fixes, apply_held_item_stat_cap_fix):
    for start, size, label in feature(stock, english, reference, probe):
        allowed.append((start, size))
        feature_ranges.append((start, size, label))
# Compare after layering the four requested corrections; preserve checks for
# every byte of the original features, including overlapping correction sites.
for start, size, label in feature_ranges:
    assert patched[start:start+size] == probe[start:start+size], label
assert changed_trainers == 212
assert patched[0x399BA:0x39A40] == trainer_pointers
assert patched[0x39A40:0x39A40 + len(trainer_data)] == trainer_data
changed = [i for i, (a, b) in enumerate(zip(stock, patched)) if a != b]
assert all(any(start <= i < start + size for start, size in allowed) for i in changed)
print("header_checksum_ok", True)
print("global_checksum_ok", True)
print("changed_bytes", len(changed))
print("outside_allowed_ranges", 0)
