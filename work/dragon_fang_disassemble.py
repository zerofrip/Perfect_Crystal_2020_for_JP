"""Disassemble the local JP held-item and damage paths with pokemontools."""
import os
import subprocess
import sys
from map_layout import ROOT

env=dict(os.environ,PYTHONPATH=str(ROOT/'work/pokemon-reverse-engineering-tools'))
for name,start,end in [('damage',0x354d0,0x357d0),('held',0x37dc0,0x37e80),('vars',0x3990,0x3aa0)]:
    target=ROOT/f'work/dragon_fang_{name}_actual.asm'
    subprocess.run([sys.executable,'-m','pokemontools.gbz80disasm','-r',
                    str(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc'),
                    '-o',str(target),'-q',f'{start:x}',f'{end:x}'],env=env,check=True)
    print(target)
