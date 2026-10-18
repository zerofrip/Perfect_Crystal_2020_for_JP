"""Read-only checks against the three local, actual ROMs."""
from map_layout import ROOT
import re

roms = {
    'jp': (ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes(),
    'stock': (ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes(),
    '2020': (ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes(),
}
patterns = {
    'short_hp': rb'\x7d\xd6\x30\x6f\x7c\xde\x00\x67',
    'slot_payout': rb'\xe6\x07[\xc0\xc8]\x11..\xcd..\xc9',
    'daisy_table': bytes.fromhex('4c0205800306ff04079a02084c0309ff040a'),
    'rocket_music': rb'\x11..\xfe\x1f\x28.\xfe\x42\x28.',
    'exp_digits': rb'\x09..[\x24\x25]',
}
for key, pattern in patterns.items():
    print(key)
    for label, rom in roms.items():
        matches=list(re.finditer(pattern,rom,re.DOTALL))
        print(label, [(hex(m.start()),rom[max(0,m.start()-8):m.end()+20].hex()) for m in matches][:35], 'count',len(matches))

for asset in ('trainers/beauty','trainers/sage','trainers/medium','trainers/swimmer_f','trainers/fisher','pics/jynx/front','pics/jynx/back'):
    path=ROOT/f'perfect_crystal_source/gfx/{asset}.2bpp.lz'
    data=path.read_bytes()
    print('sprite',asset,'compressed',len(data),{k:(hex(v.find(data)),v.count(data)) for k,v in roms.items()})
