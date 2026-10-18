"""Exercise the actual bank-0d cap helpers and full held-item battle paths.

ROM bytes are never changed by this test. Exhaustive domains use one CPU each,
with a small HRAM CALL driver and WRAM result buffer. Full entry cases use real
species, held-item, critical, screen, and truncation code in isolated CPUs.
"""
from pc_env import workspace
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys

from fix_held_item_stat_cap import (SPECIES_CAVE, SPECIES_FIXED, METAL_CAVE,
                                   METAL_FIXED, WRAPPER, WRAPPER_CODE)
from verify_held_item_stat_cap import RC2_SHA256

ROOT = workspace()
BASELINE = ROOT/'work/rc2_reference.gbc'
DOMAIN_END = {'species': 1000, 'metal': 1999, 'cap': 2998}


def start_cpu(path):
    from pyboy import PyBoy
    rom = Path(path).read_bytes()
    game = PyBoy(BytesIO(rom), window='null', sound_emulated=False)
    game.set_emulation_speed(0)
    game.tick(600, render=False, sound=False)
    game.memory[0xffff] = game.memory[0xff0f] = 0
    game.memory[0xff70] = 1
    game.memory[0x2000] = game.memory[0xff9d] = 0x0d
    return game, rom


def domain_driver(kind):
    # HRAM code: counter in HL, output in DE, CALL unmodified ROM helper.
    code = bytearray.fromhex('2100001100c0')
    loop = len(code)
    code.append(0xe5)  # push hl
    if kind == 'species':
        code += bytes.fromhex('cd707f444d')
    else:
        code += bytes.fromhex('444d')
        address = 0x52cb if kind == 'metal' else 0x7f82
        code += bytes((0xcd, address & 255, address >> 8))
    code += bytes.fromhex('781213791213e1237cfe')
    end = DOMAIN_END[kind]
    code.append(end >> 8)
    code += bytes((0x20, (loop-len(code)-2) & 255))
    code += bytes((0x7d, 0xfe, end & 255))
    code += bytes((0x20, (loop-len(code)-2) & 255))
    code += bytes.fromhex('c30001')
    assert len(code) <= 0x40
    return code


def execute_domain(path, kind):
    game, rom = start_cpu(path)
    r = game.register_file
    end = DOMAIN_END[kind]
    code = domain_driver(kind)
    game.memory[0xff70] = 6
    game.memory[0xffb0:0xffb0+len(code)] = list(code)

    def returned(_):
        assert r.SP == 0xfffc and r.HL == end
        assert game.memory[0xff9d] == 0x0d
        assert game.memory[0x4000] == rom[0x34000]
        result = bytes(game.memory[0xc000:0xc000+end*2])
        for value in range(end):
            expected = min(999, value*2 if kind == 'species' else
                           value+value//2 if kind == 'metal' else value)
            actual = int.from_bytes(result[value*2:value*2+2], 'big')
            assert actual == expected, (kind, value, actual, expected)
            if (value+1) % 100 == 0:
                print('held_cap_domain_progress', kind, value+1, '/', end, flush=True)
        print(json.dumps({'group': 'domain', 'kind': kind, 'passed': True,
                          'cases': end, 'input_min': 0, 'input_max': end-1,
                          'result_sha256': sha256(result).hexdigest(),
                          'rom_sha256': sha256(rom).hexdigest()}), flush=True)
        os._exit(0)

    game.hook_register(0, 0x100, returned, None)
    r.SP = 0xfffc
    r.PC = 0xffb0
    game.tick(30, render=False, sound=False)
    raise AssertionError(('domain return not reached', kind, hex(r.PC)))


def write16(game, address, value):
    game.memory[address:address+2] = [value >> 8, value & 255]


def setup_species(game, case):
    turn = case['turn']
    atk = case.get('attacker_species', 1)
    defender = case.get('defender_species', 132)
    atk_item = case.get('attacker_item', 0)
    def_item = case.get('defender_item', 0x23)
    game.memory[0xffe4] = turn
    game.memory[0xd094] = 1  # Real BattlePartyAttr must index the second party slot.
    game.memory[0xdca5] = 2  # Deliberately different first party member.
    game.memory[0xdca5+48] = atk if turn == 0 else defender
    game.memory[0xd235] = defender if turn == 0 else atk
    game.memory[0xc623] = atk_item if turn == 0 else def_item
    game.memory[0xd238] = def_item if turn == 0 else atk_item
    appearance_atk = case.get('attacker_appearance', atk)
    appearance_def = case.get('defender_appearance', defender)
    game.memory[0xc622] = appearance_atk if turn == 0 else appearance_def
    game.memory[0xd237] = appearance_def if turn == 0 else appearance_atk
    game.memory[0xc660] = game.memory[0xc665] = case.get('transformed', 0)


def truncate(attack, defense, link):
    while attack > 255 or defense > 255:
        attack = max(1, attack//4)
        defense = max(1, defense//4)
        if link == 3:
            break
    return attack & 255, defense & 255


def damage_oracle(case):
    attack = case.get('attack', 300)
    defense = case.get('defense', 102) * (2 if case.get('screen') else 1)
    if case.get('critical') == 'base':
        attack, defense = case.get('base_attack', 80), case.get('base_defense', 102)
    species = case.get('attacker_species', 1)
    item = case.get('attacker_item', 0)
    special = case['special']
    if ((special and species == 25 and item == 0xa3) or
            (not special and species in (104, 105) and item == 0x76)):
        attack = min(999, attack*2)
    if case.get('defender_species', 132) == 132 and case.get('defender_item', 0x23) == 0x23:
        defense = min(999, defense+defense//2)
    b, c = truncate(attack, defense, case.get('link', 0))
    return {'B': b, 'C': c, 'D': 80, 'E': 37 if case['turn'] == 0 else 41,
            'A': 1, 'F': 0x20, 'SP': 0xd000, 'bank': 13}


def setup_damage(game, case):
    attack, defense = case.get('attack', 300), case.get('defense', 102)
    base_attack, base_defense = case.get('base_attack', 80), case.get('base_defense', 102)
    turn = case['turn']
    for address in (0xc636, 0xc63c):
        write16(game, address, attack if turn == 0 else defense)
    for address in (0xc638, 0xc63e):
        write16(game, address, defense if turn else 197)
    for address in (0xd24b, 0xd251):
        write16(game, address, attack if turn else 193)
    for address in (0xd24d, 0xd253):
        write16(game, address, defense if turn == 0 else 191)
    for address in (0xc6aa, 0xc6b0):
        write16(game, address, base_attack if turn == 0 else 73)
    for address in (0xc6ac, 0xc6b2):
        write16(game, address, base_defense if turn else 71)
    for address in (0xc6b5, 0xc6bb):
        write16(game, address, base_attack if turn else 69)
    for address in (0xc6b7, 0xc6bd):
        write16(game, address, base_defense if turn == 0 else 67)
    game.memory[0xc6c0:0xc6d0] = [7]*16
    special = case['special']
    attacker_stage = (0xc6c3 if special else 0xc6c0) if turn == 0 else (0xc6cb if special else 0xc6c8)
    defender_stage = (0xc6cc if special else 0xc6c9) if turn == 0 else (0xc6c4 if special else 0xc6c1)
    critical = case.get('critical')
    game.memory[0xc65a] = 1 if critical else 0
    game.memory[attacker_stage] = 8 if critical == 'keep' else 7
    game.memory[defender_stage] = 8 if critical == 'base' else 7
    game.memory[0xc6f3] = game.memory[0xc6f4] = 0
    if case.get('screen'):
        game.memory[0xc6f4 if turn == 0 else 0xc6f3] = 8 if special else 16
    game.memory[0xc611] = game.memory[0xc60a] = 80
    game.memory[0xc612] = game.memory[0xc60b] = 20 if special else 0
    game.memory[0xc62f] = 37
    game.memory[0xd244] = 41
    game.memory[0xc2dc] = case.get('link', 0)


def execute_case(path, case):
    game, rom = start_cpu(path)
    r = game.register_file
    setup_species(game, case)
    group = case['group']
    traces = {'user_item': 0, 'opponent_item': 0, 'truncate': 0}

    def hit(name):
        def callback(_):
            traces[name] += 1
        return callback

    for address, name in ((0x7e03, 'user_item'), (0x7e12, 'opponent_item'), (0x534d, 'truncate')):
        game.hook_register(13, address, hit(name), None)

    def returned(_):
        assert r.SP == 0xd000
        assert game.memory[0xff9d] == 13
        assert game.memory[0x4000] == rom[0x34000]
        actual = {'B': r.B, 'C': r.C, 'D': r.D, 'E': r.E,
                  'A': r.A, 'F': r.F, 'SP': r.SP, 'bank': game.memory[0xff9d]}
        if group == 'boost':
            assert r.HL == case['expected'], (case, r.HL)
            assert (r.B << 8 | r.C) == 0x1234
            assert (r.D << 8 | r.E) == 0x5678
            assert traces['user_item'] == int(case['attacker_species'] in
                                              ((25,) if case['special'] else (104, 105)))
            actual['HL'] = r.HL
        else:
            if not case.get('baseline'):
                assert actual == damage_oracle(case), (case, actual, damage_oracle(case))
            assert traces['opponent_item'] == int(case.get('defender_species', 132) == 132)
            assert traces['truncate'] >= 1
        print(json.dumps({'case': case, 'passed': True, 'result': actual,
                          'real_path_hits': traces}), flush=True)
        os._exit(0)

    game.hook_register(0, 0x100, returned, None)
    game.memory[0xcffe:0xd000] = [0, 1]
    r.SP = 0xcffe
    r.A = 0; r.F = 0xf0
    r.B = 0x12; r.C = 0x34; r.D = 0x56; r.E = 0x78
    if group == 'boost':
        write16(game, 0xc900, case['stat'])
        r.HL = 0xc900
        r.PC = 0x53c3 if case['special'] else 0x53b5
    else:
        setup_damage(game, case)
        r.HL = 0
        r.PC = 0x52dc
    game.tick(1, render=False, sound=False)
    raise AssertionError(('full entry return not reached', case, hex(r.PC)))


def cases():
    result = []
    for turn in (0, 1):
        for species, item, special in ((25, 0xa3, True), (104, 0x76, False), (105, 0x76, False)):
            for stat in (1, 120, 127, 128, 255, 256, 499, 500, 511, 512, 999):
                result.append(dict(group='boost', turn=turn, special=special,
                                   attacker_species=species, attacker_item=item,
                                   stat=stat, expected=min(999, stat*2)))
            for label, extra, boosted in (
                ('wrong_species', {'attacker_species': 132}, False),
                ('wrong_item', {'attacker_item': 0}, False),
                ('opposite_item', {'attacker_item': 0, 'defender_item': item}, False),
                ('transformed_eligible', {'transformed': 8, 'attacker_appearance': 132}, True),
                ('transformed_ineligible', {'transformed': 8, 'attacker_species': 132,
                                            'attacker_appearance': species}, False)):
                case = dict(group='boost', turn=turn, special=special,
                            attacker_species=species, attacker_item=item,
                            stat=120, expected=240 if boosted else 120, label=label)
                case.update(extra)
                result.append(case)
        for special in (False, True):
            for defense in (1, 120, 170, 171, 255, 256, 257, 511, 512, 513, 665, 666, 667, 999):
                result.append(dict(group='damage', label='metal_boundaries', turn=turn,
                                   special=special, attack=300, defense=defense))
            for critical in (None, 'keep', 'base'):
                for screen in (False, True):
                    for link in (0, 3):
                        result.append(dict(group='damage', label='screens_critical_link', turn=turn,
                                           special=special, attack=999, defense=999,
                                           screen=screen, critical=critical, link=link))
            for attack, defense in ((120, 120), (499, 666), (500, 667), (999, 999), (1, 999), (3, 999)):
                result.append(dict(group='damage', label='combined_boosts', turn=turn,
                                   special=special, attack=attack, defense=defense,
                                   attacker_species=25 if special else 104,
                                   attacker_item=0xa3 if special else 0x76,
                                   attacker_appearance=132, defender_appearance=25,
                                   transformed=8, screen=attack in (1, 3)))
            for label, extra in (
                ('non_ditto', {'defender_species': 1}),
                ('wrong_item', {'defender_item': 0}),
                ('opposite_item', {'attacker_item': 0x23, 'defender_item': 0}),
                ('transformed_non_ditto', {'defender_species': 1, 'defender_appearance': 132,
                                           'transformed': 8}),
                ('wrong_offense_type', {'attacker_species': 104 if special else 25,
                                        'attacker_item': 0x76 if special else 0xa3,
                                        'defender_species': 1}),
                ('critical_base', {'defender_species': 1, 'critical': 'base'})):
                case = dict(group='damage', label=label, turn=turn, special=special,
                            attack=999, defense=999, screen=True, compare_rc2=True)
                case.update(extra)
                result.append(case)
    return result


def child(command):
    result = subprocess.run([sys.executable, __file__, *command], capture_output=True,
                            text=True, timeout=40)
    assert result.returncode == 0, (command, result.stdout, result.stderr)
    return json.loads(result.stdout.splitlines()[-1])


def main():
    path = str(Path(sys.argv[1]).resolve()) if len(sys.argv) == 2 else str(ROOT/'work/held_item_stat_cap_isolated.gbc')
    rom = Path(path).read_bytes()
    input_hash = sha256(rom).hexdigest()
    for offset, data in ((SPECIES_CAVE, SPECIES_FIXED), (METAL_CAVE, METAL_FIXED), (WRAPPER, WRAPPER_CODE)):
        assert rom[offset:offset+len(data)] == data
    assert sha256(BASELINE.read_bytes()).hexdigest() == RC2_SHA256
    domains = []
    for kind in DOMAIN_END:
        domains.append(child(['--domain', path, kind]))
        print('held_cap_domain_passed', kind, domains[-1]['cases'], flush=True)
    full_cases = cases()
    jobs = [(path, case) for case in full_cases]
    jobs += [(str(BASELINE), dict(case, baseline=True)) for case in full_cases if case.get('compare_rc2')]

    def run(job):
        return child(['--child', job[0], json.dumps(job[1], separators=(',', ':'))])

    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(run, jobs):
            results.append(result)
            if len(results) % 100 == 0:
                print('held_cap_full_entry_progress', len(results), '/', len(jobs), flush=True)
    new_comparisons = [r for r in results if r['case'].get('compare_rc2') and not r['case'].get('baseline')]
    old_comparisons = [r for r in results if r['case'].get('baseline')]
    assert len(new_comparisons) == len(old_comparisons)
    for new, old in zip(new_comparisons, old_comparisons):
        assert new['result'] == old['result'], ('non_target_RC2_mismatch', new, old)
    report = {'passed': True, 'rom_path': path, 'input_sha256': input_hash,
              'actual_tested_sha256': input_hash, 'baseline_sha256': RC2_SHA256,
              'cpu_cases': sum(d['cases'] for d in domains)+len(results),
              'helper_domain_cases': sum(d['cases'] for d in domains),
              'full_entry_cases': len(full_cases), 'baseline_entry_cases': len(old_comparisons),
              'non_target_parity_cases': len(new_comparisons),
              'domains': domains, 'results': results,
              'checks': ['unaltered_ROM_bytes', 'real_species_party_index', 'real_held_item_path',
                         'both_turns', 'physical_and_special', 'transformed_original_species',
                         'critical_base_or_modified_stats', 'screens', 'link_truncation',
                         'power_and_level_preserved', 'stack_and_ROM_bank_restored',
                         'non_targets_match_RC2_semantic_output', 'exhaustive_helper_domains']}
    (ROOT/'work/held_item_stat_cap_cpu_results.json').write_text(json.dumps(report, indent=2)+'\n')
    print('held_item_stat_cap_cpu_passed', report['cpu_cases'], 'cases', input_hash, flush=True)


if __name__ == '__main__':
    if sys.argv[1:2] == ['--domain']:
        execute_domain(sys.argv[2], sys.argv[3])
    elif sys.argv[1:2] == ['--child']:
        execute_case(sys.argv[2], json.loads(sys.argv[3]))
    else:
        main()
