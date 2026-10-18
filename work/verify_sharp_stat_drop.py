"""Verify the branch correction and exact-stage rollback wrapper."""
from pc_env import workspace
from pathlib import Path
import sys
from fix_sharp_stat_drop import (OFFSET,HOOK_OFFSET,CAVE_OFFSET,HOOK,CAVE,
                                 STAT_BLOCK,apply_sharp_stat_drop_fix)

ROOT=workspace()
j=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
u=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
p=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
if len(sys.argv)>1:
    out=Path(sys.argv[1]).read_bytes()
    assert out[0x36305:0x36310]==bytes.fromhex('fa00c7e6f0280405200104')
    assert out[OFFSET]==0x20
    assert out[HOOK_OFFSET:HOOK_OFFSET+len(HOOK)]==HOOK
    assert out[CAVE_OFFSET:CAVE_OFFSET+len(CAVE)]==CAVE
    print('sharp_stat_drop_integrated_opcode_and_rollback_verified',hex(OFFSET))
else:
    # Accept the current integrated revision as a fixture source, then
    # reconstruct this module's three strict RC1 preimages in memory.
    rc1=bytearray((ROOT/'work/development_only_jp_partial.gbc').read_bytes())
    assert rc1[OFFSET] in (0x20,0x28)
    assert rc1[HOOK_OFFSET:HOOK_OFFSET+len(STAT_BLOCK)] in (
        STAT_BLOCK,HOOK+STAT_BLOCK[len(HOOK):])
    assert rc1[CAVE_OFFSET:CAVE_OFFSET+len(CAVE)] in (bytes(len(CAVE)),CAVE)
    rc1[OFFSET]=0x28
    rc1[HOOK_OFFSET:HOOK_OFFSET+len(STAT_BLOCK)]=STAT_BLOCK
    rc1[CAVE_OFFSET:CAVE_OFFSET+len(CAVE)]=bytes(len(CAVE))
    out=bytearray(rc1)
    ranges=apply_sharp_stat_drop_fix(j,u,p,out)
    assert ranges==[(OFFSET,1,'sharp_stat_drop_two_stages_floor_one'),
                    (HOOK_OFFSET,6,'sharp_stat_drop_preserve_stage_hook'),
                    (CAVE_OFFSET,42,'sharp_stat_drop_preserve_stage_routine')]
    allowed={i for offset,size,_ in ranges for i in range(offset,offset+size)}
    assert sum(size for _,size,_ in ranges)==49
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(rc1,out)))
    assert rc1[OFFSET]==0x28 and out[OFFSET]==j[OFFSET]==0x20
    assert out[HOOK_OFFSET:HOOK_OFFSET+len(HOOK)]==HOOK
    assert out[CAVE_OFFSET:CAVE_OFFSET+len(CAVE)]==CAVE
    # The real TryLowerStat body, failures and immunity checks are retained.
    assert out[0x36354:0x36464]==rc1[0x36354:0x36464]
    assert out[0x36338:HOOK_OFFSET]==rc1[0x36338:HOOK_OFFSET]
    cave_collision=bytearray(rc1);cave_collision[CAVE_OFFSET]=0x42
    body_collision=bytearray(rc1);body_collision[HOOK_OFFSET]=0x42
    for bad in (bytearray(j),bytearray(out),cave_collision,body_collision):
        snapshot=bytes(bad)
        try:apply_sharp_stat_drop_fix(j,u,p,bad)
        except AssertionError:pass
        else:raise AssertionError('missing RC1 preimage must be rejected')
        assert bad==snapshot
    print('sharp_stat_drop_3_ranges_49_bytes_and_atomic_preimages_verified')
