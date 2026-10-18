"""Read every evolution/learnset and move record from actual ROM tables."""
from map_layout import ROOT,word,file_offset
roms={k:(ROOT/v).read_bytes() for k,v in (
 ('jp','Pocket Monsters - Crystal Version (Japan).gbc'),
 ('stock','Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc'),
 ('2020','work/perfect_crystal_ue_patched.gbc'),
 ('port','work/development_only_jp_partial.gbc'))}
def records(rom,table):
 result=[]
 for i in range(251):
  start=file_offset(16,word(rom,table+2*i));end=start
  while rom[end]:
   assert 1<=rom[end]<=5,(i,hex(end),rom[end])
   end+=4 if rom[end]==5 else 3
  end+=1
  while rom[end]:
   assert rom[end]<=100
   end+=2
  result.append(rom[start:end+1])
 return result
tables={k:records(v,0x42753 if k in ('jp','port') else 0x425b1) for k,v in roms.items()}
changes=[i+1 for i,(a,b) in enumerate(zip(tables['stock'],tables['2020'])) if a!=b]
missing=[i+1 for i,(a,b) in enumerate(zip(tables['port'],tables['2020'])) if a!=b]
regional=[i+1 for i,(a,b) in enumerate(zip(tables['jp'],tables['stock'])) if a!=b]
print('evolution_learnset_records',251,'released_changes',changes,'regional',regional,'port_differences',missing)
assert not missing
