"""Read-only probes of initial-import candidates in four actual local ROMs."""
import json
import re
from map_layout import ROOT, maps, events, file_offset, word
from dialogue_mapping import japanese_chars
from gym_text_evidence import english_chars, read_text

ROMS={
    'jp':(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes(),
    'stock':(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes(),
    '2020':(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes(),
    'output':(ROOT/'work/development_only_jp_partial.gbc').read_bytes(),
}
report={}
def matches(pattern,rom):
    return [{'offset':hex(m.start()),'bytes':m.group().hex()} for m in re.finditer(pattern,rom,re.DOTALL)]

patterns={
    'hp_compute_before_restore':rb'\xcd..(?:\x7b)?\xc1\xd1\xe1(?:\x7b)?\x21..\xbe\x28.',
    'party_evo_copy':rb'\x11..\x3e\x10\x01[\x0a\x10]\x00\xcd..\x21..\x2a\xa7\x28.\x23\x23\xfe\x02',
    'trainer_dvs':re.escape(bytes.fromhex('9a778888988898889888988898887cdddddd9888dcdddcdd')),
    'fish_data':re.escape(bytes.fromhex('b3810ad9810aff620a598114b26214e66214ff0000666228b20001e66228ff6328')),
}
for title,pattern in patterns.items():
    report[title]={tag:matches(pattern,rom) for tag,rom in ROMS.items()}

for tag,rom in ROMS.items():
    entries=report['trainer_dvs'][tag]
    assert len(entries)==1
    offset=int(entries[0]['offset'],16)
    entries[0]['all_67_classes']=rom[offset:offset+134].hex()
    entries[0]['red_offset']=hex(offset+62*2)
    entries[0]['red_dvs']=rom[offset+62*2:offset+63*2].hex()
    fish=report['fish_data'][tag]
    assert len(fish)==1,(tag,fish,ROMS['stock'][0x924e3:0x92504].hex())
    offset=int(fish[0]['offset'],16)
    fish[0]['full_tables']=rom[offset:offset+0x1e4].hex()

for title,tag in (('jp','jp'),('stock','stock'),('2020','2020'),('output','output')):
    rom=ROMS[tag]
    entry=maps(rom,tag in ('2020','output'),primary_bank=0x60 if tag=='output' else 0x25)['SilphCo1F']
    person=events(rom,entry['events'])['people'][1]
    script=file_offset(entry['bank'],word(person,9))
    data=rom[script:script+40]
    report.setdefault('silph_guard',{})[tag]={'bank':entry['bank'],'script':hex(script),'bytes':data.hex()}
    if data[0] in (0x51,0x6a,0x6b):
        text=file_offset(entry['bank'],word(data,1) if data[0]==0x51 else word(data,9))
        # The original conditional guard's first write is at +8, after checkevent.
        if rom[text]!=0:
            write=data.index(0x4c)
            text=file_offset(entry['bank'],word(data,write+1))
        chars=japanese_chars() if tag in ('jp','output') else english_chars()
        report['silph_guard'][tag]['text']=hex(text)
        report['silph_guard'][tag]['decoded']=''.join(chars.get(b,f'<{b:02x}>') for b in read_text(rom,text))

charmap={s:b for b,s in english_chars().items() if len(s)==1}
for nickname in ('DORIS','DODRIO','AEROY','AERODACTYL'):
    pattern=bytes(charmap[c] for c in nickname)+b'\x50'
    report.setdefault('trade_nickname',{})[nickname]={tag:[hex(m.start()) for m in re.finditer(re.escape(pattern),rom)] for tag,rom in ROMS.items() if tag in ('stock','2020')}
print(json.dumps(report,indent=2,ensure_ascii=False))
(ROOT/'work/audit_initial_rom_candidates.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
