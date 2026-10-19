"""Run the Hall hook CPU harness and package the RC4/RC5 CPU verification report.

The Hall hook code is byte-identical between RC4 and RC5, so the same three
modes run against the current development ROM.  The default output remains
rc4_cpu_verification.json; pass ``--revision RC5`` to emit
rc5_cpu_verification.json with the RC4 baseline recorded.
"""
from hashlib import sha256
import json
import subprocess
import sys
from pathlib import Path

from pc_env import workspace

SOURCE_DIR = Path(__file__).resolve().parent
WORK = workspace() / 'work'
ROOT = workspace()
rom_path = WORK / 'development_only_jp_partial.gbc'
rom = rom_path.read_bytes()
digest = sha256(rom).hexdigest()

revision = 'RC4'
if '--revision' in sys.argv:
    revision = sys.argv[sys.argv.index('--revision') + 1]
assert revision in ('RC4', 'RC5'), f'unsupported revision {revision}'

def run(mode):
    proc = subprocess.run(
        [sys.executable, str(SOURCE_DIR / 'test_hall_hook_emulator.py'), mode],
        capture_output=True, text=True, check=False,
    )
    passed = proc.returncode == 0
    return {
        'mode': mode,
        'passed': passed,
        'stdout': proc.stdout.strip(),
        'stderr': proc.stderr.strip(),
    }

results = [run(m) for m in ('hall', 'nonhall', 'repeat')]
for r in results:
    assert r['passed'], f"Hall hook CPU check failed: {r}"

summary = {
    'passed': True,
    'revision': revision,
    'rom_sha256': digest,
    'base_rc3_sha256': sha256((WORK / 'rc3_reference.gbc').read_bytes()).hexdigest(),
    'hall_hook_modes': results,
    'checks': [
        'Hall trigger grants 41 actual item flags plus one separate poster-display flag (42 Hall flags total), plus 0x44.',
        'Non-hall trigger grants only the original trigger flag.',
        'Repeated Hall trigger is idempotent (preset Hall flags and trigger survive, unrelated sentinel preserved).',
    ],
    'limits': [
        'PyBoy executes the actual ROM hook with synthetic event-flag RAM.',
        'The tested ROM bytes are unchanged.',
        'Not physical-hardware or full-playthrough verification.',
    ],
}
if revision == 'RC5':
    from apply_rc4_corrections import HALL_HOOK_START, HALL_HOOK_SIZE
    rc4_rom = (WORK / 'rc4_reference.gbc').read_bytes()
    hook_unchanged = (rom[HALL_HOOK_START:HALL_HOOK_START + HALL_HOOK_SIZE]
                      == rc4_rom[HALL_HOOK_START:HALL_HOOK_START + HALL_HOOK_SIZE])
    assert hook_unchanged, 'Hall hook bytes changed between RC4 and RC5'
    summary['base_rc4_sha256'] = sha256(rc4_rom).hexdigest()
    summary['hall_hook_code_unchanged_from_rc4'] = hook_unchanged
out_path = WORK / ('rc4_cpu_verification.json' if revision == 'RC4'
                   else 'rc5_cpu_verification.json')
out_path.write_text(json.dumps(summary, indent=2) + '\n')
print(f'{out_path.stem}_passed', len(results), 'modes', digest)
