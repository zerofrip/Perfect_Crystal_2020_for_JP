"""Run real Japanese script commands through the actual dispatch table."""
from io import BytesIO
import os
import subprocess
import sys
from map_layout import ROOT

CASES = ['gs_'+side+'_'+state for side in ('left','right') for state in ('locked','ready','received')]
CASES += ['red_rewards','mewtwo_present','mewtwo_absent']
if len(sys.argv)==1:
    for case in CASES:
        subprocess.run([sys.executable,__file__,case],check=True)
    print('event_script_cpu_cases_passed',len(CASES))
    raise SystemExit

from pyboy import PyBoy
case=sys.argv[1]
assert case in CASES
rom=bytearray((ROOT/'work/development_only_jp_partial.gbc').read_bytes())
flags={0x74f:False,0x340:False,0x105:False}
rewards={0x2cd,0x2bc,0x2b9,0x2b7,0x2cf}
if case.startswith('gs_'):
    side,state=case.split('_')[1:]
    bank=0x15
    script=0x6940 if side=='left' else 0x6955
    flags[0x74f]=state!='locked'
    flags[0x340]=state=='received'
    steps=4 if state=='locked' else 6
    expected=0x6997 if state!='ready' else (0x694e if side=='left' else 0x6963)
elif case=='red_rewards':
    bank,script,steps,expected=0x1c,0x4bd3,6,0x7f8d
else:
    bank,script,steps=0x60,0x5485,2
    flags[0x105]=case=='mewtwo_absent'
    expected=0x548c if flags[0x105] else 0x548b

# Harness only: CALL the original RunScriptCommand N times, then return to
# the sentinel. No substitute script interpreter is used for these checks.
harness=bytes.fromhex('cda96c')*steps+bytes.fromhex('c30001')
assert rom[0x97fd0:0x97fd0+len(harness)]==bytes(len(harness))
rom[0x97fd0:0x97fd0+len(harness)]=harness
emulator=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
emulator.tick(600,render=False,sound=False)
for flag,enabled in {**flags,**{f:False for f in rewards}}.items():
    address=0xda65+flag//8
    value=emulator.memory[address]&~(1<<(flag%8))
    emulator.memory[address]=value|((1<<(flag%8)) if enabled else 0)
emulator.memory[0xd428]=1
emulator.memory[0xd42a]=bank
emulator.memory[0xd42b]=script&0xff
emulator.memory[0xd42c]=script>>8
emulator.memory[0x2000]=0x25
emulator.memory[0xff9d]=0x25
emulator.memory[0xffff]=0
emulator.memory[0xff0f]=0
emulator.register_file.SP=0xcffe
emulator.register_file.PC=0x7fd0


def done(pyboy):
    position=pyboy.memory[0xd42b]|(pyboy.memory[0xd42c]<<8)
    good=position==expected and pyboy.memory[0xd42a]==bank
    good &= pyboy.register_file.SP==0xcffe and pyboy.memory[0xff9d]==0x25
    observed={f for f in rewards if pyboy.memory[0xda65+f//8]&(1<<(f%8))}
    good &= observed==(rewards if case=='red_rewards' else set())
    print('event_script_cpu',case,bool(good),'next',hex(position),'expected',hex(expected),
          'rewards',len(observed),flush=True)
    os._exit(0 if good else 1)


emulator.hook_register(0,0x100,done,emulator)
emulator.tick(1,render=False,sound=False)
raise RuntimeError('Script CPU probe did not complete')
