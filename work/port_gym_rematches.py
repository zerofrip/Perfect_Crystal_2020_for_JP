"""Local-only port of the released 2020 patch's sixteen leader rematches.

Actual ROM event records and existing flag branches locate the hook sites.
The original Japanese badge, TM, crying, Dragon's Den and Blue arrival paths
remain in place. Only their already-completed conversation tail is redirected.
"""
from hashlib import sha1
import re
from map_layout import ROOT, maps, jp_named_maps, events, file_offset, word
from japanese_text import dialogue
from gym_text_engine import text_engine

PAYLOAD_BANK = 0x62
# map, person index, class, gate command, gate id, Japanese invitation, defeat
GYMS = [
    ('VioletGym',0,1,0x31,8,
     [('それとも いま ここで','うでだめしを してみるかい？')],
     [('くそー！ ぼくは まだ','しゅぎょうが たりないのか……')]),
    ('AzaleaGym',0,3,0x31,9,
     [('もういちど しょうぶして','けんきゅうを てつだってくれる？')],
     [('すごい！ きみは ポケモンの','ことを よく しっているね！'),
      ('ぼくの けんきゅうも','まだまだ これからだね')]),
    ('GoldenrodGym',0,2,0x31,0x0b,
     [('なに？ いま もういっかい','ウチと しょうぶ したいん？')],
     [('ああ また まけてもうた','ぐすん……')]),
    ('EcruteakGym',0,4,0x31,0x0c,
     [('たびで まなんだことを','ぼくに みせて くれないか？')],
     [('ぼくは まだ','ちからが たりないようだ……')]),
    ('CianwoodGym',0,7,0x31,0x0a,
     [('もういちど わしと','しょうぶを してみるか？')],
     [('わしも まだまだ','きたえかたが たりんな……')]),
    ('OlivineGym',0,6,0x31,0x0d,
     [('でも やっぱり……','もういちど あなたに'),
      ('ちょうせん してみたいです！','しょうぶ しませんか？')],
     [('わたしは まだまだ','ちからぶそく ですね……')]),
    ('MahoganyGym',0,5,0x31,0x0e,
     [('もういちど きみたちの','きずなを みせて くれんか？')],
     [('きみたちの きずなは','とても つよい ようじゃな')]),
    ('BlackthornGym1F',0,8,0x31,0x0f,
     [('それとも もういちど','あなたの ちからを みせる？')],
     [('また まけたの！？','そんな はずないわ！')]),
    ('PewterGym',0,0x11,0x34,0x23,
     [('いま ここで おれの','ちからを みせようか？')],
     [('タケシ『おもっていたより','きみは つよいな……')]),
    ('CeruleanGym',1,0x12,0x34,0x24,
     [('もういちど あたしと','しょうぶ していかない？')],
     [('カスミ『やっぱり つよいわね'),
      ('でも ちょうしに','のるんじゃ ないわよ！')]),
    ('VermilionGym',0,0x13,0x34,0x25,
     [('ユー！ もういちど','しょうぶを していきマースか？')],
     [('ユー！ あいかわらず','やりマースね！')]),
    ('CeladonGym',0,0x15,0x31,0xdc,
     [('もういちど たのしく','しょうぶするのも いいですわね')],
     [('あいかわらず おつよいですわ','わたくしの まけです')]),
    ('FuchsiaGym',0,0x1a,0x31,0xdd,
     [('あたいの うでまえを','ためして みてくれないかい？')],
     [('アンズ『あたいも まだまだ','しゅぎょうが ひつようだね……')]),
    ('SaffronGym',0,0x23,0x34,0x28,
     [('その ちからが どれほどか','わたしに みせてくれる？')],
     [('ナツメ『あなたの ちから……','わたしの よちを'),
      ('はるかに こえている……')]),
    ('SeafoamGym',0,0x2e,0x34,0x29,
     [('いま ここで わしの','もえる とうしを みせよう！'),
      ('もういちど しょうぶ するか？')],
     [('カツラ『わしの ほのおが','きえて しまったわい')]),
    ('ViridianGym',0,0x40,0x34,0x2a,
     [('よし いま ここで','もういちど しょうぶ しようぜ！')],
     [('グリーン『くそ！','また まけたのかよ！'),
      ('おまえに まけてばかりじゃ','いられないぜ！')]),
]


def ptr(address):
    return (0x4000 + address % 0x4000).to_bytes(2, 'little')


def localized_text(paragraphs):
    # JP font shares the RI tile ($d8): original Blue speech spells his name
    # 07 d8 e3 ab. The incomplete reference map names that tile only "り".
    return dialogue([tuple(line.replace('？','?').replace('！','!').replace('『','<``>').replace('リ','り') for line in lines)
                     for lines in paragraphs])


def leader_info(rom, layout, config, *, perfect=False, japanese=False):
    name,index,cls,gate,flag,*_=config
    entry=layout[name]
    person=events(rom,entry['events'])['people'][index]
    assert person[7]&15==0, (name,'leader must be a script object')
    start=file_offset(entry['bank'],word(person,9))
    script=rom[start:start+0x110]
    gate_bytes=bytes((gate,flag&0xff,flag>>8,9))
    matches=[m.start() for m in re.finditer(re.escape(gate_bytes),script)]
    if gate==0x34:
        # Later gym-statue scripts repeat this badge test. The leader's
        # faceplayer/opentext prologue fixes its own test at byte two.
        assert matches and matches[0]==2,(name,'leader badge gate moved')
        matches=matches[:1]
    assert len(matches)==1,(name,'ambiguous progress gate',matches)
    gate_offset=start+matches[0]
    tail=file_offset(entry['bank'],word(rom,gate_offset+4))
    expected_end=bytes.fromhex('534990' if japanese else '544991')
    assert rom[tail]==0x4c,(name,'tail must begin writetext',hex(tail))
    trainer=bytes((0x5d if japanese else 0x5e,cls,1,0x5e if japanese else 0x5f))
    assert script.count(trainer)>=1,(name,'original trainer class/party missing')
    rematch=None
    if perfect:
        assert rom[tail+3:tail+5]==bytes.fromhex('4e09'),(name,'released rematch choice missing')
        rematch=file_offset(entry['bank'],word(rom,tail+5))
        assert rom[tail+7:tail+9]==bytes.fromhex('4991')
        assert rom[rematch]==0x64 and rom[rematch+3:rematch+5]==b'\0\0'
        assert rom[rematch+5:rematch+10]==bytes((0x5e,cls,1,0x5f,0x60)),(name,'released rematch party mismatch')
    else:
        assert rom[tail+3:tail+6]==expected_end,(name,'original conversation tail mismatch',hex(tail))
    return dict(name=name,bank=entry['bank'],start=start,gate=gate_offset,
                tail=tail,text=file_offset(entry['bank'],word(rom,tail+1)),rematch=rematch)


def apply_gym_rematches(original, english_stock, perfect, output):
    """Append validated patches to output and return (offset,size,label) ranges."""
    assert sha1(original).hexdigest()=='95127b901bbce2407daf43cce9f45d4c27ef635d'
    refs=english_stock is not None and perfect is not None
    if refs:
        assert sha1(english_stock).hexdigest()=='f2f52230b536214ef7c9924f483392993e226cfb'
        assert sha1(perfect).hexdigest()=='dd00b737fbd18d2e8ae064097a36e8fd4b16855d'
        layouts=[maps(original),maps(english_stock),maps(perfect,True)]
    else:
        layouts=[jp_named_maps(original)]
    text=text_engine(original)
    changed=[]
    cursor=PAYLOAD_BANK*0x4000
    thunk_counts={}
    for config in GYMS:
        name,index,cls,gate,flag,question,defeat=config
        japanese=leader_info(original,layouts[0],config,japanese=True)
        if refs:
            stock=leader_info(english_stock,layouts[1],config)
            released=leader_info(perfect,layouts[2],config,perfect=True)
        bank=japanese['bank']
        # PrintWinLossText obtains the map's script bank, not ScriptBank.
        # Actual JP lacks TX_FAR ($16), so use its existing TX_START_ASM ($08)
        # to call original FarPrintText, then resume at an explicit text end.
        thunk=bank*0x4000+0x3fc0+14*thunk_counts.get(bank,0)
        thunk_counts[bank]=thunk_counts.get(bank,0)+1
        assert thunk+14<=(bank+1)*0x4000
        question_bytes=localized_text(question)
        defeat_bytes=localized_text(defeat)
        # farwritetext original Japanese speech, waitbutton, new invitation,
        # yesorno, iftrue battle; no/cancel -> closetext/end.
        # Explicit end after reload prevents falling into adjacent scripts.
        battle=cursor+14
        question_offset=cursor+25
        defeat_offset=question_offset+len(question_bytes)
        script=(bytes((0x4b,bank))+ptr(japanese['text'])+bytes((0x53,0x4c))+
                ptr(question_offset)+bytes((0x4e,0x09))+ptr(battle)+bytes((0x49,0x90))+
                bytes((0x63,))+ptr(thunk)+b'\0\0'+
                bytes((0x5d,cls,1,0x5e,0x5f,0x90)))
        assert len(script)==25
        payload=script+question_bytes+defeat_bytes
        assert cursor+len(payload)<(PAYLOAD_BANK+1)*0x4000
        patches=[
            (japanese['tail'],bytes((0x04,PAYLOAD_BANK))+ptr(cursor),'rematch choice hook'),
            (thunk,bytes((0x08,0x3e,PAYLOAD_BANK,0x21))+ptr(defeat_offset)+
             bytes((0xcd,))+text['farprint'].to_bytes(2,'little')+
             bytes((0x21,))+ptr(thunk+13)+bytes((0xc9,0x50)),
             'Japanese defeat inline-ASM text thunk'),
            (cursor,payload,'Japanese rematch script and dialogue'),
        ]
        for offset,value,label in patches:
            before=original[offset:offset+len(value)]
            assert output[offset:offset+len(value)]==before,(name,label,'overlapping existing modification',hex(offset))
            if offset!=japanese['tail']:
                assert before==bytes(len(value)),(name,label,'not original zero space')
            output[offset:offset+len(value)]=value
            changed.append((offset,len(value),name+' '+label))
        cursor+=len(payload)
    return changed


if __name__=='__main__':
    original=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
    english=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
    perfect=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
    result=bytearray(original)
    patches=apply_gym_rematches(original,english,perfect,result)
    for offset,size,label in patches:
        print(f'{offset:06x} {size:4d} {label}')
    print('gym_rematches',len(GYMS),'ranges',len(patches),'bytes',sum(p[1] for p in patches))
