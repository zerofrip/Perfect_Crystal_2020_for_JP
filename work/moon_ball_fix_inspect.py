"""Inspect only the local Moon Ball routine and its existing banked readers."""
from pc_env import workspace
from pathlib import Path
ROOT = workspace()
for name, file, start in (
    ('jp', 'Pocket Monsters - Crystal Version (Japan).gbc', 0xef52),
    ('stock', 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc', 0xecdd),
    ('2020', 'work/perfect_crystal_ue_patched.gbc', 0xecd8),
    ('port', 'work/development_only_jp_partial.gbc', 0xef52),
):
    rom=(ROOT/file).read_bytes()
    print(name, 'moon', hex(start), rom[start:start+53].hex())
    if name=='jp':
        print('banked readers', rom[0x3019:0x3037].hex())
        print('pointer anchor',rom[0x42753:0x42763].hex())
    if name in ('jp','port'):
        print(name,'reserved cave zero',not any(rom[0xff80:0x10000]))
