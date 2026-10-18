"""Locate Johto grass tables by a unique local ROM anchor and compare records."""
from pc_env import workspace
from pathlib import Path
import re

root = workspace()
rebuilt = (root / "pokekuristaru/pokekuristaru.gbc").read_bytes()
japanese = (root / "Pocket Monsters - Crystal Version (Japan).gbc").read_bytes()
english = (root / "Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc").read_bytes()
perfect = (root / "work/perfect_crystal_ue_patched.gbc").read_bytes()
source = (root / "pokekuristaru/data/wild/johto_grass.asm").read_text()
maps = re.findall(r"^\s*map (\w+)", source, re.M)
assert len(maps) == 61, len(maps)
source_start = 0x0A * 0x4000 + (0x65E9 - 0x4000)
anchor = rebuilt[source_start:source_start + 16]
print("maps", len(maps), "rebuilt_start", f"{source_start:06x}")

def locate(rom):
    matches = []
    start = 0
    while (offset := rom.find(anchor, start)) >= 0:
        matches.append(offset)
        start = offset + 1
    return matches

for title, rom in (("stock_jp", japanese), ("stock_ue", english), ("perfect_ue", perfect)):
    matches = locate(rom)
    print(title, "anchor_matches", [f"{m:06x}" for m in matches])
    if len(matches) != 1:
        continue
    table_start = matches[0]
    for index, map_name in enumerate(maps):
        source_record = rebuilt[source_start + index * 47:source_start + (index + 1) * 47]
        rom_record = rom[table_start + index * 47:table_start + (index + 1) * 47]
        if rom_record[:2] != source_record[:2]:
            print("map_id_mismatch", index, map_name, rom_record[:2].hex(), source_record[:2].hex())
            break
        if rom_record[2:5] != source_record[2:5]:
            print("encounter_rate_changed", index, map_name, list(source_record[2:5]), "->", list(rom_record[2:5]))
        if rom_record[2:] != source_record[2:]:
            changes = sum(a != b for a, b in zip(rom_record[2:], source_record[2:]))
            print("changed", index, map_name, "offset", f"{table_start + index * 47:06x}", "bytes", changes)
