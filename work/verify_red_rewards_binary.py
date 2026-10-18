"""Verify Red's actual Japanese map object and postbattle reward script."""
from pc_env import workspace
from pathlib import Path

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
port = (root / 'work/development_only_jp_partial.gbc').read_bytes()
perfect = (root / 'work/perfect_crystal_ue_patched.gbc').read_bytes()

person = bytes.fromhex('060e0d0700ffff8000ad4b6207')
assert stock[0x70C23:0x70C23 + len(person)] == person
assert stock.count(person) == 1
assert 0x70000 + int.from_bytes(person[9:11], 'little') - 0x4000 == 0x70BAD
assert stock[0x70BCE:0x70BDA] == bytes.fromhex('0f33006d028a0f0f32008a1e')

flags = (0x2CD, 0x2BC, 0x2B9, 0x2B7, 0x2CF)
ue_rewards = b''.join(bytes((0x33, f & 0xff, f >> 8)) for f in flags)
assert perfect[0x18C629:0x18C629 + 15] == ue_rewards
assert port[0x70BD3:0x70BD6] == bytes.fromhex('037e7f')
assert port[0x73F7E:0x73F7E + 23] == ue_rewards + bytes.fromhex('8a0f0f320003d84b')
assert port[0x70BD6:0x70BE1] == stock[0x70BD6:0x70BE1]
print('red_map_object_unique', True)
print('red_rewards_match_2020', len(flags))
print('red_japanese_script_tail_preserved', True)
