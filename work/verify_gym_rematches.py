"""Independent structure/bank validation of the sixteen Japanese rematches."""
from pathlib import Path
import sys
from map_layout import ROOT,maps,events,file_offset,word
from port_gym_rematches import apply_gym_rematches

# Independently recorded original JP script tails and trainer classes, read
# through the original map headers and compared with the released 2020 ROM.
EXPECTED = [
    ('VioletGym',0x61c0a,1),('AzaleaGym',0x73a2a,3),
    ('GoldenrodGym',0x542dd,2),('EcruteakGym',0x61300,4),
    ('CianwoodGym',0x6681b,7),('OlivineGym',0x74c0e,6),
    ('MahoganyGym',0x7e51a,5),('BlackthornGym1F',0x78e4d,8),
    ('PewterGym',0x9bac5,0x11),('CeruleanGym',0x71e5c,0x12),
    ('VermilionGym',0x75fd7,0x13),('CeladonGym',0x6b717,0x15),
    ('FuchsiaGym',0x79911,0x1a),('SaffronGym',0x5acd6,0x23),
    ('SeafoamGym',0x9fd7a,0x2e),('ViridianGym',0x7a9a9,0x40),
]


def inputs():
    return [(ROOT/name).read_bytes() for name in (
        'Pocket Monsters - Crystal Version (Japan).gbc',
        'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc',
        'work/perfect_crystal_ue_patched.gbc')]


def verify(original,patched):
    layout=maps(original)
    for name,tail,cls in EXPECTED:
        bank=layout[name]['bank']
        assert original[tail]==0x4c and original[tail+3:tail+6]==bytes.fromhex('534990')
        assert patched[tail:tail+2]==bytes((4,0x62))
        new=file_offset(0x62,word(patched,tail+2))
        script=patched[new:new+25]
        # Original Japanese speech still refers to the original map's bank.
        assert script[:2]==bytes((0x4b,bank))
        assert script[2:4]==original[tail+1:tail+3]
        assert script[4:6]==bytes((0x53,0x4c))
        assert script[8:10]==bytes((0x4e,0x09))
        assert file_offset(0x62,word(script,10))==new+14
        assert script[12:15]==bytes.fromhex('499063')
        assert script[17:25]==bytes((0,0,0x5d,cls,1,0x5e,0x5f,0x90))
        # Win text MUST resolve in the original map bank, then call the JP
        # FarPrintText routine. JP does not implement English TX_FAR ($16).
        thunk=file_offset(bank,word(script,15))
        assert patched[thunk:thunk+4]==bytes.fromhex('083e6221')
        assert patched[thunk+6:thunk+10]==bytes.fromhex('cd7c3121')
        assert file_offset(bank,word(patched,thunk+10))==thunk+13
        assert patched[thunk+12:thunk+14]==bytes.fromhex('c950')
        question=file_offset(0x62,word(script,6))
        defeat=file_offset(0x62,word(patched,thunk+4))
        assert question==new+25<defeat
        assert patched[question]==patched[defeat]==0
        assert patched[defeat-1]==0x57
        assert 0x57 in patched[defeat:defeat+128]
        # Every old map/header/event record is still byte-for-byte intact.
        m=layout[name]
        for start,end in ((m['primary'],m['primary']+9),(m['secondary'],m['secondary']+12),
                          (m['events'],events(original,m['events'])['end'])):
            assert original[start:end]==patched[start:end],(name,'original map changed')
    print('gym_structure_verified',len(EXPECTED),'leaders; Japanese text bank thunks valid')


if __name__=='__main__':
    original,english,perfect=inputs()
    if len(sys.argv)>1:
        patched=Path(sys.argv[1]).read_bytes()
    else:
        patched=bytearray(original)
        ranges=apply_gym_rematches(original,english,perfect,patched)
        allowed=set()
        for offset,size,label in ranges:
            allowed.update(range(offset,offset+size))
        assert all(i in allowed for i,(a,b) in enumerate(zip(original,patched)) if a!=b)
        # Refuse applying twice or touching any nonzero payload destination.
        try:
            apply_gym_rematches(original,english,perfect,patched)
        except AssertionError:
            pass
        else:
            raise AssertionError('overlap guard failed')
    verify(original,patched)
