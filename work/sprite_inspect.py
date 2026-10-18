from pc_env import workspace
from pathlib import Path
import re
import sys
ROOT=workspace()
sys.path.insert(0,str(ROOT/'work/pokemon-reverse-engineering-tools'))
from pokemontools.lz import Decompressed
Decompressed.__next__=Decompressed.next

def word(d,a):return int.from_bytes(d[a:a+2],'little')
def far(bank,addr):return bank*0x4000+addr-0x4000
ROMS={n:p.read_bytes() for n,p in {'jp':ROOT/'Pocket Monsters - Crystal Version (Japan).gbc','ue':ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc','pc':ROOT/'work/perfect_crystal_ue_patched.gbc'}.items()}
patterns={'anim':rb'\x0e\x34\x21..\x11..\xcd..\x28.\x0e\x34\x21..\x11..',
          'frames':rb'\xfe\x98\x06\x35\x0e\x35\x21..\x38.\x0e\x36',
          'bitmask':rb'\x3e\x34\x21..\x28.\x3e\x34\x21..',
          'palette':rb'\x6f\x26\x00\x29\x29\x29\x01..\x09\xc9',
          'trainerpal':rb'\x6f\x26\x00\x29\x29\x01..\x09\xc9',
          'fixpic':rb'\xe5\xc5\xd6.\x4f\x06\x00\x21..\x09\x7e\xc1\xe1\xc9'}
patterns['frontloader']=rb'\xfa..\xfe\xc9\x28.\xfa..\x16\x48\x18.'
for name,d in ROMS.items():
 print(name)
 base=0xa88b if name=='jp' else 0xa8ce
 print('jynx palette',d[base+124*8:base+125*8].hex())
 print('trainer palettes',[(i,d[base+0x800+i*4:base+0x800+i*4+4].hex()) for i in (29,37,39,56,57)])
 if name=='jp':
  print('gfx free',[(hex(0x50000+m.start()),m.end()-m.start()) for m in re.finditer(b'\x00{30,}',d[0x50000:0x54000])])
  print('frame free',[(hex(0xd4000+m.start()),m.end()-m.start()) for m in re.finditer(b'\x00{30,}',d[0xd4000:0xd8000])])
  print('frames loader',d[0xd05ce:0xd061b].hex())
  print('front caller',d[0x5113b:0x5116d].hex())
 for key,pat in patterns.items():
  print(key,[(hex(m.start()),m.group().hex()) for m in re.finditer(pat,d,re.DOTALL)])
 for label,off in [('anim',0xd0695),('extra',0xd16a3),('frames',0xd4000),('masks',0xd24ef)]:
  entry=off+123*2; pointer=word(d,entry); data=far(off//0x4000,pointer)
  print(label,'entry',hex(entry),'data',hex(data),d[data:data+32].hex())
 for label,entry in [('front',0x120000+123*6),('back',0x120000+123*6+3),('swimmer',0x128000+38*3)]:
  off=far(d[entry]+0x36,word(d,entry+1));dec=Decompressed(d,start=off)
  print(label,'offset',hex(off),'compressed',len(dec.compressed_data),'plain',len(dec.output))
