"""Independent read-only review of the held-cap patch and its edit boundary."""
from pc_env import workspace
from hashlib import sha256
import json
from pathlib import Path
from fix_held_item_stat_cap import apply_held_item_stat_cap_fix

ROOT=workspace()
j=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
u=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
p=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
path=ROOT/'work/rc2_reference.gbc'
rc2=path.read_bytes()
assert sha256(rc2).hexdigest()=='96b08ba49bc42096b2156a6795c86f1b47f40afe8786a6569da764d8c493163c'
out=bytearray(rc2)
ranges=apply_held_item_stat_cap_fix(j,u,p,out)
allowed={i for offset,size,_ in ranges for i in range(offset,offset+size)}
assert sum(size for _,size,_ in ranges)==72
assert len(ranges)==8
assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(rc2,out)))
assert rc2[0x37fa0:0x37fca]==out[0x37fa0:0x37fca]  # sharp rollback wrapper
assert rc2[0x3534d:0x35378]==out[0x3534d:0x35378]  # shared Truncate
assert out[0x3560a:0x3560d]==rc2[0x3560a:0x3560d]==bytes.fromhex('cd4d53')
for start in (0x3533f,0x35453):
    assert out[start:start+3]==bytes.fromhex('cdca7f')
    assert out[start+3:start+7]==rc2[start+3:start+7]
    assert out[start+7:start+10]==bytes(3)
    assert out[start+10:start+14]==rc2[start+10:start+14]
assert out[0x37fca:0x37fd2]==bytes.fromhex('e5cdb152e1c34d53')
# JR C destinations land at the intended whole-word loads.
assert 0x37f77+2+out[0x37f78]==0x37f7e
assert out[0x37f7e:0x37f81]==bytes.fromhex('21e703')
assert 0x37f85+2+out[0x37f86]==0x37f8c
assert out[0x37f8c:0x37f8f]==bytes.fromhex('01e703')
assert out[0x352cb:0x352d7]==bytes.fromhex('6069cb3ccb1d09444dc3827f')
for offset in (0x37fca,0x3533f,0x3545a):
    collision=bytearray(rc2)
    collision[offset]^=1
    before=bytes(collision)
    try:apply_held_item_stat_cap_fix(j,u,p,collision)
    except AssertionError:pass
    else:raise AssertionError('expected preimage refusal')
    assert collision==before
assert path.read_bytes()==rc2
report={'input_sha256':sha256(rc2).hexdigest(),'ranges':ranges,
        'range_count':len(ranges),'declared_bytes':72,
        'actual_changed_bytes':sum(a!=b for a,b in zip(rc2,out)),
        'branch_destinations':['0x37f7e','0x37f8c'],
        'sharp_wrapper_unchanged':True,'confusion_unchanged':True,
        'source_rom_file_unchanged':True,'collision_refusal_atomic':True}
(ROOT/'work/held_cap_audit_review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
