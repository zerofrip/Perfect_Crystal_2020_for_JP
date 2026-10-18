"""Compare the actual released length helper with the Japanese one-byte port."""
from pc_env import workspace
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=workspace()
CASES=((0x100,0x101),(0x102,0x101),(0x200,0x101),(0xff,0x100),(0x100,0xff),(0x100,0x100))
if len(sys.argv)==1:
    results=[]
    for bc,de in CASES:
        observations=[]
        for version in ('jp','pc'):
            run=subprocess.run([sys.executable,__file__,version,str(bc),str(de)],check=True,capture_output=True,text=True)
            observations.append(json.loads(run.stdout.splitlines()[-1]))
        assert observations[0]==observations[1],(bc,de,observations)
        expected=(bc>>8)<(de>>8) or ((bc&255)<(de&255))
        assert observations[0]['carry']==expected
        results.append({'bc':bc,'de':de,'cpu':observations[0]})
    (ROOT/'work/battlefix_length_cpu_results.json').write_text(json.dumps(results,indent=2)+'\n')
    print('magikarp_length_cpu_parity_passed',len(CASES),'cases /',2*len(CASES),'CPU executions')
    raise SystemExit
from pyboy import PyBoy
version,bc,de=sys.argv[1:];bc=int(bc);de=int(de)
rom=(ROOT/('work/battlefix_isolated.gbc' if version=='jp' else 'work/perfect_crystal_ue_patched.gbc')).read_bytes()
emulator=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
emulator.tick(600,render=False,sound=False)
r=emulator.register_file
r.SP=0xcffe
emulator.memory[0xcffe:0xd000]=[0,1]
emulator.memory[0xffff]=0;emulator.memory[0xff0f]=0
emulator.memory[0x2000]=0x3e;emulator.memory[0xff9d]=0x3e
r.PC=0x7df5 if version=='jp' else 0x7c9a
r.B=bc>>8;r.C=bc&255;r.D=de>>8;r.E=de&255
def done(_):
    assert r.SP==0xd000
    print(json.dumps({'a':r.A,'flags':r.F,'carry':bool(r.F&16)}),flush=True)
    os._exit(0)
emulator.hook_register(0,0x100,done,None)
emulator.tick(1,render=False,sound=False)
raise RuntimeError('length helper checkpoint not reached')
