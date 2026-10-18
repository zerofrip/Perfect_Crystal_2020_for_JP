"""Verify completed encounter tables against the local 2020 IPS result."""
from pc_env import workspace
from pathlib import Path

root = workspace()
rebuilt = (root / "pokekuristaru/pokekuristaru.gbc").read_bytes()
patched = (root / "work/perfect_crystal_ue_patched.gbc").read_bytes()

for name, start, size in (
    ("johto_grass", 0x02A5E9, 61 * 47),
    ("johto_water", 0x02B11D, 38 * 9),
):
    a = rebuilt[start:start + size]
    b = patched[start:start + size]
    differences = sum(x != y for x, y in zip(a, b))
    print(name, "size", size, "different_bytes", differences)
    assert differences == 0, name
