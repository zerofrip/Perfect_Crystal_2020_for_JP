"""Local actual-ROM disassembly for the requested held-stat cap correction."""
from pc_env import workspace
from hashlib import sha256
from pathlib import Path
import runpy
import sys

ROOT=workspace()
rom=(ROOT/'work/development_only_jp_partial.gbc').read_bytes()
print('current_sha256',sha256(rom).hexdigest())
for start,size in ((0x352b1,43),(0x3533f,14),(0x35453,14),(0x37f70,35),(0x37fca,8)):
    print(hex(start),rom[start:start+size].hex())
sys.path.insert(0,str(ROOT/'work/pokemon-reverse-engineering-tools'))
sys.argv=['pokemontools.gbz80disasm','-r',str(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc'),
          '-o',str(ROOT/'work/held_item_stat_cap_original.asm'),'-q','0x352b1','0x35461']
runpy.run_module('pokemontools.gbz80disasm',run_name='__main__')
