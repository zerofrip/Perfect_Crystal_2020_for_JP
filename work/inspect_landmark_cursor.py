from map_layout import ROOT
import re
for label, filename in (('jp','Pocket Monsters - Crystal Version (Japan).gbc'),('2020','work/perfect_crystal_ue_patched.gbc')):
    rom=(ROOT/filename).read_bytes()
    for direction,pattern in (('up','7eba38037b3d7734'),('down','7ebb20037a3c7735')):
        for m in re.finditer(re.escape(bytes.fromhex(pattern)),rom[0x90000:0x94000]):
            pos=0x90000+m.start()
            print(label,direction,hex(pos),rom[pos-3:pos+18].hex())
