import runpy
import sys
from map_layout import ROOT

sys.path.insert(0,str(ROOT/'work/pokemon-reverse-engineering-tools'))
for name,start,end in (('script_byte',0x2697,0x26b5),('script_dispatch',0x96c60,0x96cb1)):
    sys.argv=['pokemontools.gbz80disasm','-r',str(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc'),
              '-o',str(ROOT/f'work/jp_{name}_pokemontools.asm'),'-q',f'{start:x}',f'{end:x}']
    runpy.run_module('pokemontools.gbz80disasm',run_name='__main__')
