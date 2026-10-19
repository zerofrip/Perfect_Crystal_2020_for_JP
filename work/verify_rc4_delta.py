"""Require the exact RC3 baseline plus only the RC4 corrections.

An optional command-line argument names the ROM to verify; the historical
RC4 snapshot (rc4_reference.gbc) can be gated after RC5 made the development
ROM the RC5 output.  The default stays the current development ROM.
"""
from hashlib import sha256
import json
from pathlib import Path
import sys

from pc_env import workspace
from apply_rc4_corrections import apply_rc4_corrections

WORK = workspace() / 'work'
ROOT = workspace()
baseline = (WORK / 'rc3_reference.gbc').read_bytes()
assert sha256(baseline).hexdigest() == 'b6f6b73dc7e6d8f4d3223b398fb1202519efae0c0e36959ab7ac43cb8e5a4c21'
stock = (ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
english = (ROOT / 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
reference = (WORK / 'perfect_crystal_ue_patched.gbc').read_bytes()
rom_arg = Path(sys.argv[1]) if len(sys.argv) == 2 else WORK / 'development_only_jp_partial.gbc'
actual = rom_arg.read_bytes()
expected = bytearray(baseline)
ranges = apply_rc4_corrections(stock, english, reference, expected)
expected[0x14D] = (-sum(expected[0x134:0x14D]) - 25) & 0xFF
checksum = (sum(expected) - expected[0x14E] - expected[0x14F]) & 0xFFFF
expected[0x14E:0x150] = checksum.to_bytes(2, 'big')
assert actual == expected, 'RC4 differs from the expected correction layer'
changed = [i for i, (a, b) in enumerate(zip(baseline, actual)) if a != b]
allowed = ranges + [(0x14D, 3, 'checksums')]
assert all(any(start <= i < start + size for start, size, _ in allowed) for i in changed)
result = {
    'base_rc3_sha256': sha256(baseline).hexdigest(),
    'verified_rom': rom_arg.name,
    'output_sha256': sha256(actual).hexdigest(),
    'changed_bytes_from_rc3': len(changed),
    'changed_bytes_excluding_checksums': sum(not 0x14D <= i < 0x150 for i in changed),
    'outside_requested_ranges': 0,
    'ranges': ranges,
    'passed': True,
}
(WORK / 'rc4_delta_verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
