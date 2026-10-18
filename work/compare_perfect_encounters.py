"""Compare public Perfect Crystal encounter ASM to the local 2020-patched UE ROM."""
from pc_env import workspace
from pathlib import Path
import re
import sys

root = workspace()
constants = (root / "pokekuristaru/constants/pokemon_constants.asm").read_text()
species = {}
for line in constants.splitlines():
    match = re.match(r"\s*const\s+(\w+)", line)
    if match and len(species) < 251:
        species[match.group(1)] = len(species) + 1
names = {value: key for key, value in species.items()}

source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "perfect_crystal_source/data/wild/johto_grass.asm"
source = source_path.read_text()
chunks = re.split(r"(?=^\s*map \w+)", source, flags=re.M)
records = []
for chunk in chunks:
    map_match = re.search(r"^\s*map (\w+)", chunk, re.M)
    if not map_match:
        continue
    rows = [(int(level), mon) for level, mon in re.findall(r"^\s*db\s+(\d+),\s*(\w+)", chunk, re.M)]
    assert len(rows) == 21, (map_match.group(1), len(rows))
    records.append((map_match.group(1), rows))
assert len(records) == 61, len(records)

rom = (root / "work/perfect_crystal_ue_patched.gbc").read_bytes()
table_start = 0x02A5E9
for index, (map_name, rows) in enumerate(records):
    record = rom[table_start + index * 47:table_start + (index + 1) * 47]
    differences = []
    for slot, (source_level, source_mon) in enumerate(rows):
        level, mon = record[5 + slot * 2:7 + slot * 2]
        if (level, mon) != (source_level, species[source_mon]):
            differences.append(f"{slot // 7}:{slot % 7} {source_level}:{source_mon} -> {level}:{names.get(mon, f'#{mon}')}")
    if differences:
        print(map_name)
        for change in differences:
            print(" ", change)
