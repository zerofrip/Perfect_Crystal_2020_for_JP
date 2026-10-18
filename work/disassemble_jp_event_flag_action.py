"""Disassemble the original Japanese event-flag dispatcher locally."""
import runpy
import sys
from pc_env import workspace

POKEMONTOOLS = workspace() / "work/pokemon-reverse-engineering-tools"
sys.path.insert(0, str(POKEMONTOOLS))
sys.argv = [
    "pokemontools.gbz80disasm",
    "-r", str(workspace() / "Pocket Monsters - Crystal Version (Japan).gbc"),
    "-o", str(workspace() / "work/jp_setevent_pokemontools.asm"),
    "-q", "97930", "979d5",
]
runpy.run_module("pokemontools.gbz80disasm", run_name="__main__")
