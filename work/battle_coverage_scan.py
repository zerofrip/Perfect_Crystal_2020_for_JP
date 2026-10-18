"""Read-only probes of unaccounted item and stat-down changes in actual ROMs."""
from pc_env import workspace
from pathlib import Path
import re
ROOT=workspace()
ROMS={n:p.read_bytes() for n,p in {'jp':ROOT/'Pocket Monsters - Crystal Version (Japan).gbc','ue':ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc','pc':ROOT/'work/perfect_crystal_ue_patched.gbc'}.items()}
patterns={
 'status':rb'\x47\xfa..\xe6\x27\x0e\x0a\x20.',
 'held':rb'\x57\xd5\xfa..(?:\x47)?\x3e.\x21..\xcf\x78\xfe',
 'transformed':rb'\x21..\x7e\xf5\xcb\xde\xcb\x5f',
 'statdown':rb'\xfa..\xe6\xf0\x28.\x05[\x20\x28].\x04',
}
for name,d in ROMS.items():
 print(name)
 if name=='jp':print('item_bank_free',[(hex(0xc000+m.start()),m.end()-m.start()) for m in re.finditer(b'\x00{30,}',d[0xc000:0x10000])])
 for label,pat in patterns.items():
  found=[]
  for m in re.finditer(pat,d,re.DOTALL):
   if (label=='statdown' and 0x34000<=m.start()<0x38000) or (label!='statdown' and 0xc000<=m.start()<0x10000):
    found.append((hex(m.start()),d[m.start():m.start()+75].hex()))
  print(label,found)
