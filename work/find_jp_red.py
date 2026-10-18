"""Locate the original Red party using its unique battle data, not name text."""
from pc_env import workspace
from pathlib import Path

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
baseline = (root / 'work/pokekuristaru_rgbds_history.gbc').read_bytes()
party = baseline[0x3B9A1:0x3B9C6]
assert len(party) == 37
positions = []
start = 0x38000
while True:
    offset = stock.find(party, start, 0x3C000)
    if offset < 0:
        break
    positions.append(offset)
    start = offset + 1
print('red_party_offsets', [f'{offset:06x}' for offset in positions])
red_group_start = positions[0] - 5
pointer = (red_group_start - 0x38000 + 0x4000).to_bytes(2, 'little')
pointer_offsets = []
start = 0x38000
while True:
    offset = stock.find(pointer, start, 0x3C000)
    if offset < 0:
        break
    pointer_offsets.append(offset)
    start = offset + 1
print('red_group_start', f'{red_group_start:06x}',
      'pointer_occurrences', [f'{offset:06x}' for offset in pointer_offsets])
reference = (root / 'work/perfect_crystal_ue_patched.gbc').read_bytes()
reference_needle = bytes.fromhex('91848350')
reference_positions = []
start = 0x38000
while True:
    offset = reference.find(reference_needle, start)
    if offset < 0:
        break
    reference_positions.append(offset)
    start = offset + 1
print('reference_red_offsets', [f'{offset:06x}' for offset in reference_positions])
ref_red_pointer = (0x3BA0A - 0x38000 + 0x4000).to_bytes(2, 'little')
ref_pointer_positions = []
start = 0x38000
while True:
    offset = reference.find(ref_red_pointer, start, 0x3C000)
    if offset < 0:
        break
    ref_pointer_positions.append(offset)
    start = offset + 1
print('reference_red_pointer_occurrences', [f'{offset:06x}' for offset in ref_pointer_positions])
english = (root / 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
english_needle = bytes.fromhex('91848350015119cc625557')
english_positions = []
start = 0x38000
while True:
    offset = english.find(english_needle, start, 0x3C000)
    if offset < 0:
        break
    english_positions.append(offset)
    start = offset + 1
print('english_stock_red_offsets', [f'{offset:06x}' for offset in english_positions])
if len(english_positions) == 1:
    english_pointer = (english_positions[0] - 0x38000 + 0x4000).to_bytes(2, 'little')
    pointer_positions = []
    start = 0x38000
    while True:
        offset = english.find(english_pointer, start, 0x3C000)
        if offset < 0:
            break
        pointer_positions.append(offset)
        start = offset + 1
    print('english_stock_red_pointer_occurrences', [f'{offset:06x}' for offset in pointer_positions])
