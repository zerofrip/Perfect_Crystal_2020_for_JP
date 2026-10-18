"""Locate and compare every item attribute record in the actual three ROMs."""
import json
from battle_coverage_scan import ROOT,ROMS

needle=ROMS['ue'][0x67c1:0x67cf]
offsets={}
for name,rom in ROMS.items():
    offset=rom.find(needle)
    assert offset>=0 and rom.find(needle,offset+1)<0,(name,offset)
    offsets[name]=offset
print('item table offsets', {n:hex(a) for n,a in offsets.items()})
records=[]
for i in range(0xff):
    attrs={n:d[offsets[n]+i*7:offsets[n]+(i+1)*7] for n,d in ROMS.items()}
    if attrs['ue']!=attrs['pc'] or attrs['jp']!=attrs['pc']:
        record={'item_id':i+1,'jp':attrs['jp'].hex(),'ue':attrs['ue'].hex(),'pc':attrs['pc'].hex(),
                'jp_diff':[j for j in range(7) if attrs['jp'][j]!=attrs['pc'][j]],
                'release_diff':[j for j in range(7) if attrs['ue'][j]!=attrs['pc'][j]]}
        records.append(record)
print('changed records',len(records),'price-only',sum(set(r['jp_diff'])<=set((0,1)) for r in records))
print('nonprice',[r for r in records if not set(r['jp_diff'])<=set((0,1))])
(ROOT/'work/battle_coverage_item_attributes.json').write_text(json.dumps({'offsets':offsets,'records':records},indent=2)+'\n')
