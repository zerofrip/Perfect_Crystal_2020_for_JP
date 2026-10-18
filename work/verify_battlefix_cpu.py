"""Execute mapped instructions in PyBoy; compare JP with released 2020 UE.

Each child exits from a CPU breakpoint before its synthetic stack/context
continues into the game. Ball tails test the changed comparisons; Fast Ball
uses the complete original function and real flee tables. Belly Drum uses
the real HP helpers and stops before animation or AttackUp2. Item cap tests
execute actual arithmetic, preserving released-2020 edge cases.
"""
from pc_env import workspace
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=workspace()
CASES = [f'fast:{s}:{b}' for s,b in ((81,20),(122,20),(104,20),(243,20),(25,20),(243,100))]
CASES += ['love:0:20','love:1:20','love:1:40','moon:8:20','moon:10:20','moon:8:100']
CASES += [f'species:{v}' for v in (300,600,120,512)]
CASES += [f'metal:{v}' for v in (100,200,255,600,999)]
CASES += [f'belly:{hp}' for hp in (49,50,51,100)]
CASES += [f'fish:{g}:{m}:{hi}:{lo}:{rng}' for g,m,hi,lo,rng in
          ((9,6,3,0,255),(9,1,3,0,255),(1,6,3,0,255),(9,6,5,3,20),
           (9,6,5,2,100),(9,6,5,1,100),(9,6,5,3,0))]
CASES += ['heal','mean:0:1','mean:1:0','pp:16:64:128:192:0',
          'pp:16:10:0:0:0','pp:16:0:1:0:0','pp:0:64:128:192:0','pp:0:0:0:1:0']

cached=json.loads((ROOT/'work/battlefix_cpu_results.json').read_text()) if sys.argv[1:]==['--check-results'] else None
if len(sys.argv)==1 or cached is not None:
    results=[]
    for case in CASES:
        actual=[]
        if cached is not None:
            actual=[next(x['result'] for x in cached if x['case']==case)]*2
        else:
            for version in ('jp','pc'):
                proc=subprocess.run([sys.executable,__file__,version,case],check=True,capture_output=True,text=True,timeout=30)
                actual.append(json.loads(proc.stdout.splitlines()[-1]))
        assert actual[0] == actual[1], (case,actual)
        p=case.split(':'); kind=p[0]; result=actual[0]
        if kind in ('fast','love','moon'):
            selector,rate=map(int,p[1:])
            factor=(1 if selector==25 else 4) if kind=='fast' else ((8 if selector else 1) if kind=='love' else (4 if selector==8 else 1))
            assert result=={'path':'return','catch_rate':min(rate*factor,255)},(case,result)
        elif kind=='belly':
            assert result=={'path':'attack' if int(p[1])>50 else 'failed','half_hp':50,'attack_stage':7},(case,result)
        elif kind=='heal':
            assert result=={'path':'return','flags':[0,0,254,254]},result
        elif kind=='mean':
            assert result['path']==('encourage' if int(p[1]) else 'fallback'),(case,result)
        elif kind=='pp':
            disabled,*pps=map(int,p[1:]); disabled_slot=(disabled>>4)-1
            usable=any((value&63)>0 for i,value in enumerate(pps) if i!=disabled_slot)
            assert result['path']==('return' if usable else 'struggle'),(case,result)
        results.append({'case':case,'result':actual[0]})
    if cached is None:
        (ROOT/'work/battlefix_cpu_results.json').write_text(json.dumps(results,indent=2)+'\n')
        print('battlefix_cpu_release_parity_passed',len(results),'cases /',2*len(results),'CPU executions')
    else:
        print('battlefix_cpu_saved_expectations_passed',len(results))
    raise SystemExit

from pyboy import PyBoy
version,case=sys.argv[1:]
parts=case.split(':');kind=parts[0]
jp=version=='jp'
rom=bytearray((ROOT/('work/battlefix_isolated.gbc' if jp else 'work/perfect_crystal_ue_patched.gbc')).read_bytes())
if kind=='fish':
    # Deterministic Random stub changes only this in-memory test fixture.
    rng=int(parts[5]);address=0x2f5e if jp else 0x2f8c
    rom[address:address+3]=bytes((0x3e,rng,0xc9))
emulator=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
emulator.tick(600,render=False,sound=False)
r=emulator.register_file
r.SP=0xcffe
emulator.memory[0xcffe:0xd000]=[0,1]
emulator.memory[0xffff]=0
emulator.memory[0xff0f]=0
bank=3 if kind in ('fast','love','moon') else (15 if kind in ('fish','pp') else (14 if kind in ('heal','mean') else 13))
emulator.memory[0x2000]=bank
emulator.memory[0xff9d]=bank

def report(label):
    if label=='return':
        assert r.SP==0xd000 and emulator.memory[0xff9d]==bank,(case,r.SP,emulator.memory[0xff9d])
    result={'path':label}
    if kind in ('fast','love','moon'):
        result['catch_rate']=r.B
    elif kind=='species':
        result['stat']=r.HL
    elif kind=='metal':
        result['stat']=(r.B<<8)|r.C
    elif kind=='belly':
        result['half_hp']=(r.B<<8)|r.C
        result['attack_stage']=emulator.memory[0xc6c0 if jp else 0xc6cc]
    elif kind=='heal':
        result['flags']=[emulator.memory[a] for a in
                         ((0xd2d9,0xd245,0xc661,0xc665) if jp else (0xd2a8,0xd214,0xc66d,0xc671))]
    print(json.dumps(result),flush=True)
    os._exit(0)

emulator.hook_register(0,0x100,lambda _:report('return'),None)
if kind=='fast':
    species,rate=map(int,parts[1:])
    emulator.memory[0xd235 if jp else 0xd204]=species
    r.B=rate
    r.PC=0x6fdd if jp else 0x6d63
elif kind=='love':
    gender,rate=map(int,parts[1:])
    r.SP=0xcffa
    emulator.memory[0xcffa:0xcffe]=[0,gender,0,rate]
    r.D=0
    r.PC=0x6fc7 if jp else 0x6d4d
elif kind=='moon':
    item,rate=map(int,parts[1:])
    # Point GetFarByte at a genuine item byte in the bank-$10 data. Starting
    # at its second read isolates the released constant change from the
    # release's pre-existing evolution-pointer behavior.
    offset=rom.find(bytes((item,)),0x40000,0x44000)
    assert offset>=0
    r.HL=offset%0x4000+0x4000
    r.B=rate
    anchor=bytes.fromhex('c53e10cd1930fe08' if jp else 'c53e10cd4d30fe08')
    r.PC=rom.index(anchor)%0x4000+0x4000
elif kind=='species':
    r.HL=int(parts[1])
    r.PC=0x53f1 if jp else 0x53f4
elif kind=='metal':
    value=int(parts[1]);r.B=value>>8;r.C=value&255
    r.PC=0x52cb if jp else 0x52c1
elif kind=='belly':
    hp=int(parts[1])
    base=0xc632 if jp else 0xc63c
    emulator.memory[base:base+4]=[0,hp,0,100]
    emulator.memory[0xffe4]=0
    emulator.memory[0xc6c0 if jp else 0xc6cc]=7
    emulator.memory[0xc65b if jp else 0xc667]=0
    r.PC=0x7c6b if jp else 0x7bc9
    emulator.hook_register(13,0x61c8 if jp else 0x61ac,lambda _:report('attack'),None)
    emulator.hook_register(13,0x7ec8 if jp else 0x7e28,lambda _:report('failed'),None)
elif kind=='fish':
    group,mapid,hi,lo,_=map(int,parts[1:])
    emulator.memory[0xdc7b if jp else 0xdcb5]=group
    emulator.memory[0xdc7c if jp else 0xdcb6]=mapid
    emulator.memory[0xd21b if jp else 0xd1ea]=hi
    emulator.memory[0xd21c if jp else 0xd1eb]=lo
    r.PC=0x69ea if jp else 0x69d9
    emulator.hook_register(15,0x69af if jp else 0x699e,lambda _:report('reroll'),None)
    emulator.hook_register(15,0x6a29 if jp else 0x6a18,lambda _:report('accept'),None)
elif kind=='heal':
    emulator.memory[0xc657 if jp else 0xc663]=0
    for a in ((0xd2d9,0xd245,0xc661,0xc665) if jp else (0xd2a8,0xd214,0xc66d,0xc671)):
        emulator.memory[a]=255
    r.PC=0x44ec if jp else 0x44e0
elif kind=='mean':
    player,enemy=map(int,parts[1:])
    emulator.memory[0xc660 if jp else 0xc66c]=player
    emulator.memory[0xc665 if jp else 0xc671]=enemy
    emulator.memory[0xc65c if jp else 0xc668]=0
    r.PC=0x4e26 if jp else 0x4e0d
    emulator.hook_register(14,r.PC+30,lambda _:report('encourage'),None)
    emulator.hook_register(14,r.PC+14,lambda _:report('fallback'),None)
elif kind=='pp':
    disabled,*pp=map(int,parts[1:])
    emulator.memory[0xc669 if jp else 0xc675]=disabled
    base=0xc62a if jp else 0xc634
    emulator.memory[base:base+4]=pp
    r.PC=0x6795 if jp else 0x6783
    emulator.hook_register(0,0x3a62 if jp else 0x3ad5,lambda _:report('struggle'),None)
else:
    raise AssertionError(kind)
emulator.tick(1,render=False,sound=False)
raise RuntimeError(('CPU probe did not reach checkpoint',version,case,hex(r.PC)))
