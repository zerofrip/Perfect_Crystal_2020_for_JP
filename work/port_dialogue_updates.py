"""Keep Japanese NPC explanations consistent with the released 2020 changes."""
from hashlib import sha1
from map_layout import ROOT,jp_named_maps
from japanese_text import dialogue,encode
from dialogue_mapping import ENTRIES,locate
from gym_text_evidence import english_chars
from gym_text_engine import text_engine

TEXT_BANK=0x65
IDS=('goldenrod_stones','celadon_item','celadon_porygon',
     'route8_badges','saffron_caves','vermilion_badges')


def assert_released_change(index,old,new):
    chars=english_chars()
    decode=lambda raw:' '.join(''.join(chars.get(c,'') for c in raw).replace('/',' ').replace('|',' ').split())
    before,after=decode(old),decode(new)
    checks=(
        ('Game Link cable.','the use of a stone.'),
        ('UP- GRADE','the item from it.'),
        ('The traded PORYGON','never get enough coins'),
        ('advantages in battles.','an experienced trainer.'),
        ('outside CERULEAN.','shrunk in the past few years.'),
        ('the KANTO GYM BADGES','should give you an edge in battle.'),
    )
    absent,present=checks[index]
    # Original English wraps "outside" as "out-" / "side".
    before=before.replace('out- side','outside')
    assert absent in before,(IDS[index],'stock text evidence missing',before)
    assert absent not in after and present in after,(IDS[index],'released text evidence missing',after)


def updated_text(index,old):
    assert old[0]==0 and old[-1]==0x57
    parts=old[1:-1].split(b'\x51')
    if index==0:
        assert len(parts)==2 and parts[0].startswith(encode('つうしんケーブル'))
        parts[0]=dialogue([('いしを つかうことで','しんか する ポケモンも いるよ')])[1:-1]
    elif index==1:
        before,after=encode('アップグレード'),encode('どうぐ')
        assert old.count(before)==1
        return old.replace(before,after)
    elif index==2:
        assert len(parts)==4 and encode('ポ') in parts[3]
        parts=parts[:2]
    elif index==3:
        return dialogue([('ジムバッジは','けいけん ゆたかな','トレーナーの あかしだよ')])
    elif index==4:
        assert len(parts)==3 and encode('ハナダ') in parts[1]
        parts[1]=dialogue([('ここすうねんで ちいさくなった','どうくつも いくつか あるんだよ!')])[1:-1]
    else:
        assert index==5 and len(parts)==2 and encode('カントー') in parts[1]
        parts=parts[:1]
    return b'\x00'+b'\x51'.join(parts)+b'\x57'


def apply_dialogue_updates(original,english_stock,perfect,output):
    assert sha1(original).hexdigest()=='95127b901bbce2407daf43cce9f45d4c27ef635d'
    refs=english_stock is not None and perfect is not None
    if refs:
        assert sha1(english_stock).hexdigest()=='f2f52230b536214ef7c9924f483392993e226cfb'
        assert sha1(perfect).hexdigest()=='dd00b737fbd18d2e8ae064097a36e8fd4b16855d'
    engine=text_engine(original)
    jp_layout=jp_named_maps(original)
    changes=[]
    cursor=TEXT_BANK*0x4000
    for index,config in enumerate(ENTRIES):
        jp=locate(original,config,japanese=True,layout=jp_layout)
        if refs:
            en=locate(english_stock,config)
            release=locate(perfect,config,perfect=True)
            assert_released_change(index,en['content'],release['content'])
        replacement=updated_text(index,jp['content'])
        if len(replacement)<=len(jp['content']):
            writes=[(jp['text'],replacement,'Japanese explanation')]
        else:
            # Original JP has no text_far $16. Existing text_start_asm $08
            # calls real FarPrintText and returns to a local text terminator.
            assert len(jp['content'])>=14
            local=0x4000+jp['text']%0x4000
            address=0x4000+cursor%0x4000
            thunk=(bytes((8,0x3e,TEXT_BANK,0x21))+address.to_bytes(2,'little')+
                   bytes((0xcd,))+engine['farprint'].to_bytes(2,'little')+
                   bytes((0x21,))+(local+13).to_bytes(2,'little')+bytes((0xc9,0x50)))
            assert original[cursor:cursor+len(replacement)]==bytes(len(replacement))
            writes=[(jp['text'],thunk,'Japanese explanation text thunk'),
                    (cursor,replacement,'Japanese explanation payload')]
            cursor+=len(replacement)
            assert cursor<=(TEXT_BANK+1)*0x4000
        for offset,value,label in writes:
            assert output[offset:offset+len(value)]==original[offset:offset+len(value)],(IDS[index],'overlap',hex(offset))
            output[offset:offset+len(value)]=value
            changes.append((offset,len(value),IDS[index]+' '+label))
    return changes


if __name__=='__main__':
    original=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
    en=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
    perfect=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
    output=bytearray(original)
    changes=apply_dialogue_updates(original,en,perfect,output)
    for offset,length,label in changes:
        print(f'{offset:06x} {length:3} {label}')
    print('dialogue_updates',len(ENTRIES),'ranges',len(changes),'bytes',sum(c[1] for c in changes))
