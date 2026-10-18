"""Validate held-item CPU evidence against the exact integrated RC3 ROM."""
from hashlib import sha256
import json
from pathlib import Path

from pc_env import workspace
from verify_held_item_stat_cap_cpu import cases, damage_oracle

WORK = workspace() / 'work'
digest = sha256((WORK / 'development_only_jp_partial.gbc').read_bytes()).hexdigest()
baseline = sha256((WORK / 'rc2_reference.gbc').read_bytes()).hexdigest()
assert baseline == '96b08ba49bc42096b2156a6795c86f1b47f40afe8786a6569da764d8c493163c'

def read(name):
    return json.loads((WORK / name).read_text())

report_path = WORK / 'held_item_stat_cap_cpu_results.json'
report = read(report_path.name)
assert report['passed']
assert report['input_sha256'] == report['actual_tested_sha256'] == digest
assert report['baseline_sha256'] == baseline
assert report['helper_domain_cases'] == 5997
assert report['full_entry_cases'] == 248
assert report['baseline_entry_cases'] == report['non_target_parity_cases'] == 24
assert report['cpu_cases'] == 6269

expected_domains = {'species': 1000, 'metal': 1999, 'cap': 2998}
assert {d['kind'] for d in report['domains']} == set(expected_domains)
assert len(report['domains']) == 3
for domain in report['domains']:
    kind = domain['kind']
    count = expected_domains[kind]
    assert domain['passed'] and domain['rom_sha256'] == digest
    assert domain['cases'] == count and domain['input_min'] == 0
    assert domain['input_max'] == count - 1
    expected = b''.join(min(999, value * 2 if kind == 'species' else
                            value + value // 2 if kind == 'metal' else value
                            ).to_bytes(2, 'big') for value in range(count))
    assert domain['result_sha256'] == sha256(expected).hexdigest()

current = [r for r in report['results'] if not r['case'].get('baseline')]
controls = [r for r in report['results'] if r['case'].get('baseline')]
assert len(current) == 248 and len(controls) == 24
assert [r['case'] for r in current] == cases()
assert [r['case'] for r in controls] == [dict(r['case'], baseline=True)
                                       for r in current if r['case'].get('compare_rc2')]
for row in report['results']:
    assert row['passed']
    result, case, hits = row['result'], row['case'], row['real_path_hits']
    assert result['SP'] == 0xd000 and result['bank'] == 13
    if case['group'] == 'boost':
        assert result['HL'] == case['expected']
        assert (result['B'], result['C'], result['D'], result['E']) == (0x12, 0x34, 0x56, 0x78)
        assert hits['user_item'] == int(case['attacker_species'] in
                                        ((25,) if case['special'] else (104, 105)))
    else:
        assert hits['opponent_item'] == int(case.get('defender_species', 132) == 132)
        assert hits['truncate'] >= 1
        if not case.get('baseline'):
            assert result == damage_oracle(case)
for new, old in zip([r for r in current if r['case'].get('compare_rc2')], controls):
    assert new['result'] == old['result']

smoke = read('held_cap_audit_smoke.json')
assert [(r['kind'], r['input'], r['actual']) for r in smoke] == [
    ('species', 120, 240), ('species', 499, 998), ('species', 500, 999),
    ('metal', 120, 180), ('metal', 665, 997), ('metal', 666, 999), ('metal', 667, 999)]
assert all(r['passed'] and not r['rom_modified'] and r['input_sha256'] == digest
           and r['actual'] == r['expected'] for r in smoke)
delta = read('rc3_delta_verification.json')
assert delta['passed'] and delta['output_sha256'] == digest
assert delta['base_rc2_sha256'] == baseline
assert delta['outside_requested_ranges'] == 0

summary = {
    'passed': True,
    'rom_sha256': digest,
    'baseline_rc2_sha256': baseline,
    'cpu_cases': {'rc3_exhaustive_helpers': 5997, 'rc3_entry_paths': 248,
                  'rc2_reference_entry_paths': 24},
    'total_rc3_cpu_cases': 6245,
    'total_with_rc2_reference': 6269,
    'non_target_parity_pairs': 24,
    'additional_independent_rc3_smoke_cases': 7,
    'report_file': report_path.name,
    'report_sha256': sha256(report_path.read_bytes()).hexdigest(),
    'domains': report['domains'],
    'checks': report['checks'],
    'limits': ['PyBoy executes the actual ROM routines with synthetic battle RAM and HRAM drivers.',
               'The tested ROM bytes are unchanged.',
               'RC2 has separate historical evidence; these counts only cover held-item corrections.',
               'Not physical-hardware or full-playthrough verification.'],
}
(WORK / 'rc3_cpu_verification.json').write_text(json.dumps(summary, indent=2) + '\n')
print('integrated_rc3_cpu_reports_verified', 6245, 'RC3 cases + 24 RC2 reference + 7 independent smoke', digest)
