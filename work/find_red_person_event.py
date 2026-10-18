"""Find the actual Japanese Red map object by its event flag and coordinates."""
from pc_env import workspace
from pathlib import Path

root = workspace()
for label, path in (
    ('jp', root / 'Pocket Monsters - Crystal Version (Japan).gbc'),
    ('built', root / 'work/pokekuristaru_rgbds_history.gbc'),
    ('ue', root / 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc'),
):
    rom = path.read_bytes()
    bank = rom[0x180000:0x184000] if label == 'jp' else rom[0x18c000:0x190000]
    print(label, 'red_flag_candidates')
    needle = bytes.fromhex('6207')
    offset = 0
    hits = []
    while True:
        offset = rom.find(needle, offset)
        if offset < 0:
            break
        if 0x50000 <= offset < 0x200000:
            hits.append(offset)
        offset += 1
    for offset in hits[:100]:
        if rom[offset - 10:offset - 8] == bytes((14, 13)):
            print('coord_match', f'{offset:06x}', rom[offset-11:offset+2].hex(' '))
            address = int.from_bytes(rom[offset - 2:offset], 'little')
            if label == 'jp':
                script = 0x70000 + address - 0x4000
                print('script_offset', f'{script:06x}', rom[script:script+100].hex(' '))
                tail = rom.find(bytes.fromhex('0f33006d028a0f'), script, script+100)
                print('post_battle_tail', f'{tail:06x}')
    print('flag_hits', len(hits))
    if label == 'built':
        print('built_red_event', rom[0x18C63F:0x18C680].hex(' '))
    if label == 'jp':
        start = 0x70000
        while start < 0x74000:
            if rom[start] == 0 and (start == 0x70000 or rom[start-1] != 0):
                end = start
                while end < 0x74000 and rom[end] == 0:
                    end += 1
                if end-start >= 32:
                    print('cave', f'{start:06x}', f'{end:06x}', end-start)
            start += 1
