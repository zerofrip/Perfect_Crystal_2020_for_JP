"""Locate Red's post-battle event tail in the three local Crystal ROMs."""
from pc_env import workspace
from pathlib import Path
import re

root = workspace()
roms = {
    "jp": root / "Pocket Monsters - Crystal Version (Japan).gbc",
    "ue": root / "Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc",
    "perfect": root / "work/perfect_crystal_ue_patched.gbc",
}
needles = {
    "post_disappear": bytes.fromhex("8b0f0f32008b1e0f1b004800a29100"),
    "fade_credit": bytes.fromhex("0f32008b1e0f1b004800a29100"),
    "before_disappear": bytes.fromhex("0f33006e02"),
}
for name, path in roms.items():
    rom = path.read_bytes()
    print(name)
    for label, needle in needles.items():
        matches = []
        start = 0
        while (start := rom.find(needle, start)) >= 0:
            matches.append(f"{start:06x}")
            start += 1
        print(label, matches)
    for label, expression in {
        "credits_tail_masked": rb"\x48\x00.\x91\x00",
        "red_tail_masked": rb"\x8b.\x0f\x32\x00\x8b.\x0f\x1b\x00\x48\x00.\x91\x00",
    }.items():
        print(label, [f"{match.start():06x}" for match in re.finditer(expression, rom, re.S)][:40])
