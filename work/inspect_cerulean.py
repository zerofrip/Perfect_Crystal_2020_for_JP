from map_layout import ROOT, maps

jp = (ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
ue = (ROOT / 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
perfect = (ROOT / 'work/perfect_crystal_ue_patched.gbc').read_bytes()
jm, um, pm = maps(jp), maps(ue), maps(perfect, True)
for name in ('CeruleanCity', 'Route4', 'CeruleanCave1F', 'CeruleanCave2F', 'CeruleanCaveB1'):
    entry = pm[name]
    block = perfect[entry['blockdata']:entry['blockdata']+entry['width']*entry['height']]
    print(name, 'blocks', len(block), 'unique', sorted(set(block)))
    if name in jm:
        jentry, uentry = jm[name], um[name]
        jblock = jp[jentry['blockdata']:jentry['blockdata']+len(block)]
        ublock = ue[uentry['blockdata']:uentry['blockdata']+len(block)]
        print('same_jp_ue_stock', jblock == ublock,
              'block_changes', [(i,a,b) for i,(a,b) in enumerate(zip(jblock,block)) if a!=b])
        print('events_jp', f"{jentry['events']:06x}", jp[jentry['events']:jentry['events']+75].hex(' '))
    print('events_perfect', f"{entry['events']:06x}", perfect[entry['events']:entry['events']+75].hex(' '))
    if name == 'CeruleanCaveB1':
        print('script_perfect', perfect[entry['script']:entry['events']].hex(' '))
