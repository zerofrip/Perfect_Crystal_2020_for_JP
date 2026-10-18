"""Port the released 2020 cave using original Japanese map structures.

All ROM data stays local. Bank $60 contains the extended primary map table,
three cave maps, Japanese text and extended landmark data. Bank $61 contains
the original Japanese Cerulean City scripts plus the added entrance/guard.
"""
from map_layout import ROOT, maps, map_names, events, encode_events, word, file_offset
from japanese_text import encode, dialogue

NEW_BANK = 0x60
CITY_BANK = 0x61


def apply_cave_port(original, english_stock, perfect, output):
    jm, um, pm = maps(original), maps(english_stock), maps(perfect, True)
    ranges = []

    def put(offset, data, label):
        output[offset:offset+len(data)] = data
        ranges.append((offset, len(data), label))

    def new(address, data, label):
        put(file_offset(NEW_BANK, address), data, label)

    for bank in (NEW_BANK, CITY_BANK):
        assert original[bank*0x4000:(bank+1)*0x4000] == bytes(0x4000)

    # Cave and overworld collision/metatile definitions must be the same as
    # those used by the released layouts. Never infer this from tileset IDs.
    for number in ('24', '03'):
        for kind in ('metatiles', 'collision'):
            data = (ROOT / f'pokekuristaru/tilesets/{number}_{kind}.bin').read_bytes()
            assert data in original and data in perfect, (number, kind)

    cave_names = ('CeruleanCave1F', 'CeruleanCave2F', 'CeruleanCaveB1')
    second_addresses = (0x5000, 0x500c, 0x5018)
    block_addresses = (0x5100, 0x5187, 0x520e)
    script_addresses = (0x5400, 0x5440, 0x5480)
    event_addresses = (0x5402, 0x5442, 0x5600)
    headers = {}
    for index, name in enumerate(cave_names):
        ref = pm[name]
        assert (ref['group'], ref['map_id'], ref['height'], ref['width']) == (7,18+index,9,15)
        header = bytearray(ref['header'])
        assert header[1:3] == bytes((24,4)) and header[5] == 56
        assert jm['VictoryRoad']['header'][6] == header[6]  # music ID
        header[0] = NEW_BANK
        header[3:5] = second_addresses[index].to_bytes(2,'little')
        header[5] = 96  # new landmark appended after all original Japanese IDs
        headers[name] = bytes(header)
        attrs = bytearray(ref['attrs'])
        assert attrs[11] == 0
        attrs[3] = NEW_BANK
        attrs[4:6] = block_addresses[index].to_bytes(2,'little')
        attrs[6] = NEW_BANK
        attrs[7:9] = script_addresses[index].to_bytes(2,'little')
        attrs[9:11] = event_addresses[index].to_bytes(2,'little')
        new(second_addresses[index], attrs, name+'_attributes')
        new(block_addresses[index], perfect[ref['blockdata']:ref['blockdata']+135], name+'_blocks')
        event = events(perfect, ref['events'])
        if index < 2:
            assert not event['people'] and not event['xy'] and not event['signposts']
            new(script_addresses[index], bytes(2), name+'_script')
        else:
            assert len(event['people']) == 1
            person = bytearray(event['people'][0])
            assert person[-2:] == bytes.fromhex('0501')
            person[9:11] = (0x548f).to_bytes(2,'little')
            event['people'][0] = person
        new(event_addresses[index], encode_events(event), name+'_events')

    # Every opcode in this event is mapped to the original JP dispatch table.
    # Japanese Crystal lacks English command $52 (farjumptext), so subsequent
    # commands here are one lower. $31/$33 and writecode $1e stay unchanged.
    reference = perfect[pm[cave_names[2]]['script']:pm[cave_names[2]]['script']+40]
    assert reference == bytes.fromhex(
        '0001020e61310501091561906e02906b474c31618496008b0f493305011e030a5d96465f6e026091')
    mewtwo_script = bytes.fromhex(
        '0001028554'       # object callback at $5485
        '310501098c548f'   # check fought flag; return when not fought
        '6d028f'           # disappear; return
        '6a474c0055'       # faceplayer; opentext; Japanese text at $5500
        '8396008a0f49'     # cry; pause; closetext
        '3305011e030a'     # fought flag; force-item battle type
        '5c96465e6d025f90' # Lv70 Mewtwo; battle; disappear; reload; end
    )
    assert len(mewtwo_script) == 40
    new(0x5480, mewtwo_script, 'mewtwo_script_japanese_opcodes')
    new(0x5500, dialogue([
        ['にんげんを みるのは', 'なんねんぶりだろうか'],
        ['わたしが みとめた にんげんは', 'ただ ひとり<......>'],
        ['おまえも そうだとは', 'おもえないな'],
    ]), 'mewtwo_japanese_dialogue')

    # Extend the group-7 primary table without disturbing any original maps.
    primary = bytearray(26*2)
    names = map_names(True)
    for group in range(1,27):
        pointer = 0x4000+len(primary)
        primary[(group-1)*2:group*2] = pointer.to_bytes(2,'little')
        for key, name in names.items():
            if key[0] == group:
                header = bytearray(headers[name] if name in headers else jm[name]['header'])
                if name == 'CeruleanCity':
                    assert pm[name]['header'][8] == 3
                    header[8] = 3
                if name == 'SilverCaveRoom1':
                    assert header[7] == um[name]['header'][7] == 0x14
                    assert pm[name]['header'][7] == 0x12
                    header[7] = 0x12  # released-2020 night palette, no Flash
                primary.extend(header)
    assert len(primary) == 26*2 + 391*9
    new(0x4000, primary, 'extended_primary_map_headers')
    for needle in ('3e25d7cdbf2b', '3e25d7cdb72b'):
        data=bytes.fromhex(needle)
        assert original[:0x4000].count(data) == 1
        address=original.index(data,0,0x4000)+1
        put(address, bytes((NEW_BANK,)), 'primary_map_bank')

    # The existing Japanese scripts retain their CPU addresses in a new bank.
    # Their local references remain valid; only the event table is expanded.
    city = jm['CeruleanCity']
    city_events = events(original, city['events'])
    ref_events = events(perfect, pm['CeruleanCity']['events'])
    assert len(city_events['warps']) == 6 and len(ref_events['warps']) == 7
    assert city_events['warps'] == ref_events['warps'][:6]
    assert len(city_events['people']) == 6 and len(ref_events['people']) == 7
    city_start = city['script'] % 0x4000 + 0x4000
    put(file_offset(CITY_BANK, city_start), original[city['script']:city_events['end']],
        'cerulean_city_original_japanese_scripts')
    city_events['warps'].append(ref_events['warps'][-1])
    # The entrance rebuild moves the hidden Berserk Gene five tiles south.
    # Keep its original JP event flag, item ID and local payload pointer.
    hidden=[]
    for index,sign in enumerate(city_events['signposts']):
        pointer=file_offset(city['bank'],word(sign,3))
        if sign[2]==7 and original[pointer:pointer+3]==bytes.fromhex('fa0098'):
            hidden.append(index)
    assert len(hidden)==1
    hidden_index=hidden[0]
    old_sign=city_events['signposts'][hidden_index]
    ref_sign=ref_events['signposts'][hidden_index]
    assert old_sign[:3]==bytes.fromhex('0c0207')
    assert ref_sign[:3]==bytes.fromhex('110207')
    ref_payload=file_offset(pm['CeruleanCity']['bank'],word(ref_sign,3))
    assert perfect[ref_payload:ref_payload+3]==bytes.fromhex('fa0098')
    city_events['signposts'][hidden_index]=ref_sign[:2]+old_sign[2:]
    guard = bytearray(ref_events['people'][-1])
    assert guard[-2:] == bytes.fromhex('4f07')
    guard[9:11] = (0x4200).to_bytes(2,'little')
    city_events['people'].append(guard)
    put(file_offset(CITY_BANK, 0x4000), encode_events(city_events), 'cerulean_city_extended_events')
    put(file_offset(CITY_BANK, 0x4200), bytes.fromhex('510342') + dialogue([
        ['この どうくつは', 'とても きけんだ'],
    ]), 'cave_guard_japanese_dialogue')
    put(city['secondary']+6, bytes((CITY_BANK,)), 'cerulean_city_script_bank')
    put(city['secondary']+9, bytes.fromhex('0040'), 'cerulean_city_event_pointer')
    # Translate the changed youngster rumour while keeping his itemfinder flow.
    youngster = city_events['people'][5]
    youngster_script = file_offset(CITY_BANK, word(youngster,9))
    assert output[youngster_script:youngster_script+3] == bytes.fromhex('6a474c')
    put(youngster_script+3, (0x4240).to_bytes(2,'little'), 'cerulean_youngster_text_pointer')
    put(file_offset(CITY_BANK,0x4240), dialogue([
        ['むこうの どうくつには', 'とんでもなく つよい'],
        ['ポケモンが いるって', 'うわさを きいたんだ'],
    ]), 'cerulean_youngster_japanese_dialogue')

    for name in ('CeruleanCity', 'Route4'):
        jp, eng, ref = jm[name], um[name], pm[name]
        size=jp['height']*jp['width']
        assert original[jp['blockdata']:jp['blockdata']+size] == english_stock[eng['blockdata']:eng['blockdata']+size]
        put(jp['blockdata'], perfect[ref['blockdata']:ref['blockdata']+size], name+'_entrance_blocks')

    # Append a landmark while preserving all 96 existing Japanese landmark IDs
    # and the exact eleven bytes formerly copied to StringBuffer1.
    old_landmarks = 0x92557
    landmark_table = bytearray()
    landmark_names = bytearray()
    for index in range(97):
        if index < 96:
            entry=old_landmarks+index*4
            coords=original[entry:entry+2]
            old_name=file_offset(0x24,word(original,entry+2))
            name=original[old_name:old_name+11]
        else:
            coords=bytes((106,66))
            name=encode('ハナダのどうくつ@').ljust(11,b'\x50')
        landmark_table.extend(coords+(0x5a00+len(landmark_names)).to_bytes(2,'little'))
        landmark_names.extend(name)
    new(0x5800, landmark_table, 'landmarks_with_cerulean_cave')
    new(0x5a00, landmark_names, 'japanese_landmark_names')
    coords_code=bytes.fromhex('e56b26002929115765192a5f56e1c9')
    name_code=bytes.fromhex('e5d5c56b26002929115965192a666f115bd00e0b2a12130d20fac1d1e1c9')
    for code, address, trampoline, replacement, label in (
        (coords_code,0x5f00,'e5c53e6021005fcfc1e1c9','6b26002929110058192a5f56c9','landmark_coords'),
        (name_code,0x5f20,'e5d5c53e6021205fcfc1d1e1c9','6b26002929110258192a666f115bd00e0b2a12130d20fac9','landmark_name'),
    ):
        assert original.count(code) == 1
        offset=original.index(code)
        put(offset,bytes.fromhex(trampoline).ljust(len(code),b'\x00'),label+'_trampoline')
        new(address,bytes.fromhex(replacement),label+'_reader')

    # Keep every old landmark ID and both cursor limits unchanged, while
    # inserting ID 96 between Cerulean City (55) and Route 24 (56) in the two
    # map viewers. Fly's destination loop remains an independent code path.
    # BC carries each viewer's actual JP cursor address through the far call.
    for address, before_id, after_id, stock_step in (
        (0x6000, 55, 56, '7eba38037b3d7734c9'),
        (0x6040, 56, 55, '7ebb20037a3c7735c9'),
    ):
        helper=bytearray((0x60,0x69,0x7e,0xfe,before_id,0xca))
        helper.extend((address+22).to_bytes(2,'little'))
        helper.extend((0xfe,96,0xca))
        helper.extend((address+25).to_bytes(2,'little'))
        helper.extend(bytes.fromhex(stock_step))
        helper.extend((0x36,96,0xc9,0x36,after_id,0xc9))
        assert len(helper)==28
        new(address,helper,'landmark_cursor_insert_cave')
    cursor_thunks=bytes.fromhex('3e60210060cfc93e60214060cfc9')
    assert original[0x93feb:0x93feb+len(cursor_thunks)]==bytes(len(cursor_thunks))
    assert output[0x93feb:0x93feb+len(cursor_thunks)]==bytes(len(cursor_thunks))
    put(0x93feb,cursor_thunks,'landmark_cursor_far_thunks')
    for up,down,ram in ((0x90fc3,0x90fd0,0xc6d7),(0x91b1f,0x91b2c,0xd003)):
        for position,step,trampoline in ((up,'7eba38037b3d7734',0x7feb),(down,'7ebb20037a3c7735',0x7ff2)):
            before=b'\x21'+ram.to_bytes(2,'little')+bytes.fromhex(step)
            assert original[position:position+11]==before
            replacement=b'\x01'+ram.to_bytes(2,'little')+b'\xcd'+trampoline.to_bytes(2,'little')+bytes(5)
            put(position,replacement,'landmark_cursor_navigation')

    # Three grass and two water records are added by the released IPS. Move the
    # water table into bank-$0a padding to make room for the extended grass table.
    grass=perfect[0x2b274:0x2b884]
    water=perfect[0x2b884:0x2b96f]
    assert len(grass)==33*47+1 and grass[-1]==0xff
    assert len(water)==26*9+1 and water[-1]==0xff
    assert grass[30*47:30*47+2]==bytes((7,18))
    assert original[0x2bd04:0x2bd04+len(water)]==bytes(len(water))
    put(0x2b297,grass,'complete_2020_kanto_grass')
    put(0x2bd04,water,'complete_2020_kanto_water')
    for offset, opcode in ((0x2a03d,0x21),(0x2a21b,0x11)):
        assert original[offset-1:offset+2] == bytes((opcode,0x1a,0x78))
        put(offset,bytes.fromhex('047d'),'kanto_water_pointer')

    return ranges
