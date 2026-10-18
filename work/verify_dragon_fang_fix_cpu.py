"""Execute actual held-item lookup and complete JP DamageCalc for RC2."""
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys

from map_layout import ROOT,word
from fix_dragon_fang import apply_dragon_fang_fix

WORK=ROOT/'work'
CASES=[(turn,item,kind,power) for turn in (0,1) for item in (0,0x90,0x97)
       for kind in (0,0x1a) for power in (3,100)]
if len(sys.argv)==1 or sys.argv[1]=='--rom':
    path=Path(sys.argv[2]) if len(sys.argv)>1 else ROOT/'Pokemon Perfect Crystal 2020 Japanese.gbc'
    results=[]
    for case in CASES:
        proc=subprocess.run([sys.executable,__file__,'--case',str(path),*map(str,case)],
                            check=True,capture_output=True,text=True,timeout=30)
        results.append(json.loads(proc.stdout.splitlines()[-1]))
    report={'input_sha256':sha256(path.read_bytes()).hexdigest(),'cases':results,'count':len(results)}
    (WORK/'dragon_fang_fix_cpu_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('dragon_fang_complete_damage_cpu_passed',len(results),'cases; both sides, matching/nonmatching types, rounding, no item and Dragon Scale')
    raise SystemExit

assert sys.argv[1]=='--case'
path=Path(sys.argv[2]);turn,item,kind,power=map(int,sys.argv[3:])
j=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
u=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
p=(WORK/'perfect_crystal_ue_patched.gbc').read_bytes()
rom=bytearray(path.read_bytes())
from fix_dragon_fang import OFFSET
if rom[OFFSET+3]==0:apply_dragon_fang_fix(j,u,p,rom)
else:assert rom[OFFSET:OFFSET+7]==bytes.fromhex('6400400a400100')
assert rom[0x35612:0x35619]==bytes.fromhex('3e0dcd9039fe07')
assert rom[0x3571f:0x35721]==bytes.fromhex('401a')

from pyboy import PyBoy
em=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
em.tick(600,render=False,sound=False)
r=em.register_file
em.memory[0xffff]=em.memory[0xff0f]=0
em.memory[0x2000]=em.memory[0xff9d]=13
em.memory[0xffe4]=turn
em.memory[0xc623]=item if turn==0 else 0
em.memory[0xd238]=item if turn==1 else 0
# Follow the real GetBattleVar pointer tables instead of assuming WRAM offsets.
def battle_var(var):
    pair=word(rom,0x39b7+2*var)
    return word(rom,0x3a0b+rom[pair+turn]*2)
em.memory[battle_var(0x0d)]=0 # ordinary damaging move, no special effect
em.memory[battle_var(0x0f)]=kind
em.memory[0xc65a]=0 # noncritical
em.memory[0xd287:0xd289]=[0,0]
r.B=100;r.C=100;r.D=power;r.E=50
r.SP=0xcffe;em.memory[0xcffe:0xd000]=[0,1]
r.PC=0x5612
intermediate=((2*50//5+2)*power*100//100)//50
boosted=(item==0x90 and kind==0x1a)
expected=min(997,intermediate*(110 if boosted else 100)//100)+2

def finish(_):
    actual=(em.memory[0xd287]<<8)|em.memory[0xd288]
    result=dict(turn=turn,item=item,move_type=kind,power=power,damage=actual,expected=expected)
    assert actual==expected,result
    assert r.SP==0xd000 and em.memory[0xff9d]==13
    print(json.dumps(result),flush=True)
    os._exit(0)

em.hook_register(0,0x100,finish,None)
em.tick(1,render=False,sound=False)
raise RuntimeError(('damage routine did not return',hex(r.PC)))
