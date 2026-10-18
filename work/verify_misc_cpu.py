"""Compare actual JP/2020 CPU paths for the ported miscellaneous routines."""
import json,os,subprocess,sys
from io import BytesIO
from map_layout import ROOT

CASES=[f'hp:{hp}:{pixels}' for hp,pixels in ((1,0),(1,1),(50,24),(255,47),(255,48),(128,12),(200,32))]
CASES += [f'music:{trainer}' for trainer in (0x1f,0x42,0x33,0x37,0x14,1,0x13)]
CASES += [f'slot:{frame}' for frame in (0,1,8,9)]
CASES += [f'daisy:{rng}' for rng in (0,127,128,254,255)]
if len(sys.argv)==1:
    for case in CASES:
        result=[]
        for version in ('jp','pc'):
            p=subprocess.run([sys.executable,__file__,version,case],capture_output=True,text=True,check=True,timeout=30)
            result.append(json.loads(p.stdout.splitlines()[-1]))
        assert result[0]==result[1],(case,result)
        if case.startswith('daisy:'):assert result[0]=={'value':2,'happiness':0x12}
    print('misc_cpu_release_parity_passed',len(CASES),'cases /',len(CASES)*2,'CPU executions')
    raise SystemExit

from pyboy import PyBoy
version,case=sys.argv[1:];jp=version=='jp';parts=case.split(':');kind=parts[0]
rom=(ROOT/('work/misc_isolated.gbc' if jp else 'work/perfect_crystal_ue_patched.gbc')).read_bytes()
game=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
game.tick(600,render=False,sound=False)
r=game.register_file;r.SP=0xcffe
game.memory[0xcffe:0xd000]=[0,1]
game.memory[0xffff]=0;game.memory[0xff0f]=0
bank={'hp':3,'music':11,'slot':36,'daisy':1}[kind]
game.memory[0x2000]=bank;game.memory[0xff9d]=bank

def finish(value):
    print(json.dumps(value),flush=True);os._exit(0)

if kind=='hp':
    hp,pixels=map(int,parts[1:]);base=0xd21b if jp else 0xd1ea
    game.memory[base]=hp;game.memory[base+7]=pixels
    game.memory[base+11]=0;game.memory[base+12]=255
    r.PC=0x5a8e if jp else 0x5839
    game.hook_register(0,0x100,lambda _:finish({'hp':game.memory[base+2]}),None)
elif kind=='music':
    r.A=int(parts[1]);r.PC=0x7d66 if jp else 0x6e7e
    game.hook_register(bank,0x7db9 if jp else 0x6edd,lambda _:finish({'path':'rocket','music':(r.D<<8)|r.E}),None)
    game.hook_register(bank,0x7d71 if jp else 0x6e95,lambda _:finish({'path':'other'}),None)
elif kind=='slot':
    game.memory[0xcf58 if jp else 0xcf64]=int(parts[1])
    r.PC=0x6f3b if jp else 0x69c8
    game.hook_register(0,0x100,lambda _:finish({'sound':False}),None)
    game.hook_register(0,0x3bb0 if jp else 0x3c23,lambda _:finish({'sound':True,'id':(r.D<<8)|r.E}),None)
else:
    r.A=int(parts[1]);r.HL=0x7f80 if jp else 0x7451
    if jp:
        r.PC=0x7dd8;stop=0x7de5
    else:
        needle=bytes.fromhex('96380523232318f8232aeaddc24e')
        offset=rom.index(needle,0x4000,0x8000);r.PC=offset;stop=offset+13
    game.hook_register(bank,stop,lambda _:finish({'value':r.A,'happiness':game.memory[r.HL]}),None)
game.tick(20,render=False,sound=False)
raise AssertionError(('breakpoint not reached',case,hex(r.PC)))
