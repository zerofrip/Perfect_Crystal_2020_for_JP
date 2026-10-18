"""Disassemble local original Japanese clock/title routines with pret tools."""
from pc_env import workspace
from pathlib import Path
import subprocess, sys, os
ROOT = workspace()
env = dict(os.environ, PYTHONPATH=str(ROOT/'work/pokemon-reverse-engineering-tools'))
rom=ROOT/'Pocket Monsters - Crystal Version (Japan).gbc'
for name,start,end in [('title_dispatch',0x6370,0x6474)]:
    out=ROOT/f'work/clockreset_{name}.asm'
    subprocess.run([sys.executable,'-m','pokemontools.gbz80disasm','-r',str(rom),'-o',str(out),'-q',f'{start:x}',f'{end:x}'],env=env,check=True)
    print(name,str(out))
data=rom.read_bytes()
for bank in (1,0x6a):
    begin=bank*0x4000; end=begin+0x4000
    p=end
    while p>begin and data[p-1]==0:p-=1
    print('bank',hex(bank),'trailing_zero',hex(p),end-p)
print('title table',data[0x63e4:0x63ec].hex())
print('delete menu',data[0x4d3f4:0x4d408].hex())
print('title hook',data[0x648c:0x64ab].hex())
for offset,size in [(0x63d8,12),(0x5e31,21),(0x6e3,13)]:print('anchor',hex(offset),data[offset:offset+size].hex())
for name in ['perfect_crystal_ue_patched.gbc']:
    en=(ROOT/'work'/name).read_bytes()
    print('perfect_title',en[0x6315:0x6330].hex())
    print('perfect_menu',en[0x4d3b1:0x4d40d].hex())
