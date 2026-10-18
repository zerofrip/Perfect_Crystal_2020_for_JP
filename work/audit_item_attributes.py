"""Verify all 255 item records in the integrated Japanese artifact."""
from map_layout import ROOT
from port_item_attributes import JP_TABLE,UE_TABLE,PC_TABLE,COUNT
j=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
u=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
p=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
q=(ROOT/'work/development_only_jp_partial.gbc').read_bytes()
changes=[];regional=[]
for i in range(COUNT):
 old=j[JP_TABLE+i*7:JP_TABLE+(i+1)*7]
 before=u[UE_TABLE+i*7:UE_TABLE+(i+1)*7]
 after=p[PC_TABLE+i*7:PC_TABLE+(i+1)*7]
 actual=q[JP_TABLE+i*7:JP_TABLE+(i+1)*7]
 if old!=before:regional.append(i+1)
 if before!=after:
  changes.append((i+1,[(n,a,b) for n,(a,b) in enumerate(zip(before,after)) if a!=b]))
 expected=bytearray(after if before!=after else old)
 if i+1==0x90:
  assert expected==bytes.fromhex('64004000400100')
  expected[3]=10 # explicitly requested RC2 Dragon Fang correction
 assert actual==expected,i+1
prices=[i for i,delta in changes if all(n<2 for n,_,_ in delta)]
effects=[i for i,delta in changes if any(n>=2 for n,_,_ in delta)]
assert len(prices)==11 and effects==[0x90,0x97]
print('item_records_verified',COUNT,'prices',len(prices),'held_effects',effects,'dragon_fang_amount',10,'preserved_regional_records',regional)
