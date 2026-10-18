from pc_env import workspace
from pathlib import Path
from port_clock_reset import apply_clock_reset, clock_reset_payload
ROOT=workspace()
original=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
english=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
perfect=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
output=bytearray(original)
ranges=apply_clock_reset(original,english,perfect,output)
payload,labels=clock_reset_payload()
covered=set()
for offset,size,_ in ranges:covered.update(range(offset,offset+size))
assert all(a==b or index in covered for index,(a,b) in enumerate(zip(original,output)))
rejections=0
for source,offset in [('original',0x648c),('perfect',0x6321),('output',0x7e82),('output',0x63dc)]:
    jp=bytearray(original);patch=bytearray(perfect);result=bytearray(original)
    {'original':jp,'perfect':patch,'output':result}[source][offset]^=1
    before=bytes(result)
    try:
        apply_clock_reset(jp,english,patch,result)
    except AssertionError:
        assert result==before
        rejections+=1
    else:raise AssertionError((source,offset))
assert rejections==4
print('clock_reset_payload_bytes',len(payload),'ranges',ranges,'labels', {k:f'{v:04x}' for k,v in labels.items()})
print('clock_reset_fail_closed_cases',rejections)
(ROOT/'work/clockreset_test.gbc').write_bytes(output)
