"""Find changed NPC speech through actual JP/UE map and event pointers."""
import re
from map_layout import ROOT,maps,events,file_offset,word
from gym_text_evidence import english_chars,read_text

ENTRIES=[
    ('GoldenrodDeptStore4F',3,'plain'),
    ('CeladonDeptStore3F',2,'plain'),
    ('CeladonDeptStore3F',3,'plain'),
    ('Route8',4,'trainer'),
    ('SaffronPokeCenter1F',2,'conditional'),
    ('VermilionCity',5,'conditional'),
]


def japanese_chars():
    result={0:'',0x4f:' / ',0x51:' | ',0x55:' / ',0x57:'',0x54:'ポケモン',
            0x7f:' ',0x72:'『',0x73:'』',0x84:'オ'}
    for line in (ROOT/'pokekuristaru/macros/charmap.asm').read_text().splitlines():
        match=re.match(r'\s*charmap "([^"]+)",\s*\$([a-fA-F0-9]+)',line)
        if match and len(match[1])==1 and (0x3040<=ord(match[1])<=0x30ff or match[1] in ' !?.0123456789'):
            result[int(match[2],16)]=match[1]
    result[0x84]='オ'
    result.update({0x1d:'に',0x1e:'って',0x1f:'を',0x22:'た',0x24:'は',0x25:'の',0x4a:'が',
                   0x56:'……',0x71:'っ'})
    return result


def locate(rom,config,perfect=False,japanese=False,layout=None):
    name,index,kind=config
    entry=(layout if layout is not None else maps(rom,perfect))[name]
    person=events(rom,entry['events'])['people'][index]
    bank=entry['bank']
    script=file_offset(bank,word(person,9))
    if kind=='trainer':
        assert person[7]&15==2
        script=file_offset(bank,word(rom,script+10))
        assert rom[script:script+2]==bytes((0x65 if japanese else 0x66,0x47))
        write=script+2
    elif kind=='conditional':
        assert rom[script:script+3]==bytes((0x6a if japanese else 0x6b,0x47,0x31))
        assert rom[script+5]==9
        write=file_offset(bank,word(rom,script+6))
    else:
        assert rom[script:script+2]==bytes((0x6a if japanese else 0x6b,0x47))
        write=script+2
    assert rom[write]==0x4c
    text=file_offset(bank,word(rom,write+1))
    content=read_text(rom,text)
    assert content[0]==0
    return dict(name=name,index=index,bank=bank,script=script,write=write,
                text=text,content=content)


if __name__=='__main__':
    for tag,filename,perfect,japanese in (
        ('JP','Pocket Monsters - Crystal Version (Japan).gbc',False,True),
        ('UE','Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc',False,False),
        ('2020','work/perfect_crystal_ue_patched.gbc',True,False),
    ):
        rom=(ROOT/filename).read_bytes()
        chars=japanese_chars() if japanese else english_chars()
        for config in ENTRIES:
            m=locate(rom,config,perfect,japanese)
            print(tag,config[0],config[1],'bank',hex(m['bank']),'script',hex(m['script']),
                  'write',hex(m['write']),'text',hex(m['text']),'size',len(m['content']))
            print(' ',''.join(chars.get(c,f'<{c:02x}>') for c in m['content']))
