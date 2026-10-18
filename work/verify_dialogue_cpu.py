"""Check Route8's expanded-text thunk via original Japanese text dispatch."""
from io import BytesIO
import os
import subprocess
import sys
from pyboy import PyBoy
from map_layout import word
from gym_text_engine import text_engine
from port_dialogue_updates import apply_dialogue_updates
from verify_gym_rematches import inputs

if len(sys.argv)==1:
    for mode in ('call','return'):
        subprocess.run([sys.executable,__file__,mode],check=True)
    print('dialogue_text_cpu_cases_passed 2')
    raise SystemExit
mode=sys.argv[1]
original,en,perfect=inputs()
rom=bytearray(original)
apply_dialogue_updates(original,en,perfect,rom)
engine=text_engine(original)
if mode=='return':
    rom[engine['farprint']]=0xc9
else:
    assert mode=='call'
p=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
p.tick(600,render=False,sound=False)
p.memory[0x2000]=p.memory[0xff9d]=0x15
p.memory[0xffff]=p.memory[0xff0f]=0
p.memory[0xcffe]=0
p.memory[0xcfff]=1
p.register_file.SP=0xcffe
p.register_file.HL=0x41b8
p.register_file.PC=engine['loop']


def done(emulator):
    if mode=='call':
        good=emulator.register_file.A==0x65 and emulator.register_file.HL==word(rom,0x541bc)
    else:
        good=emulator.register_file.HL==0x41c6 and emulator.register_file.SP==0xd000
    good &= emulator.memory[0xff9d]==0x15
    print('dialogue_cpu',mode,bool(good),flush=True)
    os._exit(0 if good else 1)


p.hook_register(0,engine['farprint'] if mode=='call' else 0x100,done,p)
p.tick(1,render=False,sound=False)
raise RuntimeError('dialogue CPU probe did not complete')
