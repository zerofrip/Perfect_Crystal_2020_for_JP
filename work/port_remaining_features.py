"""Initial Perfect-import features confirmed in the released 2020 ROM.

The original Japanese trade records are 16 bytes with four-character nicknames.
Only Dodrio needs the normal six-byte party-name capacity; its copy call uses a
local helper. Existing Japanese trainer names, OT names and trade data stay local.
"""
from map_layout import maps, events, file_offset, word
from japanese_text import encode

TRADE_JP=0xfce57
TRADE_UE=0xfce58
TRADE_HELPER=0xfff80


def unique(rom,needle):
    at=rom.find(needle)
    assert at>=0 and rom.find(needle,at+1)<0,('missing/ambiguous',needle.hex())
    return at


def guard_info(rom,perfect=False):
    entry=maps(rom,perfect)['SilphCo1F']
    person=events(rom,entry['events'])['people'][1]
    script=file_offset(entry['bank'],word(person,9))
    return entry,script


def apply_remaining_features(original,english_stock,perfect,output):
    ranges=[]
    def put(offset,before,after,label):
        assert len(before)==len(after)
        assert original[offset:offset+len(before)]==before,('preimage',label)
        assert output[offset:offset+len(before)]==before,('overlap',label)
        output[offset:offset+len(after)]=after
        ranges.append((offset,len(after),label))

    hp_jp=bytes.fromhex('cd5846c1d1e17b2122d2be28c8')
    hp_stock=bytes.fromhex('cd9946c1d1e17b21f1d1be28c8')
    hp_2020=bytes.fromhex('cd99467bc1d1e121f1d1be28c8')
    assert unique(original,hp_jp)==0xd99d
    assert unique(english_stock,hp_stock)==unique(perfect,hp_2020)==0xd720
    put(0xd9a0,hp_jp[3:7],hp_2020[3:7],'hp_pixel_result_before_restore')

    party_jp=bytes.fromhex('115bd03e10010a00cd770e215bd02aa728142323fe02')
    party_ue=bytes.fromhex('1173d03e10010a00cd8d0e2173d02aa728142323fe02')
    party_new=party_ue[:6]+b'\x10'+party_ue[7:]
    assert unique(original,party_jp)==0x50277
    assert unique(english_stock,party_ue)==unique(perfect,party_new)==0x50279
    put(0x5027d,b'\x0a',b'\x10','party_item_evolution_scan_16_bytes')

    dvs_anchor=bytes.fromhex('9a778888988898889888988898887cdddddd9888dcdddcdd')
    jp_dvs=unique(original,dvs_anchor)
    ue_dvs=unique(english_stock,dvs_anchor)
    perfect_dvs=unique(perfect,dvs_anchor)
    assert (jp_dvs,ue_dvs,perfect_dvs)==(0x2742f,0x270d6,0x270d6)
    before=original[jp_dvs:jp_dvs+134]
    assert before==english_stock[ue_dvs:ue_dvs+134]
    expected=bytearray(before);expected[124:126]=b'\xff\xff'
    assert perfect[perfect_dvs:perfect_dvs+134]==expected
    put(jp_dvs+124,b'\xfd\xde',b'\xff\xff','red_maximum_dvs')

    old_trades=english_stock[TRADE_UE:TRADE_UE+7*32]
    new_trades=perfect[TRADE_UE:TRADE_UE+7*32]
    changed=[]
    for index in range(7):
        old=old_trades[index*32:(index+1)*32]
        new=new_trades[index*32:(index+1)*32]
        jp=original[TRADE_JP+index*16:TRADE_JP+(index+1)*16]
        assert old[:3]==new[:3]==jp[:3]
        assert old[14:19]==new[14:19]==jp[7:12]
        assert old[30]==new[30]==jp[15]
        assert old[19:]==new[19:]
        if old!=new:changed.append(index)
    assert changed==[3,5]
    assert old_trades[99:110]==bytes.fromhex('838e918892505050505050')
    assert new_trades[99:110]==bytes.fromhex('838e8391888e5050505050')
    assert old_trades[163:174]==bytes.fromhex('8084918e98505050505050')
    assert new_trades[163:174]==bytes.fromhex('8084918e83808293988b50')
    put(TRADE_JP+5*16+3,bytes.fromhex('42ac90e3'),encode('プテラ')+b'\x50',
        'trade_aerodactyl_japanese_species_nickname')

    # JP original nickname-copy helper copies exactly four glyphs. This is its
    # sole caller; the received Dodrio name is five glyphs plus terminator.
    call_context=bytes.fromhex('1e03cdc24d11f5c6cdfa4d21e9dd010600')
    call_context_offset=unique(original,call_context)
    call_offset=call_context_offset+8
    assert call_offset==0xfcd2a
    assert original[0xfc000:0x100000].count(bytes.fromhex('cdfa4d'))==1
    # The reference map exposes リ as り ($d8) and omits オ ($84). Both tile
    # values are confirmed in the original Japanese Dodrio species-name entry.
    dodrio=encode('ドードり')+bytes((0x84,0x50))
    assert original.count(dodrio[:5])>=1
    assert len(dodrio)==6
    helper=bytes.fromhex('fa57cfe60ffe03200d21997f010500cdf22f3e5012c9c3fa4d')+dodrio
    assert len(helper)==31
    assert helper[25:]==dodrio
    put(TRADE_HELPER,bytes(len(helper)),helper,'trade_dodrio_five_character_copy')
    put(call_offset,bytes.fromhex('cdfa4d'),bytes.fromhex('cd807f'),'trade_nickname_copy_hook')

    jp_map,jp_script=guard_info(original)
    ue_map,ue_script=guard_info(english_stock)
    new_map,new_script=guard_info(perfect,True)
    assert (jp_script,ue_script,new_script)==(0x5b74a,0x18abe8,0x18ac78)
    jp_flow=bytes.fromhex('6a4731de00095f774c8a77549dac0108637733de004ccb77534990')
    assert original[jp_script:jp_script+len(jp_flow)]==jp_flow
    assert english_stock[ue_script:ue_script+8]==bytes.fromhex('6b4731de0009fd6b')
    assert perfect[new_script:new_script+3]==bytes.fromhex('51ae6c')
    jp_text=file_offset(jp_map['bank'],word(jp_flow,9))
    old_text=file_offset(ue_map['bank'],word(english_stock,ue_script+9))
    new_text=file_offset(new_map['bank'],word(perfect,new_script+1))
    english_end=english_stock.index(0x51,old_text)
    english_first=english_stock[old_text:english_end]+b'\x57'
    assert perfect[new_text:new_text+len(english_first)]==english_first
    # The original Japanese first paragraph is already the exact translation.
    japanese_end=original.index(0x51,jp_text)
    assert jp_text==0x5b78a
    put(jp_script,jp_flow[:3],bytes((0x51,word(jp_flow,9)&255,word(jp_flow,9)>>8)),
        'silph_guard_conversation_without_upgrade')
    put(japanese_end,b'\x51',b'\x57','silph_guard_end_after_employee_notice')
    return ranges


if __name__=='__main__':
    from map_layout import ROOT
    import json
    original=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
    english=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
    perfect=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
    output=bytearray(original)
    ranges=apply_remaining_features(original,english,perfect,output)
    print(json.dumps(ranges,indent=2))
    (ROOT/'work/remaining_isolated.gbc').write_bytes(output)
    (ROOT/'work/remaining_ranges.json').write_text(json.dumps(ranges,indent=2)+'\n')
