"""Compare initial-Perfect catch fixes and later stat-down branch in real CPUs."""
from pc_env import workspace
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=workspace()
CASES=[f'status:{status}:{rate}' for status in (0,8,16,64,32,3) for rate in (200,250)]
CASES += [f'held:{item}' for item in (0,37,163,246)]
CASES += [f'transform:{status}:{species}' for status in (0,8) for species in (132,151)]
CASES += [f'sharp:{modifier}:{stage}' for modifier in (0,16) for stage in (1,2,6,12)]
if len(sys.argv)==1:
    results=[]
    for case in CASES:
        got=[]
        for version in ('jp','pc'):
            run=subprocess.run([sys.executable,__file__,version,case],check=True,capture_output=True,text=True,timeout=30)
            got.append(json.loads(run.stdout.splitlines()[-1]))
        assert got[0]==got[1],(case,got)
        p=case.split(':')
        if p[0]=='status':
            status,rate=map(int,p[1:]);bonus=10 if status&0x27 else (5 if status else 0)
            assert got[0]['rate']==min(255,rate+bonus)
        elif p[0]=='held':assert got[0]['item']==int(p[1])
        elif p[0]=='transform':
            assert got[0]=={'species':int(p[2]),'backup':[0x12,0x34] if int(p[1]) else [0xab,0xcd],'substatus':8}
        elif p[0]=='sharp':
            modifier,stage=map(int,p[1:]);expected=0 if modifier and stage==1 else stage
            assert got[0]['stage']==expected
        results.append({'case':case,'cpu':got[0]})
    (ROOT/'work/battlefix_capture_cpu_results.json').write_text(json.dumps(results,indent=2)+'\n')
    print('capture_sharp_cpu_parity_passed',len(CASES),'cases /',2*len(CASES),'CPU executions')
    raise SystemExit
from pyboy import PyBoy
version,case=sys.argv[1:];jp=version=='jp';p=case.split(':');kind=p[0]
rom=(ROOT/('work/battlefix_isolated.gbc' if jp else 'work/perfect_crystal_ue_patched.gbc')).read_bytes()
emulator=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
emulator.tick(600,render=False,sound=False)
r=emulator.register_file
r.SP=0xcffe
emulator.memory[0xcffe:0xd000]=[0,1]
emulator.memory[0xffff]=0;emulator.memory[0xff0f]=0
bank=13 if kind=='sharp' else 3
emulator.memory[0x2000]=bank;emulator.memory[0xff9d]=bank
if kind=='status':
    status,rate=map(int,p[1:]);r.A=rate
    emulator.memory[0xd245 if jp else 0xd214]=status
    r.PC=0x6c16 if jp else 0x6962
    checkpoint=(3,0x6c2d if jp else 0x697c)
elif kind=='held':
    emulator.memory[0xc623 if jp else 0xc62d]=int(p[1])
    r.B=50;r.PC=0x6c2f if jp else 0x697e
    checkpoint=(13,0x7e21 if jp else 0x7d81)
elif kind=='transform':
    status,species=map(int,p[1:])
    emulator.memory[0xc665 if jp else 0xc671]=status
    emulator.memory[0xd235 if jp else 0xd204]=species
    backup=0xc6e6 if jp else 0xc6f2
    dv=0xd23d if jp else 0xd20c
    emulator.memory[backup:backup+2]=[0x12,0x34]
    emulator.memory[dv:dv+2]=[0xab,0xcd]
    r.PC=0x6cbc if jp else 0x6a0c
    checkpoint=(3,0x6cdd if jp else 0x6a22)
elif kind=='sharp':
    modifier,stage=map(int,p[1:])
    emulator.memory[0xc700 if jp else 0xc70c]=modifier
    r.B=stage;r.PC=0x6305 if jp else 0x62e9
    checkpoint=(13,0x6310 if jp else 0x62f4)
else:raise AssertionError(kind)

def done(_):
    if kind=='status':result={'rate':r.A,'bonus':r.C}
    elif kind=='held':result={'item':r.B}
    elif kind=='transform':
        result={'species':emulator.memory[0xd235 if jp else 0xd204],
                'backup':list(emulator.memory[backup:backup+2]),
                'substatus':emulator.memory[0xc665 if jp else 0xc671]}
    else:result={'stage':r.B}
    print(json.dumps(result),flush=True)
    os._exit(0)
emulator.hook_register(*checkpoint,done,None)
emulator.tick(1,render=False,sound=False)
raise RuntimeError(('CPU checkpoint not reached',version,case,hex(r.PC)))
