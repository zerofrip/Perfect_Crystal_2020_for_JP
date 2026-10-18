from map_layout import ROOT,maps
from gym_inspect import NAMES
r=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
for b in sorted({maps(r)[n]['bank'] for n in NAMES}):
    data=r[b*0x4000:(b+1)*0x4000]
    n=len(data)-len(data.rstrip(b'\0'))
    print(hex(b),'zero tail',hex((b+1)*0x4000-n),n)
