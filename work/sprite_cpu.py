"""CPU checks of the real Japanese bank mapper, pic loader and decompressor."""
from io import BytesIO
import os
import subprocess
import sys
from port_restored_sprites import ROOT,picture,word,PIC_POINTERS,TRAINER_POINTERS

CASES=['bank:18','bank:41','bank:46','front:1','front:124',
       'decompress:swimmer','decompress:jynx','frame:1','frame:124','frame:125']
if len(sys.argv)==1:
    for case in CASES:
        subprocess.run([sys.executable,__file__,case],check=True)
    print('sprite_cpu_checks_passed',len(CASES))
    raise SystemExit
from pyboy import PyBoy
case=sys.argv[1];kind,value=case.split(':')
rom=(ROOT/'work/sprite_isolated.gbc').read_bytes()
emulator=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
emulator.tick(600,render=False,sound=False)
r=emulator.register_file
r.SP=0xcffe
emulator.memory[0xcffe:0xd000]=[0,1]
emulator.memory[0xffff]=0
emulator.memory[0xff0f]=0
bank=0x34 if kind=='frame' else 0x14
emulator.memory[0x2000]=bank
emulator.memory[0xff9d]=bank
r.B=0x12;r.C=0x34;r.D=0x56;r.E=0x78;r.HL=0xc123
if kind=='bank':
    r.PC=0x525b;r.A=int(value)
elif kind=='front':
    r.PC=0x516d
    emulator.memory[0xd0c8]=int(value)
    pointer=PIC_POINTERS+(int(value)-1)*6
elif kind=='decompress':
    pointer=TRAINER_POINTERS+38*3 if value=='swimmer' else PIC_POINTERS+123*6
    address,_,expected=picture(rom,pointer)
    r.A=address//0x4000;r.HL=address%0x4000+0x4000
    r.D=0xd0;r.E=0;r.PC=0x0b2a
    emulator.memory[0xff70]=6
elif kind=='frame':
    emulator.memory[0xff70]=2
    emulator.memory[0xd16b]=int(value)
    emulator.memory[0xd16d]=int(value)
    r.PC=0x45ce

def done(_):
    assert r.SP==0xd000 and emulator.memory[0xff9d]==bank
    if kind=='bank':
        assert r.A==int(value)+0x36
        assert (r.B,r.C,r.D,r.E,r.HL)==(0x12,0x34,0x56,0x78,0xc123)
    elif kind=='front':
        address,_,_=picture(rom,pointer)
        assert r.B==address//0x4000 and r.HL==address%0x4000+0x4000
    elif kind=='decompress':
        assert bytes(emulator.memory[0xd000:0xd000+len(expected)])==expected
    elif kind=='frame':
        assert emulator.memory[0xd177]==0x35
        assert bytes(emulator.memory[0xd178:0xd17a])==rom[0xd4000+(int(value)-1)*2:0xd4002+(int(value)-1)*2]
    print('sprite_cpu_check',case,'PASS',flush=True)
    os._exit(0)

emulator.hook_register(0,0x100,done,None)
emulator.tick(1,render=False,sound=False)
raise RuntimeError(('CPU checkpoint not reached',case,hex(r.PC)))
