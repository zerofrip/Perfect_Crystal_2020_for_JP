"""Port the released sprite assets, retaining Japanese-only names and text.

The released Jynx front image has 55 tiles rather than Japan's 54; its third
frame and bitmask must travel with it. Animations and palettes already match.
"""
from pc_env import workspace
from hashlib import sha1
from pathlib import Path
import sys

ROOT=workspace()
sys.path.insert(0,str(ROOT/'work/pokemon-reverse-engineering-tools'))
from pokemontools.lz import Decompressed
Decompressed.__next__=Decompressed.next
SPRITE_BANK=0x64
FRAME_CAVE=0xD6240
PIC_POINTERS=0x120000
TRAINER_POINTERS=0x128000
JYNX=124
RESTORED_TRAINERS=(('beauty',29),('sage',56),('medium',57),('swimmer_f',39),('fisher',37))


def word(data,offset):return int.from_bytes(data[offset:offset+2],'little')
def banked(bank,address):
    assert 0x4000<=address<0x8000
    return bank*0x4000+address-0x4000


def picture(rom,pointer):
    offset=banked(rom[pointer]+0x36,word(rom,pointer+1))
    decoded=Decompressed(rom,start=offset)
    return offset,bytes(decoded.compressed_data),bytes(decoded.output)


def jynx_frames(rom):
    """Read the actual frame pointers and bitmask tile counts, not source ASM."""
    frame_table=banked(0x35,word(rom,0xD40F6))
    mask_table=banked(0x34,word(rom,0xD25E5))
    frames=[]
    for i in range(3):
        frame=banked(0x35,word(rom,frame_table+2*i))
        mask_id=rom[frame]
        assert mask_id<3
        mask=rom[mask_table+5*mask_id:mask_table+5*mask_id+5]
        count=sum(b.bit_count() for b in mask)
        frames.append((mask,bytes(rom[frame+1:frame+1+count])))
    return frames


def apply_restored_sprites(original,english_stock,perfect,output):
    assert sha1(original).hexdigest()=='95127b901bbce2407daf43cce9f45d4c27ef635d'
    assert sha1(english_stock).hexdigest()=='f2f52230b536214ef7c9924f483392993e226cfb'
    assert sha1(perfect).hexdigest()=='dd00b737fbd18d2e8ae064097a36e8fd4b16855d'
    assert len(output)==len(original)==0x200000
    ranges=[]

    def write(offset,before,after,label):
        assert len(before)==len(after)
        assert original[offset:offset+len(before)]==before,label
        assert output[offset:offset+len(before)]==before,('overlap',label)
        output[offset:offset+len(after)]=after
        ranges.append((offset,len(after),label))

    # Actual FixPicBank uses a table, not arithmetic. Retain all 24 original
    # entries and extend it through bank $64 before referencing new assets.
    assert original[0x5125B:0x5126A]==bytes.fromhex('e5c5d6124f0600216a52097ec1e1c9')
    assert original[0x5126A:0x51282]==bytes(range(0x48,0x60))
    table=bytes(range(0x48,SPRITE_BANK+1))
    write(0x539C4,bytes(len(table)),table,'extended_picture_banks')
    write(0x51263,bytes.fromhex('6a52'),bytes.fromhex('c479'),'picture_bank_table_pointer')

    # Verify table addresses from the real animation engine's instructions.
    for rom in (original,english_stock,perfect):
        assert rom[0xD0561:0xD0576]==bytes.fromhex('0e3421296211d163cdec4228080e3421954611a356')
        assert rom[0xD05E2:0xD05EF]==bytes.fromhex('fe9806350e3521004038020e36')
        assert rom[0xD0623:0xD062F]==bytes.fromhex('3e3421d37a28053e3421ef64')
    assert original[0x97AB:0x97B6]==bytes.fromhex('6f2600292929018b6809c9')
    assert perfect[0x97EE:0x97F9]==bytes.fromhex('6f260029292901ce6809c9')
    assert original[0xA88B+124*8:0xA88B+125*8]==perfect[0xA8CE+124*8:0xA8CE+125*8]
    assert original[0x9728:0x9732]==bytes.fromhex('6f26002929018b7009c9')
    assert perfect[0x976B:0x9775]==bytes.fromhex('6f2600292901ce7009c9')
    for _,index in RESTORED_TRAINERS:
        assert original[0xB08B+index*4:0xB08B+index*4+4]==perfect[0xB0CE+index*4:0xB0CE+index*4+4]
    for table,size in ((0xD0695,13),(0xD16A3,9)):
        a=banked(0x34,word(original,table+123*2))
        b=banked(0x34,word(perfect,table+123*2))
        assert original[a:a+size]==perfect[b:b+size]

    cursor=SPRITE_BANK*0x4000
    assert original[cursor:cursor+0x4000]==bytes(0x4000)
    # Everything claimed restored in the release is compared after decompress.
    targets=[(name,TRAINER_POINTERS+(index-1)*3) for name,index in RESTORED_TRAINERS]
    targets += [('jynx_front',PIC_POINTERS+123*6),('jynx_back',PIC_POINTERS+123*6+3)]
    changed=[]
    for name,pointer in targets:
        _,old,plain=picture(original,pointer)
        _,compressed,expected=picture(perfect,pointer)
        if plain==expected:
            continue
        assert name in ('swimmer_f','jynx_front'),name
        assert picture(english_stock,pointer)[2] != expected,('not a release change',name)
        write(cursor,bytes(len(compressed)),compressed,name+'_compressed')
        address=0x4000+cursor%0x4000
        new_pointer=bytes((SPRITE_BANK-0x36,address&255,address>>8))
        write(pointer,original[pointer:pointer+3],new_pointer,name+'_pointer')
        cursor+=len(compressed)
        changed.append(name)
    assert changed==['swimmer_f','jynx_front']

    expected_frames=jynx_frames(perfect)
    old_frames=jynx_frames(original)
    assert old_frames[:2]==expected_frames[:2]
    assert [len(x[1]) for x in old_frames]==[10,5,3]
    assert [len(x[1]) for x in expected_frames]==[10,5,4]
    # Frame addresses are bank-local, so relocate their tiny table in bank $35.
    block=bytearray(6)
    for i,(mask,tiles) in enumerate(expected_frames):
        address=0x4000+(FRAME_CAVE+len(block))%0x4000
        block[i*2:i*2+2]=address.to_bytes(2,'little')
        block+=bytes((i,))+tiles
    assert len(block)==28
    write(FRAME_CAVE,bytes(len(block)),block,'jynx_animation_frames')
    write(0xD40F6,bytes.fromhex('d85b'),bytes.fromhex('4062'),'jynx_frames_pointer')
    old_masks=b''.join(mask for mask,_ in old_frames)
    new_masks=b''.join(mask for mask,_ in expected_frames)
    assert old_masks[:11]==new_masks[:11] and old_masks[12:]==new_masks[12:]
    assert (old_masks[11],new_masks[11])==(0x20,0x60)
    write(0xD30D4,b'\x20',b'\x60','jynx_frame3_bitmask')
    return ranges
