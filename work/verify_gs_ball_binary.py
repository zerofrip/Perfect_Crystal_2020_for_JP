"""Check both localized GS Ball scripts and their 2020 unlock condition."""
from pc_env import workspace
from pathlib import Path

root = workspace()
stock = (root / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
port = (root / 'work/development_only_jp_partial.gbc').read_bytes()
perfect = (root / 'work/perfect_crystal_ue_patched.gbc').read_bytes()

assert perfect[0x60F99:0x60F9C] == bytes.fromhex('314f07')
for offset, cave, resume, tail_end in ((0x56940, 0x57EEB, 0x6945, 0x56955),
                                       (0x56955, 0x57EF1, 0x695A, 0x569B5)):
    assert stock[offset:offset + 5] == bytes.fromhex('150b0f8600')
    assert stock[offset + 5:offset + 14] == bytes.fromhex('089769314003099769')
    assert port[offset:offset + 3] == bytes((3, cave & 0xff, 0x7e))
    assert port[cave:cave + 6] == bytes((0x31, 0x4f, 7, 3,
                                        resume & 0xff, resume >> 8))
    assert port[offset + 5:tail_end] == stock[offset + 5:tail_end]
    target = (offset - 0x54000 + 0x4000).to_bytes(2, 'little')
    pointers = [i for i in range(0x54000, 0x58000)
                if stock[i:i + 2] == target]
    expected_pointer = 0x57659 if offset == 0x56940 else 0x57661
    assert pointers == [expected_pointer]
    print('pointer_context', f'{expected_pointer:06x}',
          stock[expected_pointer - 5:expected_pointer + 4].hex(' '))
    # Both pointers sit in XY triggers at row 15, columns 6 and 7.
    assert stock[expected_pointer - 4:expected_pointer] == bytes(
        (0, 15, 6 if offset == 0x56940 else 7, 0))
    assert stock[expected_pointer + 2:expected_pointer + 4] == bytes(2)
    print('gs_ball_trigger', f'{offset:06x}', 'pointer_candidates',
          [f'{p:06x}' for p in pointers], 'japanese_tail_preserved', True)
