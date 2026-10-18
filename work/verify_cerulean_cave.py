"""Independent pointer, map, warp and encounter checks of the local port."""
from map_layout import ROOT, maps, events, file_offset, word

stock=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
port=(ROOT/'work/development_only_jp_partial.gbc').read_bytes()
perfect=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
old=maps(stock)
new=maps(port,True,primary_bank=0x60)
ref=maps(perfect,True)
assert len(old)==388 and len(new)==391
assert port[0x2be2]==port[0x2c13]==0x60
for name, entry in old.items():
    expected=bytearray(entry['header'])
    if name=='CeruleanCity':
        expected[8]=3
    if name=='SilverCaveRoom1':
        expected[7]=0x12
    assert new[name]['header']==expected, name
    if name!='CeruleanCity':
        assert new[name]['attrs']==entry['attrs'], name

all_ids={(e['group'],e['map_id']):name for name,e in new.items()}
names=('CeruleanCity','CeruleanCave1F','CeruleanCave2F','CeruleanCaveB1')
warp_count=0
for name in names:
    entry=new[name]
    event=events(port,entry['events'])
    expected=events(perfect,ref[name]['events'])
    assert event['warps']==expected['warps'], name
    for warp in event['warps']:
        destination=all_ids[tuple(warp[3:5])]
        dest=events(port,new[destination]['events'])
        assert 1<=warp[2]<=len(dest['warps']), (name,destination)
        assert warp[0]<entry['height']*2 and warp[1]<entry['width']*2
        warp_count+=1
    if name!='CeruleanCity':
        assert entry['header'][5]==96
        assert port[entry['blockdata']:entry['blockdata']+135]==perfect[ref[name]['blockdata']:ref[name]['blockdata']+135]
        assert len(event['people'])==len(expected['people'])
        for person in event['people']:
            pointer=file_offset(entry['bank'],word(person,9))
            assert pointer==0x18148f and person[-2:]==bytes.fromhex('0501')

city_events=events(port,new['CeruleanCity']['events'])
old_city_events=events(stock,old['CeruleanCity']['events'])
assert city_events['people'][:6]==old_city_events['people']
expected_signposts=list(old_city_events['signposts'])
hidden=[i for i,s in enumerate(expected_signposts) if s==bytes.fromhex('0c0207d076')]
assert len(hidden)==1
expected_signposts[hidden[0]]=bytes.fromhex('110207d076')
assert city_events['signposts']==expected_signposts
assert port[file_offset(0x61,0x76d0):file_offset(0x61,0x76d0)+3]==bytes.fromhex('fa0098')
assert city_events['people'][-1][-2:]==bytes.fromhex('4f07')
assert port[0x184200:0x184203]==bytes.fromhex('510342')
assert port[0x2b297:0x2b8a7]==perfect[0x2b274:0x2b884]
assert port[0x2bd04:0x2bdef]==perfect[0x2b884:0x2b96f]
assert port[0x2a03d:0x2a03f]==port[0x2a21b:0x2a21d]==bytes.fromhex('047d')

for index in range(96):
    old_entry=0x92557+index*4
    new_entry=0x181800+index*4
    assert stock[old_entry:old_entry+2]==port[new_entry:new_entry+2]
    old_name=file_offset(0x24,word(stock,old_entry+2))
    new_name=file_offset(0x60,word(port,new_entry+2))
    assert stock[old_name:old_name+11]==port[new_name:new_name+11]
new_name=file_offset(0x60,word(port,0x181800+96*4+2))
assert port[new_name:new_name+9]==bytes.fromhex('99940fc934b3b8c250')
print('original_map_headers_preserved',388)
print('new_cave_maps',3,'warp_destinations_checked',warp_count)
print('original_japanese_landmark_names_preserved',96)
print('full_kanto_encounters_match_2020','grass=33 water=26')
