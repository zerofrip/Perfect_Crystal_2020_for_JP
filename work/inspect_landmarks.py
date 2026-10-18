import re
from map_layout import ROOT, file_offset, word

rom = (ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
hits = list(re.finditer(rb'\x00\x00..\x94\x74..\x88\x74..\x6c\x74', rom, re.S))
assert len(hits) == 1
offset = hits[0].start()
bank = offset // 0x4000
print('landmarks', f'{offset:06x}', 'bank', hex(bank))
print('prefix_code', rom[offset-64:offset].hex(' '))
for index in (0, 0x37, 0x38, 0x5e, 0x5f):
    entry = offset+index*4
    pointer = word(rom, entry+2)
    name = file_offset(bank, pointer)
    print('entry', index, rom[entry:entry+4].hex(' '), 'name', f'{name:06x}', rom[name:name+20].hex(' '))
for i in range(bank*0x4000, (bank+1)*0x4000):
    if rom[i] == 0 and (i % 0x4000 == 0 or rom[i-1] != 0):
        end=i
        while end < (bank+1)*0x4000 and rom[end] == 0:
            end+=1
        if end-i>=32:
            print('cave', f'{i:06x}', end-i)
