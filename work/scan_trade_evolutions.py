"""Read-only, local scan of stock trade-evolution records in Crystal ROMs."""
from pc_env import workspace
from pathlib import Path
import re

root = workspace()
constants = root / "pokekuristaru/constants/pokemon_constants.asm"
species = {}
for line in constants.read_text().splitlines():
    match = re.match(r"\s*const\s+(\w+)", line)
    if match and len(species) < 251:
        species[match.group(1)] = len(species) + 1

cases = [
    ("POLITOED", 0x52, 0x08),
    ("ALAKAZAM", 0xFF, 0x08),
    ("MACHAMP", 0xFF, 0xA9),
    ("GOLEM", 0xFF, 0xA9),
    ("SLOWKING", 0x52, 0x18),
    ("GENGAR", 0xFF, 0x08),
    ("STEELIX", 0x8F, 0xA9),
    ("KINGDRA", 0x97, 0x18),
    ("SCIZOR", 0x8F, 0x22),
    ("PORYGON2", 0xAC, 0x17),
]
for title, path in [
    ("stock Japanese", root / "Pocket Monsters - Crystal Version (Japan).gbc"),
    ("Perfect Crystal 2020 English", root / "work/perfect_crystal_ue_patched.gbc"),
]:
    rom = path.read_bytes()
    print(title)
    for name, old_item, new_item in cases:
        for label, pattern in (
            ("trade", bytes((3, old_item, species[name]))),
            ("stone", bytes((2, new_item, species[name]))),
        ):
            offsets = []
            start = 0
            while (offset := rom.find(pattern, start)) >= 0:
                offsets.append(offset)
                start = offset + 1
            print(f"  {name:9s} {label:5s}: {len(offsets):2d} matches " + ", ".join(f"{n:06x}" for n in offsets[:8]))
