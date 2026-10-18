"""Use pokemontools on original Japanese home map loader, locally."""
import runpy
import sys
from map_layout import ROOT

rom = (ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
needle = bytes.fromhex('c50548060021004009092a666fc10d06003e09')
positions = [i for i in range(0x4000) if rom.startswith(needle, i)]
assert len(positions) == 1, positions
start = positions[0]
print('GetAnyMapHeaderPointer', f'{start:04x}')
sys.path.insert(0, str(ROOT / 'work/pokemon-reverse-engineering-tools'))
sys.argv = ['pokemontools.gbz80disasm', '-r',
            str(ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc'),
            '-o', str(ROOT / 'work/jp_map_loader_pokemontools.asm'),
            '-q', f'{start:x}', f'{start+0x90:x}']
runpy.run_module('pokemontools.gbz80disasm', run_name='__main__')
