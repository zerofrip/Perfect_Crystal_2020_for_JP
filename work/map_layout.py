"""Local ROM map-header reader, following pokemontools/crystal.py layouts.

The public disassemblies supply group/map names only. All pointers, dimensions,
script banks and event records are read from each actual input ROM.
"""
from pc_env import workspace
from pathlib import Path
import re

ROOT = workspace()


def file_offset(bank, address):
    assert 0x4000 <= address < 0x8000, (bank, hex(address))
    return bank * 0x4000 + address - 0x4000


def word(rom, offset):
    return int.from_bytes(rom[offset:offset+2], 'little')


def map_names(perfect=False):
    names = {}
    source = 'perfect_crystal_source' if perfect else 'pokekuristaru'
    for line in (ROOT / source / 'maps/map_headers.asm').read_text().splitlines():
        group = re.match(r'MapGroup(\d+):', line)
        if group:
            group_id, map_id = int(group[1]), 0
        header = re.match(r'\s*map_header (\w+),', line)
        if header:
            map_id += 1
            names[(group_id, map_id)] = header[1]
    return names


def maps(rom, perfect=False, primary_bank=0x25):
    result = {}
    for (group, map_id), name in map_names(perfect).items():
        primary = file_offset(primary_bank, word(rom, primary_bank*0x4000 + (group-1)*2)) + (map_id-1)*9
        header = rom[primary:primary+9]
        secondary = file_offset(header[0], word(header, 3))
        attrs = rom[secondary:secondary+12]
        blockdata = file_offset(attrs[3], word(attrs, 4))
        script = file_offset(attrs[6], word(attrs, 7))
        events = file_offset(attrs[6], word(attrs, 9))
        result[name] = dict(group=group, map_id=map_id, primary=primary,
                            secondary=secondary, header=header, attrs=attrs,
                            blockdata=blockdata, script=script, events=events,
                            height=attrs[1], width=attrs[2], bank=attrs[6])
    return result


def events(rom, offset):
    """Read all four counted event sections, retaining raw Japanese pointers."""
    result = {'filler': rom[offset:offset+2]}
    cursor = offset+2
    for name, size in (('warps',5), ('xy',8), ('signposts',5), ('people',13)):
        count = rom[cursor]
        cursor += 1
        result[name] = [rom[cursor+i*size:cursor+(i+1)*size] for i in range(count)]
        cursor += count*size
    result['end'] = cursor
    return result


def encode_events(event):
    result = bytearray(event['filler'])
    for name in ('warps','xy','signposts','people'):
        result.append(len(event[name]))
        result.extend(b''.join(event[name]))
    return bytes(result)


if __name__ == '__main__':
    for label, filename, perfect in (
        ('jp', 'Pocket Monsters - Crystal Version (Japan).gbc', False),
        ('ue2020', 'work/perfect_crystal_ue_patched.gbc', True),
    ):
        rom = (ROOT / filename).read_bytes()
        layout = maps(rom, perfect)
        print(label, 'map_count', len(layout))
        for name in ('GoldenrodPokeCenter1F', 'SilverCaveRoom3', 'CeruleanCity',
                     'CeruleanCave1F', 'CeruleanCave2F', 'CeruleanCaveB1'):
            if name in layout:
                entry = layout[name]
                print(name, {k: f'{v:06x}' if k in ('primary','secondary','script','events','blockdata')
                             else v.hex() if isinstance(v, bytes) else v
                             for k,v in entry.items()})
