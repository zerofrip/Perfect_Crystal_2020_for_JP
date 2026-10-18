"""Check patch boundaries and atomic refusal against the stable released RC1."""
from pc_env import workspace
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from fix_moon_ball import (apply_moon_ball_fix, CAVE, ENTRY, JP_EVOS,
                           corrected_routine, moon_targets, TARGETS)

ROOT = workspace()
RC1_SHA256 = 'bdb8b08177dc6e5a549c5d3ed2499a9835ae7c7c01ad0acafda659072335805e'


def inputs():
    original = (ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
    english = (ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
    perfect = (ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
    sys.path.insert(0, str(ROOT/'lazy_ips'))
    from lazy_ips.patch import ips
    base = bytearray(original)
    patch = (ROOT/'work/release/Perfect_Crystal_2020_Japanese_RC1.ips').read_bytes()
    for record in ips.read_patch(BytesIO(patch)):
        assert record.offset+len(record.data) <= len(base)
        base[record.offset:record.offset+len(record.data)] = record.data
    assert sha256(base).hexdigest() == RC1_SHA256
    return original, english, perfect, base


def main():
    original, english, perfect, base = inputs()
    output = bytearray(base)
    ranges = apply_moon_ball_fix(original, english, perfect, output)
    allowed = {i for start, size, _ in ranges for i in range(start, start+size)}
    assert len(allowed) == sum(size for _, size, _ in ranges)
    changes = {i for i, (a, b) in enumerate(zip(base, output)) if a != b}
    assert changes <= allowed
    assert moon_targets(output) == TARGETS
    assert output[JP_EVOS:0x44000] == base[JP_EVOS:0x44000]
    refusal_cases = []

    def refused(name, supplied_original, candidate):
        snapshot = bytes(candidate)
        try:
            apply_moon_ball_fix(supplied_original, english, perfect, candidate)
        except AssertionError:
            assert candidate == snapshot, ('partial mutation after rejection', name)
            refusal_cases.append(name)
        else:
            raise AssertionError(('unsafe input accepted', name))

    unknown = bytearray(original); unknown[0] ^= 1
    refused('unknown_original', unknown, bytearray(base))
    refused('unported_output', original, bytearray(original))
    refused('double_application', original, bytearray(output))
    conflict = bytearray(base); conflict[CAVE] = 1
    refused('occupied_output_cave', original, conflict)
    conflict = bytearray(base); conflict[ENTRY+8] ^= 1
    refused('changed_entry_preimage', original, conflict)
    conflict = bytearray(base); conflict[0x3019] ^= 1
    refused('changed_bank_reader', original, conflict)
    conflict = bytearray(base); conflict[JP_EVOS] ^= 1
    refused('changed_evolution_pointer', original, conflict)
    conflict = bytearray(base); conflict[0x42e30] = 0x18
    refused('missing_ported_moon_evolution', original, conflict)
    conflict = bytearray(base)
    conflict[0x190000:0x190000+53] = base[ENTRY:ENTRY+53]
    refused('ambiguous_entry_anchor', original, conflict)
    report = {'ranges': ranges, 'changed_bytes': len(changes),
              'routine_bytes': len(corrected_routine()), 'moon_targets': TARGETS,
              'refusal_cases': refusal_cases, 'baseline_sha256': RC1_SHA256}
    (ROOT/'work/moon_ball_fix_isolated.gbc').write_bytes(output)
    (ROOT/'work/moon_ball_fix_binary_results.json').write_text(json.dumps(report, indent=2)+'\n')
    print('moon_ball_fix_binary_passed', json.dumps(report))


if __name__ == '__main__':
    main()
