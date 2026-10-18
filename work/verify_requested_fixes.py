"""Verify the complete RC1-to-RC2 delta is exactly the four requested fixes."""
from hashlib import sha256
import json
import sys
from pathlib import Path

from pc_env import workspace
from fix_requested_issues import apply_requested_fixes

WORK = workspace() / 'work'
ROOT = workspace()
baseline = (WORK / 'rc1_reference.gbc').read_bytes()
assert sha256(baseline).hexdigest() == 'bdb8b08177dc6e5a549c5d3ed2499a9835ae7c7c01ad0acafda659072335805e'
stock = (ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
english = (ROOT / 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
reference = (WORK / 'perfect_crystal_ue_patched.gbc').read_bytes()
actual_path = Path(sys.argv[1]) if len(sys.argv) == 2 else WORK / 'rc2_reference.gbc'
actual = actual_path.read_bytes()
expected = bytearray(baseline)
ranges = apply_requested_fixes(stock, english, reference, expected)
expected[0x14D] = (-sum(expected[0x134:0x14D]) - 25) & 0xFF
checksum = (sum(expected) - expected[0x14E] - expected[0x14F]) & 0xFFFF
expected[0x14E:0x150] = checksum.to_bytes(2, 'big')
assert actual == expected, 'integrated ROM differs from the requested four corrections'
changed = [i for i, (a, b) in enumerate(zip(baseline, actual)) if a != b]
allowed = ranges + [(0x14D, 3, 'checksums')]
assert all(any(start <= i < start + size for start, size, _ in allowed) for i in changed)
# Independent checks of externally observable constants and comparison branch.
assert actual[0x6DE3:0x6DEA] == bytes.fromhex('6400400a400100')
assert actual[0xFBDF5:0xFBDFC] == bytes.fromhex('78bad8c079bbc9')
assert actual[0x3630D] == 0x20
assert actual[0xEF52:0xEF55] == bytes.fromhex('c3807f')
result = {
    'baseline_sha256': sha256(baseline).hexdigest(),
    'output_sha256': sha256(actual).hexdigest(),
    'changed_bytes_from_rc1': len(changed),
    'changed_bytes_excluding_checksums': sum(not 0x14D <= i < 0x150 for i in changed),
    'outside_requested_ranges': 0,
    'ranges': ranges,
    'passed': True,
}
(WORK / 'requested_fixes_verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
