"""Exercise actual JP CPU dispatch for rematch hooks and yes/no outcomes.

UI and combat are deliberately outside this narrow probe: it checks real
farjump, iftrue, winlosstext and loadtrainer through the original dispatch.
"""
from io import BytesIO
import os
import subprocess
import sys
from map_layout import ROOT,file_offset,word
from port_gym_rematches import apply_gym_rematches
from verify_gym_rematches import EXPECTED,inputs

if len(sys.argv)==1 or sys.argv[1]=='yes_only':
    modes=('yes',) if len(sys.argv)>1 else ('hook','no','yes')
    for index in range(len(EXPECTED)):
        for mode in modes:
            subprocess.run([sys.executable,__file__,str(index),mode],check=True)
    print('gym_cpu_cases_passed',len(EXPECTED)*len(modes))
    raise SystemExit

from pyboy import PyBoy
index,mode=int(sys.argv[1]),sys.argv[2]
name,tail,cls=EXPECTED[index]
original,english,perfect=inputs()
rom=bytearray(original)
apply_gym_rematches(original,english,perfect,rom)
entry=word(rom,tail+2)
payload=file_offset(0x62,entry)
if mode=='hook':
    bank,script,steps=tail//0x4000,0x4000+tail%0x4000,1
    expected=entry
elif mode=='no':
    bank,script,steps=0x62,entry+9,1
    expected=entry+12
else:
    assert mode=='yes'
    bank,script,steps=0x62,entry+9,3
    expected=entry+22

harness=bytes.fromhex('cda96c')*steps+bytes.fromhex('c30001')
assert rom[0x97fd0:0x97fd0+len(harness)]==bytes(len(harness))
rom[0x97fd0:0x97fd0+len(harness)]=harness
pyboy=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
pyboy.tick(600,render=False,sound=False)
for address in (0xd260,0xd262,0xd44a,0xd03d,0xd03e,0xd03f,0xd040):
    pyboy.memory[address]=0
pyboy.memory[0xc2dd]=1 if mode=='yes' else 0
pyboy.memory[0xd428]=1
pyboy.memory[0xd42a]=bank
pyboy.memory[0xd42b]=script&255
pyboy.memory[0xd42c]=script>>8
pyboy.memory[0x2000]=pyboy.memory[0xff9d]=0x25
pyboy.memory[0xffff]=pyboy.memory[0xff0f]=0
pyboy.register_file.SP=0xcffe
pyboy.register_file.PC=0x7fd0


def done(emulator):
    pos=emulator.memory[0xd42b]|emulator.memory[0xd42c]<<8
    okay=(pos==expected and emulator.memory[0xd42a]==0x62 and
          emulator.register_file.SP==0xcffe and emulator.memory[0xff9d]==0x25)
    trainer=(emulator.memory[0xd260],emulator.memory[0xd262],emulator.memory[0xd44a])
    wintext=emulator.memory[0xd03d]|emulator.memory[0xd03e]<<8
    okay &= trainer==((cls,1,0x81) if mode=='yes' else (0,0,0))
    okay &= wintext==(word(rom,payload+15) if mode=='yes' else 0)
    okay &= emulator.memory[0xd03f]==emulator.memory[0xd040]==0
    print('gym_cpu',name,mode,bool(okay),'next',hex(pos),'trainer',trainer,flush=True)
    os._exit(0 if okay else 1)


pyboy.hook_register(0,0x100,done,pyboy)
pyboy.tick(1,render=False,sound=False)
raise RuntimeError('gym CPU probe did not finish')
