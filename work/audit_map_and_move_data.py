"""Semantic inventory: all original maps and all move data, from actual ROMs."""
from map_layout import ROOT,maps,events
roms={k:(ROOT/v).read_bytes() for k,v in (
 ('jp','Pocket Monsters - Crystal Version (Japan).gbc'),
 ('stock','Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc'),
 ('2020','work/perfect_crystal_ue_patched.gbc'),
 ('port','work/development_only_jp_partial.gbc'))}
move_anchor=bytes.fromhex('01002800ff230002003201ff1900')
tables={}
for name,rom in roms.items():
 assert rom.count(move_anchor)==1,(name,rom.count(move_anchor))
 start=rom.index(move_anchor);table=rom[start:start+251*7]
 assert all(table[i*7]==i+1 for i in range(251))
 tables[name]=table
print('move_records',251,'released_changes',sum(a!=b for a,b in zip(tables['stock'],tables['2020'])),
      'port_difference_bytes',sum(a!=b for a,b in zip(tables['port'],tables['2020'])))
assert tables['port']==tables['2020']
ms={k:maps(v,k in ('2020','port'),primary_bank=0x60 if k=='port' else 0x25) for k,v in roms.items()}
block_changes=[];header_changes=[];event_count_changes=[];attribute_changes=[]
for name,u in ms['stock'].items():
 p=ms['2020'][name];j=ms['jp'][name];q=ms['port'][name]
 def blocks(key,entry):return roms[key][entry['blockdata']:entry['blockdata']+entry['height']*entry['width']]
 if blocks('stock',u)!=blocks('2020',p):
  block_changes.append(name)
  assert blocks('port',q)==blocks('2020',p),(name,'block data')
 ph=bytearray(p['header'])
 if ph[5]>56:ph[5]-=1
 changes=[(i,u['header'][i],ph[i]) for i in (1,2,5,6,7,8) if u['header'][i]!=ph[i]]
 if changes:
  header_changes.append((name,changes))
  for i,before,after in changes:
   assert q['header'][i]==after,(name,i,'unported header field')
 attrs=[(i,u['attrs'][i],p['attrs'][i]) for i in (0,1,2,11) if u['attrs'][i]!=p['attrs'][i]]
 if attrs:attribute_changes.append((name,attrs))
 ue,pe=events(roms['stock'],u['events']),events(roms['2020'],p['events'])
 counts=[(section,len(ue[section]),len(pe[section])) for section in ('warps','xy','signposts','people') if len(ue[section])!=len(pe[section])]
 if counts:event_count_changes.append((name,counts))
print('existing_map_blocks_changed',block_changes)
print('existing_map_header_fields_changed',header_changes)
print('existing_map_attribute_fields_changed',attribute_changes)
print('existing_map_event_counts_changed',event_count_changes)
