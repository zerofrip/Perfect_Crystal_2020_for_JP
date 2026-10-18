"""Read-only check of numeric event fields in all actual map records.

No ROM data leaves the local filesystem. Pointer operands are intentionally
excluded: those need language-specific script mapping, not byte comparison.
"""
from hashlib import sha256
from map_layout import ROOT, maps, events

FILES = {
    'jp': 'Pocket Monsters - Crystal Version (Japan).gbc',
    'stock': 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc',
    'release': 'work/perfect_crystal_ue_patched.gbc',
    'port': 'work/development_only_jp_partial.gbc',
}


def audit():
    roms = {key: (ROOT / path).read_bytes() for key, path in FILES.items()}
    layouts = {key: maps(raw, key in ('release', 'port'),
                         primary_bank=0x60 if key == 'port' else 0x25)
               for key, raw in roms.items()}
    fields = {'warps': range(5), 'xy': (0, 1, 2, 3, 6, 7),
              'signposts': range(3),
              'people': (0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 12)}
    results = []
    for name in layouts['stock']:
        records = {key: events(raw, layouts[key][name]['events'])
                   for key, raw in roms.items()}
        for section, indexes in fields.items():
            for number, (old, new) in enumerate(zip(records['stock'][section],
                                                    records['release'][section])):
                for field in indexes:
                    if old[field] == new[field]:
                        continue
                    jp = records['jp'][section][number][field]
                    port = records['port'][section][number][field]
                    results.append((name, section, number, field, old[field],
                                    new[field], jp, port, port == new[field]))
    print('port_sha256', sha256(roms['port']).hexdigest())
    print('stock_maps_checked', len(layouts['stock']))
    for row in results:
        print(row)
    print('changed_numeric_fields', len(results),
          'unmatched_port_fields', sum(not row[-1] for row in results))
    return results


if __name__ == '__main__':
    audit()
