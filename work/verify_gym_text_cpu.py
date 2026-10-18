"""Run original JP text dispatch and inline-ASM victory-text thunks on CPU."""
from io import BytesIO
import os
import subprocess
import sys
from map_layout import file_offset,word
from port_gym_rematches import apply_gym_rematches
from verify_gym_rematches import EXPECTED,inputs
from gym_text_engine import text_engine

if len(sys.argv)==1:
    for index in range(len(EXPECTED)):
        for mode in ('call','return'):
            subprocess.run([sys.executable,__file__,str(index),mode],check=True)
    print('gym_text_cpu_cases_passed',len(EXPECTED)*2)
    raise SystemExit

from pyboy import PyBoy
index,mode=int(sys.argv[1]),sys.argv[2]
name,tail,cls=EXPECTED[index]
original,english,perfect=inputs()
rom=bytearray(original)
apply_gym_rematches(original,english,perfect,rom)
engine=text_engine(original)
entry=file_offset(0x62,word(rom,tail+2))
bank=tail//0x4000
thunk=word(rom,entry+15)
defeat=word(rom,file_offset(bank,thunk)+4)
if mode=='return':
    # Harness-only stub: skip UI at FarPrintText, retain actual command loop
    # and the inline code's entire stack/return/terminator behavior.
    rom[engine['farprint']]=0xc9
else:
    assert mode=='call'
pyboy=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
pyboy.tick(600,render=False,sound=False)
pyboy.memory[0x2000]=pyboy.memory[0xff9d]=bank
pyboy.memory[0xffff]=pyboy.memory[0xff0f]=0
pyboy.memory[0xcffe]=0
pyboy.memory[0xcfff]=1
pyboy.register_file.SP=0xcffe
pyboy.register_file.HL=thunk
pyboy.register_file.PC=engine['loop']


def done(emulator):
    if mode=='call':
        okay=(emulator.register_file.A==0x62 and emulator.register_file.HL==defeat
              and emulator.memory[0xff9d]==bank)
    else:
        okay=(emulator.register_file.HL==thunk+14 and emulator.register_file.SP==0xd000
              and emulator.memory[0xff9d]==bank)
    print('gym_text_cpu',name,mode,bool(okay),'hl',hex(emulator.register_file.HL),flush=True)
    os._exit(0 if okay else 1)


pyboy.hook_register(0,engine['farprint'] if mode=='call' else 0x100,done,pyboy)
pyboy.tick(1,render=False,sound=False)
raise RuntimeError('gym text CPU probe did not finish')
