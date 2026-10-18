"""Create a source-only reference for the exact local 2020 Johto grass table."""
from pc_env import workspace
from pathlib import Path
import re

root = workspace()
constants = (root / "pokekuristaru/constants/pokemon_constants.asm").read_text()
names = {}
for line in constants.splitlines():
    match = re.match(r"\s*const\s+(\w+)", line)
    if match and len(names) < 251:
        names[len(names) + 1] = match.group(1)

rom = (root / "work/perfect_crystal_ue_patched.gbc").read_bytes()
input_path = root / "perfect_crystal_source/data/wild/johto_grass.asm"
output_path = root / "work/expected_johto_grass_2020.asm"
lines = input_path.read_text().splitlines(keepends=True)
map_index = -1
slot = 0
changed = 0
result = []
for line in lines:
    if re.match(r"\s*map \w+", line):
        map_index += 1
        slot = 0
    match = re.match(r"^(\s*)db\s+(\d+),\s*(\w+)(?:\s*;.*)?(\n?)$", line)
    if map_index >= 0 and match and slot < 21:
        record = rom[0x02A5E9 + map_index * 47:0x02A5E9 + (map_index + 1) * 47]
        level, species = record[5 + slot * 2:7 + slot * 2]
        if (int(match.group(2)), match.group(3)) != (level, names[species]):
            line = f"{match.group(1)}db {level}, {names[species]}{match.group(4)}"
            changed += 1
        slot += 1
    result.append(line)

assert map_index + 1 == 61, map_index + 1
assert changed == 22, changed
output_path.write_text("".join(result))
print("reference", output_path, "2020_changed_slots", changed)
