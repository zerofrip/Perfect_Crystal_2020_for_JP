from map_layout import ROOT, maps, events, file_offset, word

NAMES = ['VioletGym','AzaleaGym','GoldenrodGym','EcruteakGym','CianwoodGym','OlivineGym','MahoganyGym','BlackthornGym1F','PewterGym','CeruleanGym','VermilionGym','CeladonGym','FuchsiaGym','SaffronGym','SeafoamGym','ViridianGym']

if __name__ == '__main__':
    for tag, path, perf in [('JP','Pocket Monsters - Crystal Version (Japan).gbc', False),('EN','work/perfect_crystal_ue_patched.gbc',True)]:
        rom=(ROOT/path).read_bytes()
        layout=maps(rom,perf)
        for name in NAMES:
            m=layout[name]
            people=events(rom,m['events'])['people']
            print(tag,name,'bank',hex(m['bank']),'secondary',hex(m['secondary']))
            for i,p in enumerate(people):
                if p[7]&15==0 and 0x4000<=word(p,9)<0x8000:
                    ptr=file_offset(m['bank'],word(p,9))
                    if (rom[ptr:ptr+160].find(bytes.fromhex('5d'))>=0 if tag=='JP' else rom[ptr:ptr+160].find(bytes.fromhex('5e'))>=0):
                        print(' person',i,'sprite',hex(p[0]),'script',hex(ptr),rom[ptr:ptr+100].hex())
