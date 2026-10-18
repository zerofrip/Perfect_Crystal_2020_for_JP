"""Require successful CPU reports for the exact integrated RC2 ROM hash."""
from hashlib import sha256
import json
import sys
from pathlib import Path

from pc_env import workspace

WORK = workspace() / 'work'
rom_path = Path(sys.argv[1]) if len(sys.argv) == 2 else WORK / 'rc2_reference.gbc'
digest = sha256(rom_path.read_bytes()).hexdigest()
def read(name):
    return json.loads((WORK / name).read_text())

moon = read('moon_ball_fix_cpu_results.json')
assert moon['input_sha256'] == digest
assert moon['cpu_cases'] == len(moon['results']) == 401
targets = {30, 33, 35, 39, 61, 64, 93}
assert set(moon['targets']) == targets
assert {r['species'] for r in moon['results'] if r['group'] == 'actual_251'} == set(range(1, 252))
for r in moon['results']:
    applies = (r['species'] in targets if r['group'] in ('actual_251', 'target_boundaries', 'non_target_boundaries')
               else r['group'] in ('method5_then_moon', 'all_methods_before_moon'))
    assert r['result'] == (min(255, r['rate'] * 4) if applies else r['rate'])

fang = read('dragon_fang_fix_cpu_results.json')
assert fang['input_sha256'] == digest
assert fang['count'] == len(fang['cases']) == 24
assert all(r['damage'] == r['expected'] for r in fang['cases'])

length = read('magikarp_comparison_cpu_results.json')
assert length['tested_rom_sha256'] == digest
assert length['correct_cpu_executions'] == 140 and length['regression_controls'] == 2
assert len(length['results']) == 142
for r in length['results']:
    less = bool(r['cpu']['f'] & 0x10)
    assert (less == (r['bc'] < r['de'])) == (r['version'] == 'correct')

sharp = read('sharp_stat_drop_cpu_results.json')
assert len(sharp) == 792
assert all(r['passed'] and r['input_sha256'] == r['tested_sha256'] == digest
           and r['patch_mode'] == 'integrated_fixed_rom_unchanged' for r in sharp)
rollback_control = read('sharp_stat_drop_rollback_control.json')
assert rollback_control['passed'] and rollback_control['stage_before'] == 3
assert rollback_control['stage_after'] == 2 and rollback_control['failed_message'] == 3
assert rollback_control['attack_missed'] == 1 and rollback_control['calculated_stat'] == 1
summary = {
    'rom_sha256': digest,
    'passed': True,
    'cpu_cases': {'moon_ball': 401, 'dragon_fang': 24,
                  'magikarp_comparison': 140, 'sharp_stat_drop': 792},
    'total_corrected_cpu_cases': 1357,
    'additional_old_bug_regression_controls': 3,
    'limits': ['Synthetic battle RAM and return sentinels; original ROM routines execute.',
               'Not physical-hardware or full-playthrough verification.'],
}
(WORK / 'rc2_cpu_verification.json').write_text(json.dumps(summary, indent=2) + '\n')
print('integrated_rc2_cpu_reports_verified', 1357, 'cases + 3 old-bug regression controls', digest)
