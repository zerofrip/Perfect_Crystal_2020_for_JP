from pc_env import workspace
from pathlib import Path
import runpy, sys
root = workspace()
roms = {'jp':root/'Pocket Monsters - Crystal Version (Japan).gbc', 'ue':root/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc','pc':root/'work/perfect_crystal_ue_patched.gbc'}
if len(sys.argv)>2:
    name, start, end = sys.argv[1:4]
    sys.path.insert(0,str(root/'work/pokemon-reverse-engineering-tools'))
    sys.argv=['pokemontools.gbz80disasm','-r',str(roms[name]),'-o',str(root/'work/battlefix_disasm.asm'),'-q',start,end]
    runpy.run_module('pokemontools.gbz80disasm',run_name='__main__')
    print((root/'work/battlefix_disasm.asm').read_text())
else:
    for label,pattern in [('love_tail','7ad1bac1c0cb2038'),('moon_evo','fe02c1c0232323'),('fast_prefix','0e'),('belly','c5'),('boost','c5d506680e6916e0'),('light','c5d506190e1916a3')]:
        if len(pattern)<8:continue
        needle=bytes.fromhex(pattern)
        print(label, {name:[hex(i) for i in range(len(data)) if data.startswith(needle,i)] for name,path in roms.items() if (data:=path.read_bytes())})
