"""Check all actual-ROM sprite assets and Jynx's complete animation tile maps."""
import json
from port_restored_sprites import (ROOT,PIC_POINTERS,TRAINER_POINTERS,
    RESTORED_TRAINERS,picture,jynx_frames,apply_restored_sprites)
jp=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
stock=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
perfect=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
output=bytearray(jp)
ranges=apply_restored_sprites(jp,stock,perfect,output)
allowed={i for a,n,_ in ranges for i in range(a,a+n)}
assert len(allowed)==sum(n for _,n,_ in ranges)
assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(jp,output)))

for name,index in RESTORED_TRAINERS:
    pointer=TRAINER_POINTERS+(index-1)*3
    assert picture(output,pointer)[2]==picture(perfect,pointer)[2],name
for index in range(67):
    if index==38:continue
    pointer=TRAINER_POINTERS+index*3
    assert output[pointer:pointer+3]==jp[pointer:pointer+3]
    assert picture(output,pointer)[2]==picture(jp,pointer)[2],index+1
for species in range(251):
    for side in range(2):
        pointer=PIC_POINTERS+species*6+side*3
        if species==123 and side==0:
            assert picture(output,pointer)[2]==picture(perfect,pointer)[2]
        else:
            assert output[pointer:pointer+3]==jp[pointer:pointer+3]
            if output[pointer:pointer+3]==bytes((255,255,255)):
                assert species==200,('unexpected empty pointer',species+1,side)
            else:
                assert 0x4000<=int.from_bytes(output[pointer+1:pointer+3],'little')<0x8000, (species+1,side,output[pointer:pointer+3].hex())
                assert picture(output,pointer)[2]==picture(jp,pointer)[2],(species+1,side)
for index in range(26*2):
    pointer=0x124000+index*3
    assert output[pointer:pointer+3]==jp[pointer:pointer+3]
    assert picture(output,pointer)[2]==picture(jp,pointer)[2],('unown',index)

def rendered_tiles(rom):
    """Reconstruct frame tile selections using the ROM bitmask and tile IDs."""
    image=picture(rom,PIC_POINTERS+123*6)[2]
    assert len(image)%16==0
    count=len(image)//16
    result=[image[:36*16]]
    for mask,replacements in jynx_frames(rom):
        indices=list(range(36)); replacement=iter(replacements)
        for bit in range(40):
            if mask[bit//8] & (1 << (bit%8)):
                assert bit<36
                index=next(replacement)
                assert index<count
                indices[bit]=index
        assert next(replacement,None) is None
        result.append(b''.join(image[i*16:i*16+16] for i in indices))
    return result

assert jynx_frames(output)==jynx_frames(perfect)
assert rendered_tiles(output)==rendered_tiles(perfect)
assert output[0xD4000:0xD40F6]==jp[0xD4000:0xD40F6]
assert output[0xD40F8:0xD41F6]==jp[0xD40F8:0xD41F6]
assert output[0xA88B:0xB198]==jp[0xA88B:0xB198]  # original JP palettes
assert output[0xD0695:0xD24EF]==jp[0xD0695:0xD24EF]  # animation commands
(ROOT/'work/sprite_isolated.gbc').write_bytes(output)
(ROOT/'work/sprite_ranges.json').write_text(json.dumps(ranges,indent=2)+'\n')
print('sprite checks passed:',len(ranges),'write ranges, all 251 species / 67 trainers; Jynx base+3 frames match actual 2020')
