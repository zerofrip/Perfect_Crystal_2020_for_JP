import runpy,sys
from map_layout import ROOT
sys.path.insert(0,str(ROOT/'work/pokemon-reverse-engineering-tools'))
for name,start,end in (('massage',0x7d80,0x7e82),('hpbar',0xda8e,0xdaea),('music',0x2fd20,0x2fe20)):
 sys.argv=['pokemontools.gbz80disasm','-r',str(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc'),'-o',str(ROOT/f'work/jp_{name}_pokemontools.asm'),'-q',f'{start:x}',f'{end:x}']
 runpy.run_module('pokemontools.gbz80disasm',run_name='__main__')
