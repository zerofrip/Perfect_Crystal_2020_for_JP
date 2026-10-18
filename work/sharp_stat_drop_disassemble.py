"""Read original/integrated stat-down code with local pokemontools."""
from pc_env import workspace
import os
from pathlib import Path
import subprocess
import sys

ROOT=workspace()
env=dict(os.environ,PYTHONPATH=str(ROOT/'work/pokemon-reverse-engineering-tools'))
inputs=[('original','Pocket Monsters - Crystal Version (Japan).gbc'),
        ('integrated','work/development_only_jp_partial.gbc')]
ranges=((0x36280,0x36410),(0x36432,0x36464),(0x373b0,0x373e5),
        (0x37dfb,0x37e10),(0x3990,0x39f0),(0x37fa0,0x37fca))
if sys.argv[1:]==['--integrated-wrapper']:
    inputs=inputs[1:]
    ranges=((0x37fa0,0x37fca),)
else:assert not sys.argv[1:]
for label,filename in inputs:
    for start,end in ranges:
        target=ROOT/f'work/sharp_stat_drop_{label}_{start:x}.asm'
        subprocess.run([sys.executable,'-m','pokemontools.gbz80disasm','-r',str(ROOT/filename),'-o',str(target),'-q',f'{start:x}',f'{end:x}'],env=env,check=True)
        print(target)
