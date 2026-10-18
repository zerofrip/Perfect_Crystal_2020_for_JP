"""Require the exact RC2 baseline plus only the requested held-item fix."""
from hashlib import sha256
import json
from pathlib import Path
import sys

from pc_env import workspace
from fix_held_item_stat_cap import apply_held_item_stat_cap_fix

WORK=workspace()/'work'
ROOT=workspace()
baseline=(WORK/'rc2_reference.gbc').read_bytes()
assert sha256(baseline).hexdigest()=='96b08ba49bc42096b2156a6795c86f1b47f40afe8786a6569da764d8c493163c'
stock=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
english=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
reference=(WORK/'perfect_crystal_ue_patched.gbc').read_bytes()
rom_arg = Path(sys.argv[1]) if len(sys.argv) == 2 else WORK / 'development_only_jp_partial.gbc'
actual = rom_arg.read_bytes()
expected=bytearray(baseline)
ranges=apply_held_item_stat_cap_fix(stock,english,reference,expected)
expected[0x14D]=(-sum(expected[0x134:0x14D])-25)&255
checksum=(sum(expected)-expected[0x14E]-expected[0x14F])&65535
expected[0x14E:0x150]=checksum.to_bytes(2,'big')
assert actual==expected, 'RC3 differs from the expected held-item correction'
changed=[i for i,(a,b) in enumerate(zip(baseline,actual)) if a!=b]
allowed=ranges+[(0x14D,3,'checksums')]
assert all(any(start<=i<start+size for start,size,_ in allowed) for i in changed)
result={'base_rc2_sha256':sha256(baseline).hexdigest(),
        'output_sha256':sha256(actual).hexdigest(),
        'changed_bytes_from_rc2':len(changed),
        'changed_bytes_excluding_checksums':sum(not 0x14D<=i<0x150 for i in changed),
        'outside_requested_ranges':0,'ranges':ranges,'passed':True}
(WORK/'rc3_delta_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
