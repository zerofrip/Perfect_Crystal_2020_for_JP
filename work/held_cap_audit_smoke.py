"""Seven independent, actual-CPU smoke cases on the immutable RC3 bytes."""
from pc_env import workspace
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=workspace()
EXPECTED_SHA256='b6f6b73dc7e6d8f4d3223b398fb1202519efae0c0e36959ab7ac43cb8e5a4c21'
CASES=[('species',value) for value in (120,499,500)]
CASES += [('metal',value) for value in (120,665,666,667)]

if len(sys.argv)==1:
    def run(case):
        result=subprocess.run([sys.executable,__file__,case[0],str(case[1])],
                              check=True,capture_output=True,text=True,timeout=30)
        return json.loads(result.stdout.splitlines()[-1])
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,CASES))
    assert len(results)==7 and all(result['passed'] for result in results)
    assert {result['input_sha256'] for result in results}=={EXPECTED_SHA256}
    (ROOT/'work/held_cap_audit_smoke.json').write_text(json.dumps(results,indent=2)+'\n')
    print('held_cap_audit_smoke_passed',len(results),'actual CPU cases',EXPECTED_SHA256)
    raise SystemExit

from pyboy import PyBoy
kind,value=sys.argv[1],int(sys.argv[2])
assert (kind,value) in CASES
rom=(ROOT/'work/development_only_jp_partial.gbc').read_bytes()
digest=sha256(rom).hexdigest()
assert digest==EXPECTED_SHA256
em=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
em.tick(600,render=False,sound=False)
r=em.register_file
em.memory[0xffff]=em.memory[0xff0f]=0
em.memory[0x2000]=em.memory[0xff9d]=0x0d
r.SP=0xcffe
em.memory[0xcffe:0xd000]=[0,1]
r.D=0x89;r.E=0xab
if kind=='species':
    r.B=0x45;r.C=0x67;r.HL=value;r.PC=0x53f1
    expected=min(value*2,999)
else:
    r.B=value>>8;r.C=value&255;r.HL=0x4567;r.PC=0x52cb
    expected=min(value+value//2,999)

def done(_):
    actual=r.HL if kind=='species' else r.B*256+r.C
    checks=[actual==expected,r.D==0x89,r.E==0xab,r.SP==0xd000,
            em.memory[0xff9d]==0x0d]
    if kind=='species':checks.append((r.B,r.C)==(0x45,0x67))
    # The Metal arithmetic deliberately uses HL as its uncapped scratch sum.
    else:checks.append(r.HL==value+value//2)
    result={'kind':kind,'input':value,'expected':expected,'actual':actual,
            'registers':{name:getattr(r,name) for name in ('A','F','B','C','D','E','HL','SP')},
            'input_sha256':digest,'rom_modified':False,'passed':all(checks)}
    if not result['passed']:result['checks']=checks
    print(json.dumps(result),flush=True)
    os._exit(0 if result['passed'] else 1)

em.hook_register(0,0x100,done,None)
em.tick(1,render=False,sound=False)
raise RuntimeError(('CPU sentinel not reached',kind,value,hex(r.PC)))
