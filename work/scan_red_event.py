"""Locate the actual Red trainer event by its script command, not source offset."""
from pc_env import workspace
from pathlib import Path

root = workspace()
for name, path in (
    ("jp", root / "Pocket Monsters - Crystal Version (Japan).gbc"),
    ("ue", root / "Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc"),
    ("perfect", root / "work/perfect_crystal_ue_patched.gbc"),
):
    rom = path.read_bytes()
    for label, needle in (
        ("loadtrainer_red", bytes.fromhex("5e3f01")),
        ("red_battle_tail", bytes.fromhex("5e3f015f8360")),
    ):
        positions = []
        cursor = 0
        while (cursor := rom.find(needle, cursor)) >= 0:
            positions.append(cursor)
            cursor += 1
        print(name, label, [f"{position:06x}" for position in positions])
