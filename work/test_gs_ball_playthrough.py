"""Exercise the original Japanese GS Ball delivery after a real map warp."""
from io import BytesIO
from pathlib import Path
import sys,subprocess
from pyboy import PyBoy
from map_layout import ROOT
if len(sys.argv)==1:
 for case in ('locked','ready','received'):
  run=subprocess.run([sys.executable,__file__,case],capture_output=True,text=True,timeout=120)
  print(run.stdout,flush=True)
  assert run.returncode==0,run.stderr
 print('gs_ball_playthrough_passed',3)
 raise SystemExit
case=sys.argv[1]
rom=(ROOT/'work/development_only_jp_partial.gbc').read_bytes()
game=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
with (ROOT/'work/cave_test_state.bin').open('rb') as stream:game.load_state(stream)
def tick(n):game.tick(n,render=True,sound=False)
def press(key,n=30):game.button(key,5);tick(n)
def hold(key,n):game.button_press(key);tick(n);game.button_release(key);tick(8)
def flag(n):return bool(game.memory[0xda65+n//8]&(1<<(n%8)))
def setflag(n,value):
 a=0xda65+n//8;v=game.memory[a]&~(1<<(n%8));game.memory[a]=v|((1<<(n%8)) if value else 0)
setflag(0x74f,case!='locked');setflag(0x340,case=='received')
def redirect(_):
 if tuple(game.memory[0xdc7b:0xdc7d])==(24,7):game.memory[0xd106:0xd109]=[1,11,20]
game.hook_register(0,0x22b0,redirect,None)
hold('up',32);hold('right',64);hold('up',32);tick(160)
print(case,'entered',list(game.memory[0xdc7b:0xdc7f]),'gs',flag(0x340),flush=True)
game.screen.image.save(ROOT/f'work/gs_{case}_entry.png')
assert tuple(game.memory[0xdc7b:0xdc7d])==(11,20)
# Approach the front door; these two XY triggers are at (y=15,x=6/7).
hold('up',24);hold('down',48);tick(120)
game.screen.image.save(ROOT/f'work/gs_{case}_trigger.png')
for i in range(60):
 press('a',45)
 if i in (2,7,15):game.screen.image.save(ROOT/f'work/gs_{case}_dialogue_{i}.png')
print(case,'final',list(game.memory[0xdc7b:0xdc7f]),'gs',flag(0x340),'readyflag',flag(0xbe),flush=True)
game.screen.image.save(ROOT/f'work/gs_{case}_final.png')
assert flag(0x340)==(case!='locked')
if case=='ready':assert flag(0xbe)
game.stop(save=False)
