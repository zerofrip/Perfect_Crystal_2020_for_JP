"""Actual command-entry CPU tests for all 13 stages, 7 stats and both sides.

ROM routines are not stubbed. The fixture supplies battle RAM, a return
sentinel and no active status ailments. All 1/2-stage entry points execute
their original checks and (for physical stats) the real stat recalculation.
"""
from pc_env import workspace
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from fix_sharp_stat_drop import (OFFSET,HOOK_OFFSET,CAVE_OFFSET,HOOK,CAVE,
                                 STAT_BLOCK,apply_sharp_stat_drop_fix)

ROOT=workspace()
STATS=('attack','defense','speed','sp_attack','sp_defense','accuracy','evasion')
BLOCKS=('miss','effect_failed','mist','substitute','flying','underground')
CASES=[(side,stat,amount,stage,'none') for side in (0,1) for stat in range(7)
       for amount in (1,2) for stage in range(1,14)]
CASES += [(side,stat,amount,7,block) for side in (0,1) for stat in range(7)
          for amount in (1,2) for block in BLOCKS]
CASES += [(side,stat,amount,stage,'stat_one') for side in (0,1) for stat in range(5)
          for amount in (1,2) for stage in range(1,14)]

if len(sys.argv)==1:
    def run(case):
        process=subprocess.run([sys.executable,__file__,*(str(x) for x in case)],
                               check=True,capture_output=True,text=True,timeout=30)
        return json.loads(process.stdout.splitlines()[-1])
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for index,result in enumerate(pool.map(run,CASES),1):
            results.append(result)
            if index==1 or index%100==0:
                print('sharp_stat_drop_cpu_progress',index,'/',len(CASES),flush=True)
    assert len({result['input_sha256'] for result in results})==1, 'input ROM changed during the run'
    assert len({result['tested_sha256'] for result in results})==1, 'tested ROM differs between cases'
    (ROOT/'work/sharp_stat_drop_cpu_results.json').write_text(json.dumps(results,indent=2)+'\n')
    print('sharp_stat_drop_cpu_passed',len(results),
          'cases; 364 stage cases, 168 preserved block cases, 260 stat-one failures')
    print('input_sha256',results[0]['input_sha256'],'mode',results[0]['patch_mode'])
    raise SystemExit

from pyboy import PyBoy
side,stat,amount,stage=map(int,sys.argv[1:5]);block=sys.argv[5]
control=sys.argv[6:]==['--control-before-rollback']
assert not sys.argv[6:] or control
if control:assert (side,stat,amount,stage,block)==(0,0,2,3,'stat_one')
original=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
english=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
perfect=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
input_rom=(ROOT/'work/development_only_jp_partial.gbc').read_bytes()
input_sha256=hashlib.sha256(input_rom).hexdigest()
rom=bytearray(input_rom)
rc1=bytes.fromhex('fa00c7e6f0280405280104f0e4a72823')
fixed=bytes.fromhex('fa00c7e6f0280405200104f0e4a72823')
assert len(rom)==0x200000
if control:
    assert rom[0x36305:0x36305+len(fixed)]==fixed
    assert rom[HOOK_OFFSET:HOOK_OFFSET+len(STAT_BLOCK)]==STAT_BLOCK
    assert rom[CAVE_OFFSET:CAVE_OFFSET+len(CAVE)]==bytes(len(CAVE))
    patch_mode='rollback_bug_control_rom_unchanged'
elif rom[0x36305:0x36305+len(rc1)]==rc1:
    apply_sharp_stat_drop_fix(original,english,perfect,rom)
    patch_mode='rc1_fixed_in_memory'
else:
    assert rom[0x36305:0x36305+len(fixed)]==fixed, 'expected RC1 or corrected stat-drop context'
    if rom[HOOK_OFFSET:HOOK_OFFSET+len(STAT_BLOCK)]==STAT_BLOCK:
        # The first RC2 candidate already corrected the branch. Reconstruct
        # the module's RC1 preimage in memory, then apply both corrections.
        rom[OFFSET]=0x28
        apply_sharp_stat_drop_fix(original,english,perfect,rom)
        patch_mode='branch_fixed_rollback_added_in_memory'
    else:
        assert rom[HOOK_OFFSET:HOOK_OFFSET+len(HOOK)]==HOOK
        assert rom[CAVE_OFFSET:CAVE_OFFSET+len(CAVE)]==CAVE
        assert rom==input_rom, 'integrated fixed ROM must remain unchanged'
        patch_mode='integrated_fixed_rom_unchanged'
tested_sha256=hashlib.sha256(rom).hexdigest()
def word(offset):return int.from_bytes(rom[offset:offset+2],'little')
def battle_var(which):
    pair=word(0x39b7+which*2)
    return word(0x3a0b+rom[pair+side]*2)

em=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
em.tick(600,render=False,sound=False)
r=em.register_file
for lo,hi in ((0xc600,0xc710),(0xd230,0xd260)):
    for address in range(lo,hi):em.memory[address]=0
em.memory[0xffff]=em.memory[0xff0f]=0
em.memory[0x2000]=em.memory[0xff9d]=13
em.memory[0xffe4]=side
em.memory[0xc2dc]=0;em.memory[0xcfb4]=0
em.memory[0xc6c0:0xc6c8]=[7]*8
em.memory[0xc6c8:0xc6d0]=[7]*8
target=0xc6c8 if side==0 else 0xc6c0
other=0xc6c0 if side==0 else 0xc6c8
em.memory[target+stat]=stage
for base in (0xc6aa,0xc6b5,0xc636,0xd24b):
    em.memory[base:base+10]=[0,120]*5
MULTIPLIERS=((25,100),(28,100),(33,100),(40,100),(50,100),(66,100),
             (1,1),(15,10),(2,1),(25,10),(3,1),(35,10),(4,1))
def scaled(level):
    n,d=MULTIPLIERS[level-1]
    return 120*n//d
current=0xd24b if side==0 else 0xc636
if stat<5:
    value=1 if block=='stat_one' else scaled(stage)
    em.memory[current+2*stat:current+2*stat+2]=[value>>8,value&255]
em.memory[battle_var(13)]=(0x12 if amount==1 else 0x3a)+stat
if block=='miss':em.memory[0xc65b]=1
elif block=='effect_failed':em.memory[0xc701]=1
elif block=='mist':em.memory[battle_var(8)]=2
elif block=='substitute':em.memory[battle_var(8)]=16
elif block=='flying':em.memory[battle_var(7)]=32
elif block=='underground':em.memory[battle_var(7)]=64
else:assert block in ('none','stat_one')
r.SP=0xcffe;em.memory[0xcffe:0xd000]=[0,1]
r.PC=(0x62ad if amount==1 else 0x62c9)+stat*4


def done(_):
    expected=max(1,stage-amount) if block=='none' else stage
    if control:expected=2  # The old failure rollback incorrectly loses one stage.
    result={'side':side,'stat':STATS[stat],'amount':amount,'stage_before':stage,
            'block':block,'stage_after':em.memory[target+stat],
            'failed_message':em.memory[0xc702],'attack_missed':em.memory[0xc65b],
            'input_sha256':input_sha256,'tested_sha256':tested_sha256,
            'patch_mode':patch_mode}
    expected_message=(3 if block=='stat_one' else
                      ((2 if block=='mist' else 1) if block!='none' else (3 if stage==1 else 0)))
    expected_miss=int(block!='none' or stage==1)
    checks=[result['stage_after']==expected,result['failed_message']==expected_message,
            result['attack_missed']==expected_miss,em.memory[0xffe4]==side,
            list(em.memory[other:other+8])==[7]*8,
            all(em.memory[target+i]==(expected if i==stat else 7) for i in range(8)),
            r.SP==0xd000,em.memory[0xff9d]==13]
    if stat<5:
        expected_value=1 if block=='stat_one' else scaled(expected)
        actual_value=em.memory[current+2*stat]*256+em.memory[current+2*stat+1]
        result['calculated_stat']=actual_value
        checks.append(actual_value==expected_value)
        checks.append(all(em.memory[current+2*i]*256+em.memory[current+2*i+1]==120
                          for i in range(5) if i!=stat))
    if block=='stat_one' and stage>1:
        # TryLowerStat preserves BC and returns with DE selecting the base
        # stat. The wrapper must also restore the original stage pointer.
        result['registers']={name:getattr(r,name) for name in ('A','F','B','C','D','E','HL')}
        checks.extend((r.A==1,r.F==0,r.B==max(1,stage-amount),r.C==stat,
                       (r.D<<8|r.E)==(0xc6b5 if side==0 else 0xc6aa)+2*stat,
                       r.HL==target+stat))
    result['passed']=all(checks)
    if not result['passed']:result['checks']=checks
    if control:
        result['control_expectation']='prior bug loses one stage despite stat-one failure'
        (ROOT/'work/sharp_stat_drop_rollback_control.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    os._exit(0 if result['passed'] else 1)


em.hook_register(0,0x100,done,None)
em.tick(1,render=False,sound=False)
raise RuntimeError(('CPU sentinel not reached',side,stat,amount,stage,block,hex(r.PC)))
