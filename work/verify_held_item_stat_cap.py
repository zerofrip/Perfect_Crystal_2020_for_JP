"""Build the requested correction on immutable RC2; check writes and refusals."""
from pc_env import workspace
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from fix_held_item_stat_cap import apply_held_item_stat_cap_fix, SPECIES_2020

ROOT = workspace()
RC2_SHA256 = '96b08ba49bc42096b2156a6795c86f1b47f40afe8786a6569da764d8c493163c'


def inputs():
    original = (ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
    english = (ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
    perfect = (ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
    sys.path.insert(0, str(ROOT/'lazy_ips'))
    from lazy_ips.patch import ips
    output = bytearray(original)
    patch = (ROOT/'work/release/Perfect_Crystal_2020_Japanese_RC2.ips').read_bytes()
    for record in ips.read_patch(BytesIO(patch)):
        assert record.offset+len(record.data) <= len(output)
        output[record.offset:record.offset+len(record.data)] = record.data
    assert sha256(output).hexdigest() == RC2_SHA256
    return original, english, perfect, output


def main():
    original, english, perfect, base = inputs()
    output = bytearray(base)
    ranges = apply_held_item_stat_cap_fix(original, english, perfect, output)
    allowed = {i for start, size, _ in ranges for i in range(start, start+size)}
    assert len(allowed) == sum(size for _, size, _ in ranges)
    changed = {i for i, (a, b) in enumerate(zip(base, output)) if a != b}
    assert changed <= allowed
    assert output[0x37fa0:0x37fca] == base[0x37fa0:0x37fca], 'sharp wrapper changed'
    assert output[0xff80:0x10000] == base[0xff80:0x10000], 'Moon Ball changed'
    assert output[0x3534d:0x35378] == base[0x3534d:0x35378], 'Truncate changed'
    assert output[0x3560a:0x3560d] == base[0x3560a:0x3560d], 'confusion caller changed'
    refusals = []

    def refuse(name, source, candidate):
        before = bytes(candidate)
        try:
            apply_held_item_stat_cap_fix(source, english, perfect, candidate)
        except AssertionError:
            assert candidate == before, ('non-atomic rejection', name)
            refusals.append(name)
        else:
            raise AssertionError(('unsafe acceptance', name))

    unknown = bytearray(original); unknown[0] ^= 1
    refuse('unknown_original', unknown, bytearray(base))
    refuse('unported_input', original, bytearray(original))
    refuse('duplicate_application', original, bytearray(output))
    for name, offset in (('altered_species_cap', 0x37f70),
                         ('altered_metal_cap', 0x37f82),
                         ('altered_metal_arithmetic', 0x352cb),
                         ('occupied_wrapper', 0x37fca),
                         ('altered_player_call', 0x3533f),
                         ('altered_enemy_call', 0x35453),
                         ('altered_shared_truncate', 0x3534d),
                         ('altered_confusion_call', 0x3560a)):
        candidate = bytearray(base); candidate[offset] ^= 1
        refuse(name, original, candidate)
    duplicate = bytearray(base)
    duplicate[0x190800:0x190800+len(SPECIES_2020)] = SPECIES_2020
    refuse('ambiguous_cap_anchor', original, duplicate)
    report = {'passed': True, 'ranges': ranges, 'changed_bytes': len(changed),
              'refusal_cases': refusals, 'input_sha256': RC2_SHA256,
              'actual_tested_sha256': sha256(output).hexdigest()}
    (ROOT/'work/held_item_stat_cap_isolated.gbc').write_bytes(output)
    (ROOT/'work/held_item_stat_cap_binary_results.json').write_text(json.dumps(report, indent=2)+'\n')
    print('held_item_stat_cap_binary_passed', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
