"""Independent ROM-level checks for the bounded initial-import feature port."""
from pathlib import Path
import sys
from map_layout import ROOT,word,file_offset,maps,events
from japanese_text import encode
from port_remaining_features import apply_remaining_features
from gym_text_evidence import read_text


def inputs():
    return tuple((ROOT/name).read_bytes() for name in (
        'Pocket Monsters - Crystal Version (Japan).gbc',
        'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc',
        'work/perfect_crystal_ue_patched.gbc'))


def verify(jp,patched):
    assert patched[0xd99d:0xd9a7]==bytes.fromhex('cd58467bc1d1e12122d2')
    assert patched[0x5027c:0x5027f]==bytes.fromhex('011000')
    before=jp[0x2742f:0x274b5]
    after=patched[0x2742f:0x274b5]
    assert before[:124]==after[:124] and before[126:]==after[126:]
    assert after[124:126]==b'\xff\xff'
    assert patched[0xfceaa:0xfceae]==bytes.fromhex('4292a550') # プテラ@
    assert patched[0xfcd2a:0xfcd2d]==bytes.fromhex('cd807f')
    assert patched[0xfff99:0xfff9f]==bytes.fromhex('13e313d88450') # ドードリオ@
    # Party nickname buffers remain the original six bytes and ordinary
    # four-character trade nicknames retain the original copy helper.
    assert patched[0xfcdfa:0xfce04]==jp[0xfcdfa:0xfce04]
    assert patched[0xfcd2d:0xfcd39]==jp[0xfcd2d:0xfcd39]
    assert patched[0x5b74a:0x5b74d]==bytes.fromhex('518a77')
    old=read_text(jp,0x5b78a)
    new=read_text(patched,0x5b78a)
    assert new==old.split(b'\x51',1)[0]+b'\x57'
    # Every non-nickname trade field is unchanged in all seven records.
    for index in range(7):
        start=0xfce57+16*index
        old=jp[start:start+16];new=patched[start:start+16]
        assert old[:3]==new[:3] and old[7:]==new[7:]
        assert index==5 or old==new
    print('remaining_features_verified',5,'feature groups; 67 DV classes and 7 trade records checked')


if __name__=='__main__':
    j,u,p=inputs()
    if len(sys.argv)>1:
        out=Path(sys.argv[1]).read_bytes()
    else:
        out=bytearray(j)
        ranges=apply_remaining_features(j,u,p,out)
        allowed={i for off,size,_ in ranges for i in range(off,off+size)}
        assert all(i in allowed for i,(a,b) in enumerate(zip(j,out)) if a!=b)
    verify(j,out)
