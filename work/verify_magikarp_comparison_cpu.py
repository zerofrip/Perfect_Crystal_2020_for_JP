"""Compare actual LR35902 execution with unsigned mathematics, including caller.

The original JP caller and comparison execute locally in PyBoy. No user SRAM
is opened: ROMs are supplied through BytesIO and workers stop at CPU hooks.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys

from fix_magikarp_comparison import apply_magikarp_comparison_fix, ENTRY, PATCH, RC1, CORRECT
from verify_magikarp_comparison_build import inputs, ROOT

BOUNDARIES = (
    (0, 0), (0, 1), (1, 0), (0xffff, 0xffff), (0xffff, 0), (0, 0xffff),
    (0x00ff, 0x0100), (0x0100, 0x00ff), (0xfffe, 0xffff), (0xffff, 0xfffe),
    (0x0101, 0x0100), (0x0100, 0x0101), (0x0100, 0x0100),
    (0x0200, 0x0101), (0x0101, 0x0200), (0x0100, 0xff01), (0xff01, 0x0100),
    (0x7fff, 0x8000), (0x8000, 0x7fff), (0xff00, 0xfeff), (0xfeff, 0xff00),
    (0x000f, 0x0010), (0x0010, 0x000f), (0x010f, 0x0110), (0x0110, 0x010f),
    (0x1234, 0x1234), (0x1235, 0x1234), (0x1233, 0x1234),
)


def worker(path, mode, bc, de, version):
    from pyboy import PyBoy
    raw = bytearray(Path(path).read_bytes())
    assert raw[ENTRY:ENTRY + 7] == CORRECT
    if version != 'correct':
        raw[PATCH] = {'original': 0xd0, 'rc1': 0}[version]
    p = PyBoy(BytesIO(raw), window='null', sound_emulated=False)
    p.tick(600, render=False, sound=False)
    r = p.register_file
    r.SP = 0xcffe
    p.memory[0xcffe:0xd000] = [0, 1]
    p.memory[0xffff] = 0
    p.memory[0xff0f] = 0
    p.memory[0x2000] = 0x3e
    p.memory[0xff9d] = 0x3e
    r.B, r.C, r.D, r.E = bc >> 8, bc & 255, de >> 8, de & 255
    r.HL, r.A, r.F = 0xc123, 0x5a, 0xf0
    r.PC = 0x7df5 if mode == 'helper' else 0x7da3

    def done(branch):
        print(json.dumps({'a': r.A, 'f': r.F, 'bc': (r.B << 8) | r.C,
                          'de': (r.D << 8) | r.E, 'hl': r.HL, 'sp': r.SP,
                          'bank': p.memory[0xff9d], 'branch': branch}), flush=True)
        os._exit(0)

    if mode == 'helper':
        p.hook_register(0, 0x100, done, 'returned')
    else:
        p.hook_register(0x3e, 0x7da8, done, 'interval')
        p.hook_register(0x3e, 0x7dd9, done, 'next')
    p.tick(1, render=False, sound=False)
    raise RuntimeError('comparison CPU checkpoint not reached')


def expected(bc, de):
    x, y = (bc >> 8, de >> 8) if bc >> 8 != de >> 8 else (bc & 255, de & 255)
    flags = 0x40 | (0x80 if x == y else 0) | (0x10 if x < y else 0)
    flags |= 0x20 if (x & 15) < (y & 15) else 0
    assert bool(flags & 0x10) == (bc < de)
    assert bool(flags & 0x80) == (bc == de)
    return x, flags


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'work/development_only_jp_partial.gbc'
    original, english, perfect = inputs()
    rom = bytearray(source.read_bytes())
    if rom[ENTRY:ENTRY + 7] == RC1:
        apply_magikarp_comparison_fix(original, english, perfect, rom)
    else:
        assert rom[ENTRY:ENTRY + 7] == CORRECT, 'neither RC1 nor repaired comparison'
    assert rom[0xFBDA3:0xFBDA8] == bytes.fromhex('cdf57d3031')
    snapshot = ROOT / 'work/magikarp_comparison_test.gbc'
    snapshot.write_bytes(rom)

    # Extract all 14 thresholds from the actual JP table (little endian + divisor).
    thresholds = [int.from_bytes(original[0xFBE03 + 3*i:0xFBE05 + 3*i], 'little')
                  for i in range(14)]
    assert thresholds == [110, 310, 710, 2710, 7710, 17710, 32710, 47710,
                          57710, 62710, 64710, 65210, 65410, 65510]
    cases = sorted(set(BOUNDARIES) | {(limit + delta, limit)
                                    for limit in thresholds for delta in (-1, 0, 1)})
    jobs = [('helper', bc, de, 'correct') for bc, de in cases]
    jobs += [('caller', bc, de, 'correct') for bc, de in cases]
    jobs += [('helper', 0x0100, 0x0101, 'original'), ('helper', 0x0200, 0x0101, 'rc1')]

    def run(job):
        mode, bc, de, version = job
        child = subprocess.run([sys.executable, __file__, '--worker', str(snapshot), mode,
                                str(bc), str(de), version], capture_output=True, text=True, check=True)
        observation = json.loads(child.stdout.splitlines()[-1])
        assert observation['bc'] == bc and observation['de'] == de
        assert observation['hl'] == 0xc123 and observation['bank'] == 0x3e
        assert observation['sp'] == (0xd000 if mode == 'helper' else 0xcffe)
        if version == 'correct':
            accumulator, flags = expected(bc, de)
            assert (observation['a'], observation['f']) == (accumulator, flags), (job, observation, flags)
            if mode == 'caller':
                assert observation['branch'] == ('interval' if bc < de else 'next'), (job, observation)
        else:
            assert bool(observation['f'] & 0x10) != (bc < de), 'regression control did not expose old bug'
        return {'mode': mode, 'bc': bc, 'de': de, 'version': version,
                'expected_less': bc < de, 'cpu': observation}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, jobs))
    report = {'input_rom': str(source), 'tested_rom_sha256': sha256(rom).hexdigest(),
              'correct_input_pairs': len(cases), 'correct_cpu_executions': 2*len(cases),
              'regression_controls': 2, 'actual_table_thresholds': thresholds, 'results': results}
    (ROOT / 'work/magikarp_comparison_cpu_results.json').write_text(json.dumps(report, indent=2) + '\n')
    print('magikarp_comparison_cpu_passed', len(cases), 'pairs;', 2*len(cases),
          'correct executions; 2 original/RC1 regression controls')
    print('caller_condition', 'next iff BC >= DE; interval iff BC < DE')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--worker':
        worker(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6])
    else:
        main()
