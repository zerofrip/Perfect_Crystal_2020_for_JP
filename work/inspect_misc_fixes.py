from map_layout import ROOT
roms={k:(ROOT/v).read_bytes() for k,v in (
 ('jp','Pocket Monsters - Crystal Version (Japan).gbc'),
 ('stock','Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc'),
 ('2020','work/perfect_crystal_ue_patched.gbc'))}
import re
patterns={
 'daisy':bytes.fromhex('4c020980030aff040b9a020c4c030dff040e'),
 'jp_exp':re.escape(bytes.fromhex('0966d024')),
 'ue_exp':bytes.fromhex('0902d125'),
 'exp_any':rb'\x09..[\x24\x25]\x00',
}
for name,pattern in patterns.items():
 print(name)
 for tag,rom in roms.items():
  area=rom[:0x100000] if name!='exp_any' else rom[0x180000:0x200000]
  print(tag,[(hex(m.start()+(0x180000 if name=='exp_any' else 0)),area[max(0,m.start()-12):m.end()+20].hex()) for m in re.finditer(pattern,area,re.DOTALL)])
for bank in (1,3,0xb,0x24,0x3f):
 rom=roms['jp'];end=(bank+1)*0x4000;start=end
 while start>bank*0x4000 and rom[start-1]==0:start-=1
 print('tail',hex(bank),hex(start),end-start)
for name,rom in roms.items():
 for needle in ('843030303030300000233d','21077e','216a7e','0966d024'):
  data=bytes.fromhex(needle)
  pos=rom.find(data)
  print('literal',name,needle,rom.count(data),hex(pos),rom[max(0,pos-8):pos+35].hex())
