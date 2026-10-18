from pc_env import workspace
from pathlib import Path
from hashlib import sha1
root=workspace()
paths={'jp':root/'Pocket Monsters - Crystal Version (Japan).gbc','ue':root/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc','pc':root/'work/perfect_crystal_ue_patched.gbc'}
needles={'belly':'219f4c3e0fcf21de4c3e0fcf30','boost':'2a6e67','metal':'7d','magikarp':'fe813e','gender':'7ad1bac1'}
data={n:p.read_bytes() for n,p in paths.items()}
print('SHA1', {n:sha1(d).hexdigest() for n,d in data.items()})
print({n:{hex(a):d[a:z].hex() for a,z in ([(0x37c6b,0x37ca6),(0x3e9d7,0x3ea29)] if n=='jp' else [(0x37bc9,0x37c06),(0x352c8,0x352df),(0x3e9c6,0x3ea18)])} for n,d in data.items() if n!='ue'})
for n,pattern in needles.items():
 if len(pattern)<8:continue
 print(n,{name:[hex(i) for i in range(len(d)) if d.startswith(bytes.fromhex(pattern),i)] for name,d in data.items()})
for name in data:
 d=data[name]
 for label,a,z in [('metal',0x352a0,0x35300),('boost',0x353b0,0x35440)]:
  print(name,label,hex(a),d[a:z].hex())
for name,d in data.items():
 print(name,'zeros bank d',[(hex(a),len(m)) for a,m in __import__('re').finditer if False] if False else [(hex(0x34000+m.start()),m.end()-m.start()) for m in __import__('re').finditer(b'\x00{12,}',d[0x34000:0x38000])])
 print(name,'magikarp',[(hex(m.start()),d[m.start():m.start()+85].hex()) for m in __import__('re').finditer(bytes.fromhex('fe813e'),d)] if False else [(hex(m.start()),d[m.start():m.start()+90].hex()) for m in __import__('re').finditer(bytes.fromhex('fe8100'),d)])
 print(name,'fish species',[(hex(m.start()),d[m.start():m.start()+85].hex()) for m in __import__('re').finditer(bytes.fromhex('fec9'),d) if 0x3c000<=m.start()<0x40000])
