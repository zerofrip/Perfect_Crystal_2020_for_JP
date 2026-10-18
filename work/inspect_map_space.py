from map_layout import ROOT, maps

rom = (ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
for bank in range(128):
    data = rom[bank*0x4000:(bank+1)*0x4000]
    if data == bytes(0x4000):
        print('empty_bank', f'{bank:02x}')
for start in range(0x94000, 0x98000):
    if rom[start] or (start > 0x94000 and rom[start-1] == 0):
        continue
    end = start
    while end < 0x98000 and rom[end] == 0:
        end += 1
    if end-start >= 16:
        print('bank25_zeros', f'{start:06x}', f'{end:06x}', end-start)
needle = bytes.fromhex('817973796579')
assert rom.count(needle) == 1
table = rom.index(needle) - 0x31*2
print('jp_script_pointer_table', f'{table:06x}')
for opcode in (0, 3, 8, 9, 0x31, 0x33, 0x53, 0x5D, 0x6D, 0x8A, 0x90):
    print('opcode', f'{opcode:02x}', rom[table+opcode*2:table+opcode*2+2].hex())
