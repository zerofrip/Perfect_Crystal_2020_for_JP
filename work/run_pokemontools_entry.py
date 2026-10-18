"""Disassemble only the ROM entry range locally with historical pokemontools."""
import runpy
import sys
from pc_env import workspace

POKEMONTOOLS = workspace() / "work/pokemon-reverse-engineering-tools"
sys.path.insert(0, str(POKEMONTOOLS))
for name, rom in (
    ("jp", workspace() / "Pocket Monsters - Crystal Version (Japan).gbc"),
    ("perfect_ue", workspace() / "work/perfect_crystal_ue_patched.gbc"),
):
    sys.argv = [
        "pokemontools.gbz80disasm",
        "-r", str(rom),
        "-o", str(workspace() / f"work/{name}_entry_pokemontools.asm"),
        "-q", "016e", "0200",
    ]
    runpy.run_module("pokemontools.gbz80disasm", run_name="__main__")
