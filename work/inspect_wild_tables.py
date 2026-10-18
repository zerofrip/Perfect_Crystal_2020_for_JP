from map_layout import ROOT

for label, filename, start in (
    ('jp', 'Pocket Monsters - Crystal Version (Japan).gbc', 0x2b297),
    ('perfect', 'work/perfect_crystal_ue_patched.gbc', 0x2b274),
):
    rom = (ROOT / filename).read_bytes()
    for name, stride in (('kanto_grass',47), ('kanto_water',9),
                         ('swarm_grass',47), ('swarm_water',9)):
        offset = start
        while rom[offset] != 0xff:
            offset += stride
            assert offset < 0x2c000
        print(label, name, f'{start:06x}', 'records', (offset-start)//stride,
              'end', f'{offset+1:06x}')
        pointer=(0x4000+start%0x4000).to_bytes(2,'little')
        print('code_pointer_candidates', [f'{p:06x}' for p in range(0x28000,0x2a60c)
                                          if rom[p:p+2]==pointer])
        start = offset+1
    print('tail_zero', rom[start:0x2c000]==bytes(0x2c000-start))
    for i in range(start,0x2c000):
        if rom[i] == 0 and rom[i-1] != 0:
            end=i
            while end<0x2c000 and rom[end]==0:
                end+=1
            if end-i>=32:
                print('zero_space', f'{i:06x}', end-i)
