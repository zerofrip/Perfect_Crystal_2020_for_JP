"""Run complete JP Moon Ball entry and real banked reads in isolated CPUs.

Each process exits at the real return destination before its synthetic stack
continues through game code. Fixtures change only in-memory test ROM copies.
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
from fix_moon_ball import ENTRY, JP_EVOS, TARGETS, moon_targets

ROOT = workspace()
RATES = (0, 1, 2, 63, 64, 65, 127, 128, 254, 255)
FIXTURES = {
    'method5_then_moon': ('0514026b02081f00', True),
    'destination_is_08': ('0514020800', False),
    'terminator_then_fake_moon': ('0002081f', False),
    'all_methods_before_moon': ('01100203ff040401060514036b02180802081f00', True),
    'non_moon_item_then_end': ('02180800', False),
}


def execute(path, group, species, rate, expected):
    from pyboy import PyBoy
    rom = bytearray(Path(path).read_bytes())
    if group in FIXTURES:
        data, target = FIXTURES[group]
        rom[JP_EVOS:JP_EVOS+2] = bytes.fromhex('007f')
        payload = bytes.fromhex(data)
        rom[0x43f00:0x43f00+len(payload)] = payload
        # Opposite answer in the caller's bank detects a wrong-bank read.
        rom[0xff00:0xff04] = bytes.fromhex('00000000' if target else '02081f00')
    game = PyBoy(BytesIO(rom), window='null', sound_emulated=False)
    game.set_emulation_speed(0)
    game.tick(600, render=False, sound=False)
    r = game.register_file
    reads = []
    pointer_reads = []

    def read_method(_):
        assert game.memory[0xff9d] == 0x10, 'wrong actual data bank'
        offset = 0x40000 + r.HL - 0x4000
        assert game.memory[r.HL] == rom[offset]
        reads.append(offset)

    def read_pointer(_):
        assert game.memory[0xff9d] == 0x10, 'wrong actual pointer bank'
        assert r.HL == 0x6753+2*(species-1)
        pointer_reads.append(r.HL)

    def returned(_):
        assert r.B == expected, (group, species, rate, r.B, expected)
        assert r.C == 0xa5 and (r.D << 8 | r.E) == 0xbeef, 'register corruption'
        assert r.SP == 0xd000, 'unbalanced stack'
        assert game.memory[0xff9d] == 3, 'bank not restored'
        assert game.memory[0x6f52] == rom[ENTRY], 'actual ROM bank not restored'
        assert len(pointer_reads) == 1
        if group == 'actual_251' and species == 61:
            assert {0x42e2c, 0x42e2f, 0x42e30} <= set(reads), 'second Moon record not read'
        print(json.dumps({'group': group, 'species': species, 'rate': rate,
                          'result': r.B, 'bank_10_byte_reads': reads}), flush=True)
        os._exit(0)

    # Real load instructions after genuine Bankswitch RST calls.
    game.hook_register(0, 0x3021, read_method, None)
    game.hook_register(0, 0x3031, read_pointer, None)
    game.hook_register(0, 0x100, returned, None)
    game.memory[0xffff] = game.memory[0xff0f] = 0
    game.memory[0xff70] = 1
    game.memory[0x2000] = game.memory[0xff9d] = 3
    game.memory[0xd235] = species
    game.memory[0xcffe:0xd000] = [0, 1]
    r.SP = 0xcffe
    r.B = rate; r.C = 0xa5
    r.D = 0xbe; r.E = 0xef
    r.A = 0; r.F = 0xf0; r.HL = 0
    r.PC = ENTRY % 0x4000 + 0x4000
    game.tick(1, render=False, sound=False)
    raise AssertionError(('return not reached', group, species, hex(r.PC)))


def main():
    path = str(ROOT/'work/moon_ball_fix_isolated.gbc')
    if len(sys.argv) == 2:
        path = str(Path(sys.argv[1]).resolve())
    input_rom = Path(path).read_bytes()
    input_sha256 = sha256(input_rom).hexdigest()
    assert moon_targets(input_rom) == TARGETS
    cases = [('actual_251', species, 20, 80 if species in TARGETS else 20)
             for species in range(1, 252)]
    cases += [('target_boundaries', species, rate, min(255, rate*4))
              for species in TARGETS for rate in RATES]
    cases += [('non_target_boundaries', species, rate, rate)
              for species in (1, 133, 236) for rate in RATES]
    cases += [(name, 1, rate, min(255, rate*4) if target else rate)
              for name, (_, target) in FIXTURES.items() for rate in RATES]

    def run(case):
        command = [sys.executable, __file__, '--child', path, *map(str, case)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, (case, result.stdout, result.stderr)
        return json.loads(result.stdout.splitlines()[-1])

    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(run, cases):
            results.append(result)
            if len(results) % 50 == 0:
                print('moon_ball_cpu_progress', len(results), '/', len(cases), flush=True)
    report = {'cpu_cases': len(results), 'targets': TARGETS, 'results': results,
              'rom_path': path, 'input_sha256': input_sha256,
              'all_cases_check': ['full_entry', 'real_bank_switch', 'actual_bank_10_reads',
                                 'restored_bank_03', 'balanced_stack', 'preserved_C_DE']}
    (ROOT/'work/moon_ball_fix_cpu_results.json').write_text(json.dumps(report, indent=2)+'\n')
    print('moon_ball_fix_cpu_passed', len(results), 'full-entry CPU cases; 251 species and 5 fixtures')


if __name__ == '__main__':
    if sys.argv[1:2] == ['--child']:
        execute(sys.argv[2], sys.argv[3], *map(int, sys.argv[4:7]))
    else:
        main()
