"""Use the requested reverse-engineering toolkit on real JP feature routines."""
import os
import subprocess
import sys
from map_layout import ROOT

env=dict(os.environ,PYTHONPATH=str(ROOT/'work/pokemon-reverse-engineering-tools'))
for name,start,end in [('trade',0xfcc60,0xfce58),('party',0x50260,0x502a1),('hp',0xd970,0xd9ad),('red',0x2741d,0x2742f)]:
    path=ROOT/f'work/remaining_{name}_actual.asm'
    subprocess.run([sys.executable,'-m','pokemontools.gbz80disasm','-r',
                    str(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc'),
                    '-o',str(path),'-q',f'{start:x}',f'{end:x}'],env=env,check=True)
    print(name,path)
