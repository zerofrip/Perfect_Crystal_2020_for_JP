"""CPU tests of map headers and landmark readers in the actual JP ROM.

Each injected context runs until a home-bank sentinel, then exits before a
frame can execute with an artificial stack. Parent mode runs all cases.
"""
from io import BytesIO
import os
import subprocess
import sys
from map_layout import ROOT, maps, word, file_offset

CASES = ('header_old', 'header_new', 'header_shifted', 'copy_new',
         'coords_old', 'coords_new', 'name_old', 'name_new')
if len(sys.argv) == 1:
    for case in CASES:
        subprocess.run([sys.executable, __file__, case], check=True)
    print('map_port_cpu_cases_passed', len(CASES))
    raise SystemExit

from pyboy import PyBoy
case = sys.argv[1]
assert case in CASES
rom = (ROOT / 'work/development_only_jp_partial.gbc').read_bytes()
stock = (ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
layout = maps(rom, True, primary_bank=0x60)
emulator = PyBoy(BytesIO(rom), window='null', sound_emulated=False)
emulator.tick(600, render=False, sound=False)
r = emulator.register_file
r.SP = 0xCFFE
emulator.memory[0xCFFE] = 0
emulator.memory[0xCFFF] = 1
emulator.memory[0xFFFF] = 0
emulator.memory[0xFF0F] = 0
r.HL, r.B, r.C, r.D, r.E = 0xc123,0x12,0x34,0x56,0x78
bank = 7
if case.startswith('header') or case == 'copy_new':
    name = {'header_old':'CeruleanCity', 'header_new':'CeruleanCaveB1',
            'header_shifted':'GoldenrodPokeCenter1F', 'copy_new':'CeruleanCave1F'}[case]
    entry = layout[name]
    r.B, r.C, r.D, r.E = entry['group'], entry['map_id'], 0, 3
    r.PC = 0x2bde
    if case == 'copy_new':
        r.PC = 0x2c0f
        emulator.memory[0xdc7b] = entry['group']
        emulator.memory[0xdc7c] = entry['map_id']
elif case.startswith(('coords','name')):
    bank = 0x24
    index = 96 if case.endswith('new') else 55
    r.E = index
    prefix = bytes.fromhex('e56b26002929115765') if case.startswith('coords') else bytes.fromhex('e5d5c56b26002929115965')
    original_address = stock.index(prefix)
    r.PC = original_address % 0x4000 + 0x4000

emulator.memory[0x2000] = bank
emulator.memory[0xFF9D] = bank


def done(pyboy):
    regs = pyboy.register_file
    good = regs.SP == 0xd000 and pyboy.memory[0xFF9D] == bank
    if case.startswith('header'):
        good &= bytes((regs.C,regs.B)) == entry['header'][3:5]
    elif case == 'copy_new':
        good &= bytes(pyboy.memory[0xd1c9:0xd1ce]) == entry['header'][:5]
    elif case.startswith('coords'):
        expected = bytes((106,66)) if index == 96 else stock[0x92557+index*4:0x92559+index*4]
        good &= bytes((regs.E,regs.D)) == expected
        good &= (regs.HL,regs.B,regs.C) == (0xc123,0x12,0x34)
    else:
        if index == 96:
            expected = bytes.fromhex('99940fc934b3b8c2505050')
        else:
            offset = file_offset(0x24,word(stock,0x92557+index*4+2))
            expected = stock[offset:offset+11]
        actual = bytes(pyboy.memory[0xd05b:0xd066])
        good &= actual == expected
        good &= (regs.HL,regs.B,regs.C,regs.D,regs.E) == (0xc123,0x12,0x34,0x56,index)
        if actual != expected:
            print('name_buffer_mismatch', actual.hex(), expected.hex(), flush=True)
    print('map_port_cpu_check', case, bool(good), 'SP', hex(regs.SP),
          'bank', pyboy.memory[0xFF9D], flush=True)
    os._exit(0 if good else 1)


emulator.hook_register(0,0x100,done,emulator)
emulator.tick(1,render=False,sound=False)
raise RuntimeError('CPU probe did not return')
