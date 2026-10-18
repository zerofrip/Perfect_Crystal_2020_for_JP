"""Create source-only reference for exact local 2020 Johto water encounters."""
from pc_env import workspace
from pathlib import Path
import re

root = workspace()
names = {}
for line in (root / "pokekuristaru/constants/pokemon_constants.asm").read_text().splitlines():
    match = re.match(r"\s*const\s+(\w+)", line)
    if match and len(names) < 251:
        names[len(names) + 1] = match.group(1)
rom = (root / "work/perfect_crystal_ue_patched.gbc").read_bytes()
source = (root / "perfect_crystal_source/data/wild/johto_water.asm").read_text().splitlines(keepends=True)
output_path = root / "work/expected_johto_water_2020.asm"

map_index = -1
slot = 0
changes = 0
output = []
for line in source:
    if re.match(r"\s*map \w+", line):
        map_index += 1
        slot = 0
    match = re.match(r"^(\s*)db\s+(\d+),\s*(\w+)(?:\s*;.*)?(\n?)$", line)
    if map_index >= 0 and match and slot < 3:
        record = rom[0x02B11D + map_index * 9:0x02B11D + (map_index + 1) * 9]
        level, species = record[3 + slot * 2:5 + slot * 2]
        if (int(match.group(2)), match.group(3)) != (level, names[species]):
            line = f"{match.group(1)}db {level}, {names[species]}{match.group(4)}"
            changes += 1
        slot += 1
    output.append(line)
assert map_index + 1 == 38, map_index + 1
assert changes == 2, changes
output_path.write_text("".join(output))
print("reference", output_path, "2020_changed_slots", changes)
