"""Compare complete encounter records in the actual integrated JP artifact."""
from map_layout import ROOT
jp=(ROOT/'work/development_only_jp_partial.gbc').read_bytes()
pc=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
for name,a,b,count,width in (
    ('johto_grass',0x2a60c,0x2a5e9,61,47),
    ('johto_water',0x2b140,0x2b11d,38,9),
    ('kanto_grass',0x2b297,0x2b274,33,47),
    ('kanto_water',0x2bd04,0x2b884,26,9),
):
    size=count*width+1
    assert jp[a:a+size]==pc[b:b+size],name
    assert jp[a+size-1]==0xff
    print(name,'records',count,'match_released_2020',True)
