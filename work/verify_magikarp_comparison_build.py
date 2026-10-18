"""Verify the one-byte repair and rejection without partial mutation."""
from pc_env import workspace
from pathlib import Path
from fix_magikarp_comparison import apply_magikarp_comparison_fix, ENTRY, PATCH, RC1, CORRECT

ROOT = workspace()


def inputs():
    return tuple((ROOT / path).read_bytes() for path in (
        'Pocket Monsters - Crystal Version (Japan).gbc',
        'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc',
        'work/perfect_crystal_ue_patched.gbc'))


def main():
    original, english, perfect = inputs()
    port = bytearray(original)
    # Minimal valid pre-state: only the earlier released-2020 comparison port.
    # The fix intentionally neither requires nor rewrites unrelated features.
    port[ENTRY:ENTRY + len(RC1)] = RC1
    before = bytes(port)
    ranges = apply_magikarp_comparison_fix(original, english, perfect, port)
    assert ranges == [(PATCH, 1, 'correct_unsigned_16bit_magikarp_length_comparison')]
    assert port[ENTRY:ENTRY + len(CORRECT)] == CORRECT
    assert [i for i, (a, b) in enumerate(zip(before, port)) if a != b] == [PATCH]
    cases = []
    for label in ('missing_rc1', 'already_fixed', 'changed_helper', 'changed_caller', 'wrong_original'):
        output = bytearray(before)
        jp = original
        if label == 'missing_rc1':
            output = bytearray(original)
        elif label == 'already_fixed':
            output = bytearray(port)
        elif label == 'changed_helper':
            output[ENTRY] ^= 1
        elif label == 'changed_caller':
            output[0xFBDA6] ^= 1
        else:
            jp = original[:-1] + bytes((original[-1] ^ 1,))
        snapshot = bytes(output)
        try:
            apply_magikarp_comparison_fix(jp, english, perfect, output)
        except AssertionError:
            assert bytes(output) == snapshot
        else:
            raise AssertionError(('unsafe acceptance', label))
        cases.append(label)
    print('magikarp_comparison_build_passed', 'one-byte repair;', len(cases), 'safe rejections')


if __name__ == '__main__':
    main()
