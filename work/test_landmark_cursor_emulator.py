"""Exercise both actual map UI cursor paths, including unchanged wrap limits."""
from io import BytesIO
import os,sys,subprocess
from map_layout import ROOT
CASES=[('up',55,47,94,96),('up',96,47,94,56),('down',56,47,94,96),('down',96,47,94,55),
       ('up',94,47,94,47),('down',47,47,94,94),('up',46,1,46,1),('down',1,1,46,46)]
if len(sys.argv)==1:
 for viewer in (0,1):
  for index in range(len(CASES)):
   p=subprocess.run([sys.executable,__file__,str(viewer),str(index)],text=True,capture_output=True,timeout=30)
   assert p.returncode==0,(viewer,index,p.stdout,p.stderr)
 print('landmark_cursor_cpu_passed',16)
 raise SystemExit
from pyboy import PyBoy
viewer,index=map(int,sys.argv[1:]);direction,value,low,high,expected=CASES[index]
game=PyBoy(BytesIO((ROOT/'work/development_only_jp_partial.gbc').read_bytes()),window='null',sound_emulated=False)
game.tick(600,render=False,sound=False)
r=game.register_file
ram=0xc6d7 if viewer==0 else 0xd003
game.memory[ram]=value;game.memory[0x2000]=0x24;game.memory[0xff9d]=0x24
game.memory[0xffff]=0;game.memory[0xff0f]=0;r.SP=0xcffe
r.D=high;r.E=low
r.PC=((0x4fc3 if direction=='up' else 0x4fd0) if viewer==0 else
      (0x5b1f if direction=='up' else 0x5b2c))
def done(_):
 assert game.memory[ram]==expected,(direction,value,game.memory[ram],expected)
 assert (r.D,r.E,r.SP,game.memory[0xff9d])==(high,low,0xcffe,0x24)
 print('pass',viewer,index,flush=True);os._exit(0)
game.hook_register(0x24,0x4fdb if viewer==0 else 0x5b37,done,None)
game.tick(10,render=False,sound=False)
raise AssertionError(('no breakpoint',hex(r.PC)))
