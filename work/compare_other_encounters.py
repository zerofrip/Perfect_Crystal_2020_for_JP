"""Compare the remaining wild encounter ASM tables to the local 2020 IPS result."""
from pc_env import workspace
from pathlib import Path
import re

root = workspace()
rebuilt = (root / "pokekuristaru/pokekuristaru.gbc").read_bytes()
rom = (root / "work/perfect_crystal_ue_patched.gbc").read_bytes()
species = {}
for line in (root / "pokekuristaru/constants/pokemon_constants.asm").read_text().splitlines():
    match = re.match(r"\s*const\s+(\w+)", line)
    if match and len(species) < 251:
        species[match.group(1)] = len(species) + 1
names = {value: key for key, value in species.items()}

for filename, source_start, size, slots, base_maps in (
    ("johto_water", 0x02B11D, 9, 3, 38),
    ("kanto_grass", 0x02B274, 47, 21, 30),
    ("kanto_water", 0x02B7F7, 9, 3, 24),
):
    text = (root / f"perfect_crystal_source/data/wild/{filename}.asm").read_text()
    maps = []
    for chunk in re.split(r"(?=^\s*map \w+)", text, flags=re.M):
        map_match = re.search(r"^\s*map (\w+)", chunk, re.M)
        if map_match:
            rows = [(int(level), mon) for level, mon in re.findall(r"^\s*db\s+(\d+),\s*(\w+)", chunk, re.M)]
            assert len(rows) == slots, (filename, map_match.group(1), len(rows))
            maps.append((map_match.group(1), rows))
    anchor = rebuilt[source_start:source_start + 16]
    matches = []
    position = 0
    while (found := rom.find(anchor, position)) >= 0:
        matches.append(found)
        position = found + 1
    print(filename, "maps", len(maps), "anchor_matches", [f"{n:06x}" for n in matches])
    if len(matches) != 1:
        continue
    table_start = matches[0]
    for index, (map_name, rows) in enumerate(maps):
        rec = rom[table_start + index * size:table_start + (index + 1) * size]
        source_rec = rebuilt[source_start + index * size:source_start + (index + 1) * size]
        if index < base_maps and rec[:2] != source_rec[:2]:
            print(" map_id_mismatch", index, map_name)
            break
        header = size - slots * 2
        for slot, (level, mon) in enumerate(rows):
            got = tuple(rec[header + slot * 2:header + slot * 2 + 2])
            if got != (level, species[mon]):
                print(" difference", map_name, slot, f"{level}:{mon}", "->", f"{got[0]}:{names.get(got[1], got[1])}")
