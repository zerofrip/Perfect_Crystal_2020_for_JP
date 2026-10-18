"""Local actual-ROM evidence for the Japanese Magikarp comparison repair."""
from pc_env import workspace
from pathlib import Path
import os
import subprocess
import sys

ROOT = workspace()
rom = ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc'
raw = rom.read_bytes()
needle = bytes.fromhex('cdf57d')
bank = raw[0xf8000:0xfc000]
print('bank_3e_compare_calls', [hex(0xf8000 + i) for i in range(len(bank))
                               if bank.startswith(needle, i)])
env = dict(os.environ, PYTHONPATH=str(ROOT / 'work/pokemon-reverse-engineering-tools'))
dest = ROOT / 'work/magikarp_comparison_actual_jp.asm'
subprocess.run([sys.executable, '-m', 'pokemontools.gbz80disasm', '-r', str(rom),
                '-o', str(dest), '-q', 'fbd00', 'fbe40'], env=env, check=True)
print('actual_disassembly', dest)
