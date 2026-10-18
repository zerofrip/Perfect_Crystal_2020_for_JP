"""Small 2020 fixes verified against actual JP and released English ROMs."""

def apply_misc_fixes(original, english_stock, perfect, output):
    ranges=[]
    def put(offset,before,after,label):
        assert len(before)==len(after)
        assert original[offset:offset+len(before)]==before,label
        assert output[offset:offset+len(before)]==before,('overlap',label)
        output[offset:offset+len(after)]=after
        ranges.append((offset,len(after),label))

    # Keep the original function entry and all JP RAM/call addresses. The
    # released additional Z branch uses the CPU flags from SBC, exactly as-is.
    old_loop=bytes.fromhex('7dd6306f7cde006738030418f3')
    new_loop=bytes.fromhex('7dd6306f7cde0067280538030418f1')
    assert original.count(old_loop)==1 and original.find(old_loop)==0xdaa6
    assert english_stock[0xd851:0xd85e]==old_loop
    assert perfect[0xd851:0xd860]==new_loop
    hp_loop=new_loop+bytes.fromhex('c3b35a')
    put(0xff2c,bytes(len(hp_loop)),hp_loop,'short_hp_bar_zero_branch')
    put(0xdaa6,old_loop[:3],bytes.fromhex('c32c7f'),'short_hp_bar_loop_entry')

    old_slot=bytes.fromhex('fa58cfe607c8116700cdb03bc9')
    assert original[0x92f3b:0x92f3b+len(old_slot)]==old_slot
    assert english_stock[0x929cd]==0xc8 and perfect[0x929cd]==0xc0
    put(0x92f40,b'\xc8',b'\xc0','slot_payout_sound_interval')

    # JP retains two copies of this data path. Relocate both table references;
    # no following code or pre-existing callers move.
    assert english_stock[0x746b:0x746e]==bytes.fromhex('ff0212')
    assert perfect[0x7451:0x7457]==bytes.fromhex('800212ff0212')
    for operand,old in ((0x7dba,0x7e07),(0x7e1d,0x7e6a)):
        assert original[operand-1]==0x21
        assert original[old:old+3]==bytes.fromhex('ff0212')
        put(operand,old.to_bytes(2,'little'),bytes.fromhex('807f'),'daisy_massage_table_pointer')
    put(0x7f80,bytes(6),bytes.fromhex('800212ff0212'),'daisy_massage_full_random_range')

    music=bytes.fromhex('113100fe1f284cfe422848')
    assert original.count(music)==1 and original.find(music)==0x2fd66
    assert english_stock[0x2eebe:0x2eec9]==music
    assert perfect[0x2ee7e:0x2ee95]==bytes.fromhex('113100fe1f2858fe422854fe332850fe37284cfe142848')
    helper=bytearray.fromhex('113100')
    for trainer in (0x1f,0x42,0x33,0x37,0x14):
        helper.extend((0xfe,trainer,0xca,0xb9,0x7d))
    helper.extend(bytes.fromhex('c3717d'))
    put(0x2fe50,bytes(len(helper)),helper,'rocket_admin_scientist_music')
    put(0x2fd66,music[:3],bytes.fromhex('c3507e'),'rocket_music_entry')

    # Japanese uses one shared number-print command for both EXP messages.
    text=bytes.fromhex('0966d024007fb9b2b9dec11fd3d7dfc0e758')
    assert original.count(text)==1 and original.find(text)==0x3f14a
    for offset in (0x1c02b6,0x1c02cc):
        assert english_stock[offset:offset+4]==bytes.fromhex('0986d024')
        assert perfect[offset:offset+4]==bytes.fromhex('0986d025')
    put(0x3f14d,b'\x24',b'\x25','five_digit_experience_display')

    ditto=bytes.fromhex('843030303030300000233d0000ff641405550000000000dd0000000000000000')
    assert original.count(ditto)==1 and original.find(ditto)==0x5251a
    assert english_stock[0x52484:0x52484+len(ditto)]==ditto
    expected=bytearray(ditto);expected[12]=0x23
    assert perfect[0x52484:0x52484+len(ditto)]==expected
    put(0x52526,b'\x00',b'\x23','ditto_metal_powder_held_item')
    # Released 2020 additionally reduces Mew's catch rate from 45 to 3.
    # This is absent from the older public source, found by all-251 audit.
    mew=bytes.fromhex('9764646464646418182d40006dff647805550000000003ffffffffffffffff0f')
    jp_mew=0x5251a+(151-132)*32
    ue_mew=0x52484+(151-132)*32
    assert original[jp_mew:jp_mew+32]==mew
    assert english_stock[ue_mew:ue_mew+32]==mew
    changed=bytearray(mew);changed[9]=3
    assert perfect[ue_mew:ue_mew+32]==changed
    put(jp_mew+9,b'\x2d',b'\x03','mew_released_2020_catch_rate')
    return ranges

if __name__=='__main__':
    from map_layout import ROOT
    j=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
    u=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
    p=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
    output=bytearray(j)
    print(apply_misc_fixes(j,u,p,output))
    (ROOT/'work/misc_isolated.gbc').write_bytes(output)
