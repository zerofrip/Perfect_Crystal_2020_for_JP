"""Print only local semantic NPC-trade data and guard text for port planning."""
from map_layout import ROOT
from dialogue_mapping import japanese_chars
from gym_text_evidence import read_text
import re

for label,filename in [('jp','Pocket Monsters - Crystal Version (Japan).gbc'),('ue','Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc'),('2020','work/perfect_crystal_ue_patched.gbc')]:
    rom=(ROOT/filename).read_bytes()
    print(label)
    for pat in (rb'\x77\x66.\x1b\x01',rb'\x96\x66.\x7b\x67'):
        for m in re.finditer(pat,rom,re.DOTALL):
            i=m.start()
            print(hex(i),rom[i-16:i+24].hex())
    if label=='jp':
        for i in range(0xfce40,0xfced0,16):print(hex(i),rom[i:i+16].hex(' '))
        print('Silph text',read_text(rom,0x5b78a).hex())
        charmap=japanese_chars()
        print('near_trade_decode',''.join(charmap.get(x,f'<{x:02x}>') for x in rom[0xfd000:0xfd100]))
