from pc_env import workspace
from pathlib import Path
import re
root=workspace()
roms={'jp':root/'Pocket Monsters - Crystal Version (Japan).gbc','ue':root/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc','pc':root/'work/perfect_crystal_ue_patched.gbc'}
patterns={'heal':rb'\xfa..\x21..\x01\x30\x00\xcd..\xaf\x77\xea..\x21..\xcb\x86',
          'mean':rb'\xfa..\xcb\x47\x20.\xfa..\xe6\xc9\x20.',
          'pp':rb'\x3e\xa5\xea..\xfa..\xa7\x21..\x20.\x2a\xb6\x23\xb6\x23\xb6\xe6\x3f',
          'defense':rb'\x00'}
for name,path in roms.items():
 d=path.read_bytes()
 for key,pat in patterns.items():
  if key=='defense':continue
  print(name,key,[(hex(m.start()),d[m.start():m.start()+65].hex()) for m in re.finditer(pat,d,flags=re.DOTALL)])
 print(name,'effect',d[0x2750b:0x27528].hex())
 for label,needle in [('fish_compare_old',bytes.fromhex('78bad8d079bbc9')),('fish_compare_new',bytes.fromhex('78bad879bbc9'))]:
  print(name,label,hex(d.find(needle)),d.count(needle))
 if name=='jp':
  for bank in (9,14,15):
   print(name,'free',bank,[(hex(bank*0x4000+m.start()),m.end()-m.start()) for m in re.finditer(b'\x00{20,}',d[bank*0x4000:(bank+1)*0x4000])])
  old=bytes.fromhex('02030405066207080990ab0d0e0f101112907f8dff')
  print('JP defense script',hex(d.find(old)))
