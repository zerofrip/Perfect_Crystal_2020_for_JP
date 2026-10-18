from map_layout import ROOT,maps,events
rom=(ROOT/'work/development_only_jp_partial.gbc').read_bytes()
m=maps(rom,True,primary_bank=0x60)['GoldenrodPokeCenter1F']
print(m)
e=events(rom,m['events'])
for section in ('warps','xy','people'):
 print(section,[x.hex() for x in e[section]])
print('original tail',rom[0x56940:0x569b0].hex())
