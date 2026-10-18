"""Build this bounded port in isolation; verify changed ranges and fail-closed."""
from pc_env import workspace
from pathlib import Path
import json
from port_battle_bugfixes import apply_battle_bugfixes

ROOT=workspace()
original=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
stock=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
perfect=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
output=bytearray(original)
ranges=apply_battle_bugfixes(original,stock,perfect,output)
allowed={i for offset,size,_ in ranges for i in range(offset,offset+size)}
assert len(allowed)==sum(size for _,size,_ in ranges), 'overlapping ranges'
assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(original,output)))
assert all(output[a:a+n] != original[a:a+n] for a,n,_ in ranges)
bad=bytearray(original)
bad[0]^=1
try:
    apply_battle_bugfixes(bad,stock,perfect,bytearray(original))
except AssertionError:
    pass
else:
    raise AssertionError('unknown input accepted')
conflict=bytearray(original)
conflict[0x37f33]=1
try:
    apply_battle_bugfixes(original,stock,perfect,conflict)
except AssertionError:
    pass
else:
    raise AssertionError('conflicting edit accepted')
(ROOT/'work/battlefix_isolated.gbc').write_bytes(output)
(ROOT/'work/battlefix_ranges.json').write_text(json.dumps(ranges,indent=2)+'\n')
print('battlefix binary checks passed:',len(ranges),'ranges,',sum(a!=b for a,b in zip(original,output)),'changed bytes')
