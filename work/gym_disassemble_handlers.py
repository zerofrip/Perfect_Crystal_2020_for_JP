"""Use pokemon-reverse-engineering-tools on the real JP script dispatcher."""
import os
import subprocess
import sys
from map_layout import ROOT,file_offset,word

rom=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
env=dict(os.environ,PYTHONPATH=str(ROOT/'work/pokemon-reverse-engineering-tools'))
for command,name in ((4,'farjump'),(0x4b,'farwritetext'),(0x5d,'loadtrainer'),(0x63,'winlosstext')):
    offset=file_offset(0x25,word(rom,0x96cb1+command*2))
    output=ROOT/f'work/gym_{name}_actual.asm'
    subprocess.run([sys.executable,'-m','pokemontools.gbz80disasm','-r',
                    str(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc'),
                    '-o',str(output),'-q',f'{offset:x}',f'{offset+40:x}'],env=env,check=True)
    print(name,hex(offset))
    print(output.read_text())
subprocess.run([sys.executable,'-m','pokemontools.gbz80disasm','-r',
                str(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc'),
                '-o',str(ROOT/'work/gym_text_commands_actual.asm'),'-q','1417','1580'],env=env,check=True)
subprocess.run([sys.executable,'-m','pokemontools.gbz80disasm','-r',
                str(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc'),
                '-o',str(ROOT/'work/gym_farprint_actual.asm'),'-q','317c','318b'],env=env,check=True)
