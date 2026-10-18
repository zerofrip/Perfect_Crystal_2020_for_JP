"""Run the Hall hook CPU harness and package the RC4 CPU verification report."""
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
out_path = WORK / 'rc4_cpu_verification.json'
out_path.write_text(json.dumps(summary, indent=2) + '\n')
print('rc4_cpu_verification_passed', len(results), 'modes', digest)
