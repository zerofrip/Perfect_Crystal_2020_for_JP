"""Confirm every species' released base stats, including regional differences."""
from map_layout import ROOT
jp=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
stock=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
pc=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
port=(ROOT/'work/development_only_jp_partial.gbc').read_bytes()
jbase=0x5251a-131*32;ubase=0x52484-131*32
changed=[];regional=[];missing=[]
for i in range(251):
 j=jp[jbase+i*32:jbase+(i+1)*32]
 u=stock[ubase+i*32:ubase+(i+1)*32]
 p=pc[ubase+i*32:ubase+(i+1)*32]
 q=port[jbase+i*32:jbase+(i+1)*32]
 assert j[0]==u[0]==p[0]==q[0]==i+1
 if j!=u:regional.append(i+1)
 if u!=p:changed.append(i+1)
 if q!=p:
  missing.append(i+1)
  print('missing_record',i+1,'stock',u.hex(),'released',p.hex(),'field_changes',[(n,a,b) for n,(a,b) in enumerate(zip(u,p)) if a!=b])
print('species',251,'2020_changes',changed,'stock_regional_differences',regional,'port_differences',missing)
assert not missing
