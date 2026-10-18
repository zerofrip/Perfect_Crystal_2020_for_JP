"""Run the actual JP nickname, evolution-compatibility, HP and DV routines."""
from io import BytesIO
import os
import subprocess
import sys
from map_layout import word,file_offset
from port_remaining_features import apply_remaining_features
from verify_remaining_features import inputs

CASES=[('trade',str(i)) for i in range(7)]+[('party',str(i)) for i in (0x16,0x17,0x18,0x22,0x08)]+[('hp','0'),('red','0')]
if len(sys.argv)==1:
    for mode,case in CASES:subprocess.run([sys.executable,__file__,mode,case],check=True)
    print('remaining_cpu_cases_passed',len(CASES))
    raise SystemExit

from pyboy import PyBoy
mode=sys.argv[1];case=int(sys.argv[2])
j,u,p=inputs();rom=bytearray(j)
apply_remaining_features(j,u,p,rom)
em=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
em.tick(600,render=False,sound=False)
em.memory[0xffff]=em.memory[0xff0f]=0
em.register_file.SP=0xcffe
em.memory[0xcffe]=0;em.memory[0xcfff]=1
def pair_set(pair,value):
    setattr(em.register_file,pair[0],value>>8)
    setattr(em.register_file,pair[1],value&255)
def pair_get(pair):
    return (getattr(em.register_file,pair[0])<<8)|getattr(em.register_file,pair[1])
target_bank=0
target_pc=0x100
if mode=='trade':
    bank=0x3f;pc=0x7f80
    em.memory[0xcf57]=case
    em.register_file.HL=0x4e57+case*16+3
    pair_set('DE',0xc6f5)
    for i in range(8):em.memory[0xc6f4+i]=0xa5
    name=rom[0xfce57+case*16+3:0xfce57+case*16+7]+b'\x50'
    expected=bytes.fromhex('13e313d88450') if case==3 else name
elif mode=='party':
    bank=0x14;pc=0x4266
    table=0x42753+132*2 # Eevee, all five evolution records plus terminator.
    em.register_file.HL=0x4000+table%0x4000
    em.memory[0xd0c6]=case
    for i in range(20):em.memory[0xd05b+i]=0
    # Stale text after the old ten-byte copy could mimic another evolution.
    # The full sixteen-byte copy must overwrite this false Leaf Stone record.
    em.memory[0xd05b+12]=2;em.memory[0xd05b+13]=0x22;em.memory[0xd05b+14]=135
    expected=0x42a1 if case in (0x16,0x17,0x18) else 0x42a6
elif mode=='hp':
    bank=3;pc=0x599d;target_bank=3;target_pc=0x59a7
    pair_set('BC',50)
    pair_set('DE',100)
    em.register_file.SP=0xcff8
    # Original caller's saved BC, DE and HL, in the real stack order.
    for i,b in enumerate(bytes.fromhex('3412efbe7777')):em.memory[0xcff8+i]=b
    expected=24
else:
    assert mode=='red'
    bank=9;pc=0x741d
    em.memory[0xd260]=63
    em.register_file.HL=0x1234
    expected=0xffff
em.memory[0x2000]=em.memory[0xff9d]=bank
em.register_file.PC=pc


def done(emulator):
    if mode=='trade':
        actual=bytes(emulator.memory[0xc6f5:0xc6f5+len(expected)])
        okay=(actual==expected and emulator.memory[0xc6f4]==0xa5 and emulator.memory[0xc6fb]==0xa5)
    elif mode=='party':
        actual=pair_get('DE')
        okay=actual==expected
    elif mode=='hp':
        actual=emulator.register_file.A
        okay=(actual==expected and pair_get('DE')==0xbeef and pair_get('BC')==0x1234
              and emulator.register_file.HL==0xd222 and emulator.register_file.SP==0xcffe)
    else:
        actual=pair_get('BC')
        okay=actual==expected and emulator.register_file.HL==0x1234
    print('remaining_cpu',mode,case,bool(okay),'actual',actual.hex() if isinstance(actual,bytes) else hex(actual),flush=True)
    os._exit(0 if okay else 1)


em.hook_register(target_bank,target_pc,done,em)
em.tick(1,render=False,sound=False)
raise RuntimeError('remaining CPU probe did not finish')
