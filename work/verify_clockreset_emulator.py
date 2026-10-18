"""Execute patched JP title keys and SRAM request/cancellation on LR35902."""
from pc_env import workspace
from pathlib import Path
from io import BytesIO
import os, subprocess, sys
from port_clock_reset import clock_reset_payload

ROOT=workspace()
CASES = ('none','a','start','delete','reset','both','partial',
         'confirm_empty','confirm_patterned','no_empty','no_patterned','b_empty','b_patterned')
if len(sys.argv)==1:
    for case in CASES:
        subprocess.run([sys.executable,__file__,case],check=True)
    print('clock_reset_cpu_cases_passed',len(CASES))
    raise SystemExit
from pyboy import PyBoy
case=sys.argv[1]
assert case in CASES
_, labels=clock_reset_payload()
rom=(ROOT/'work/clockreset_test.gbc').read_bytes()
p=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
p.tick(600,render=False,sound=False)
r=p.register_file
r.SP=0xcffe
p.memory[0xcffe:0xd000]=[0,1]
p.memory[0xffff]=0
p.memory[0xff0f]=0
p.memory[0x2000]=1
p.memory[0xff9d]=1
r.F=0

def ram_snapshot():
    p.memory[0]=0x0a
    result=[]
    for bank in range(4):
        p.memory[0x4000]=bank
        result.append(bytes(p.memory[0xa000:0xc000]))
    p.memory[0]=0
    return result

if case in CASES[:7]:
    buttons={'none':0,'a':1,'start':8,'delete':0x46,'reset':0x86,'both':0xc6,'partial':0x82}[case]
    p.memory[0xffa8]=buttons
    p.memory[0xcf57]=2
    p.memory[0xcf58]=0x7f
    r.PC=0x648c
else:
    patterned=case.endswith('patterned')
    p.memory[0]=0x0a
    for bank in range(4):
        p.memory[0x4000]=bank
        p.memory[0xa000:0xc000]=[(i*17+bank*41)&255 if patterned else 0xff for i in range(0x2000)]
    p.memory[0]=0
    before=ram_snapshot()
    p.memory[0xcf9d]=1 if case.startswith('no') else 2
    r.F=0x10 if case.startswith('b_') else 0
    r.PC=labels['decision']
    # Stop before the success message, after the actual SRAM routine returned.
    def success_message(_):
        r.PC=0x100
        r.SP+=2
    p.hook_register(1,labels['request']+13,success_message,None)

def done(_):
    good=(r.SP==0xd000 and p.memory[0xff9d]==1)
    if case in CASES[:7]:
        expect={'none':(2,0x7f),'a':(0x82,0),'start':(0x82,0),'delete':(0x82,1),
                'reset':(0x82,4),'both':(0x82,1),'partial':(2,0x7f)}[case]
        good &= tuple(p.memory[0xcf57:0xcf59])==expect
    else:
        expected=[bytearray(block) for block in before]
        if case.startswith('confirm'):expected[0][0xc80]=0x80
        good &= ram_snapshot()==expected
    print('clock_reset_cpu',case,bool(good),'SP',hex(r.SP),flush=True)
    os._exit(0 if good else 1)
p.hook_register(0,0x100,done,None)
p.tick(1,render=False,sound=False)
raise RuntimeError('clock reset probe did not return')
