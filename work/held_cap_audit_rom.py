"""Local-only, read-only ROM audit for the held-stat-cap review."""
from pc_env import workspace
import os
import json
from pathlib import Path
import subprocess
import sys

ROOT=workspace()
env=dict(os.environ,PYTHONPATH=str(ROOT/'work/pokemon-reverse-engineering-tools'))
for label,path in (('original',ROOT/'Pocket Monsters - Crystal Version (Japan).gbc'),
                   ('rc2',ROOT/'work/rc2_reference.gbc')):
    for start,end in ((0x352a0,0x35480),(0x37df0,0x37e31),(0x37f70,0x37f93),
                      (0x3900,0x3970)):
        target=ROOT/f'work/held_cap_audit_{label}_{start:x}.asm'
        subprocess.run([sys.executable,'-m','pokemontools.gbz80disasm','-r',str(path),
                        '-o',str(target),'-q',f'{start:x}',f'{end:x}'],
                       env=env,check=True)
        print(target)

rom=(ROOT/'work/rc2_reference.gbc').read_bytes()
calls={}
for name,cpu in (('DittoMetalPowder',0x52b1),('TruncateHL_BC',0x534d),
                 ('ThickClubBoost',0x53b5),('LightBallBoost',0x53c3),
                 ('SpeciesItemBoost',0x53d1)):
    pattern=b'\xcd'+cpu.to_bytes(2,'little')
    calls[name]=[hex(offset) for offset in range(0x34000,0x38000-2)
                 if rom[offset:offset+3]==pattern]
target=ROOT/'work/held_cap_audit_calls.json'
target.write_text(json.dumps(calls,indent=2)+'\n')
print(json.dumps(calls))
