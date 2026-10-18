"""Compare built existing Kanto encounter records to the 2020 IPS result."""
from pc_env import workspace
from pathlib import Path

root = workspace()
built = (root / "pokekuristaru/pokekuristaru.gbc").read_bytes()
reference = (root / "work/perfect_crystal_ue_patched.gbc").read_bytes()

for name, built_offset, reference_offset, count, record_size in (
    ("kanto_grass", 0x02B274, 0x02B274, 30, 47),
    ("kanto_water", 0x02B7F7, 0x02B884, 24, 9),
):
    length = count * record_size
    actual = built[built_offset:built_offset + length]
    expected = reference[reference_offset:reference_offset + length]
    differences = [(i, a, b) for i, (a, b) in enumerate(zip(actual, expected)) if a != b]
    print(name, "records", count, "size", length, "different_bytes", len(differences))
    for index, a, b in differences[:10]:
        print("  +", f"{index:04x}", f"{a:02x}", f"{b:02x}")
    assert len(actual) == len(expected) == length
    assert not differences
