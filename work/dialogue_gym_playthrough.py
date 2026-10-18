"""Local gym rematch playthrough from the isolated cave test save state."""
from io import BytesIO
import argparse
import re
from collections import deque
from pyboy import PyBoy
from map_layout import ROOT,maps,events,word

parser=argparse.ArgumentParser()
parser.add_argument('--phase',type=int,default=0)
args=parser.parse_args()
rom=(ROOT/'work/development_only_jp_partial.gbc').read_bytes()
layout=maps(rom,True,primary_bank=0x60)
gym=layout['VioletGym']
matches=list(re.finditer(re.escape(bytes.fromhex('fa7bdcea'))+b'..'+re.escape(bytes.fromhex('fa7cdcea'))+b'..'+re.escape(bytes.fromhex('37c9')),rom[:0x4000],re.DOTALL))
assert len(matches)==1
warp_tail=matches[0].end()-1
p=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
p.set_emulation_speed(0)
with (ROOT/'work/cave_test_state.bin').open('rb') as stream:p.load_state(stream)
def tick(n):p.tick(n,render=True,sound=False)
def press(key,n=30):p.button(key,5);tick(n)
def hold(key,n):p.button_press(key);tick(n);p.button_release(key);tick(8)
def shot(name):p.screen.image.save(ROOT/f'work/dialogue_gym_{name}.png')
def status():print('map',list(p.memory[0xdc7b:0xdc83]),'pc',hex(p.register_file.PC),'battle',p.memory[0xd260],flush=True)

# Test fixture only: post-Falkner progression flags, no user save modified.
for event in (0x4bd,0x08,0x3fb,0x3fc):
    p.memory[0xda65+event//8] |= 1<<(event%8)

def redirect(_):
    if p.memory[0xdc7b]==24 and p.memory[0xdc7c]==7:
        p.memory[0xd106:0xd109]=[1,gym['group'],gym['map_id']]

p.hook_register(0,warp_tail,redirect,None)
completed=[]
victory=[]
def script_end(_):
    pos=p.memory[0xd42b]|p.memory[0xd42c]<<8
    if p.memory[0xd42a]==0x62 and pos==0x4019:
        completed.append(True)
def farprint(_):
    if p.register_file.A==0x62 and p.register_file.HL==0x4035:
        victory.append(True)
p.hook_register(0x25,word(rom,0x96cb1+0x90*2),script_end,None)
p.hook_register(0,0x317c,farprint,None)
hold('up',32);hold('right',64);hold('up',32);tick(160)
shot('arrival');status()
print('gym_destination',gym['group'],gym['map_id'],flush=True)
print('test_party_moves',list(p.memory[0xdca7:0xdcab]),flush=True)
print('gym_header',gym['header'].hex(),'size',gym['height'],gym['width'],flush=True)
collision=(ROOT/f"pokekuristaru/tilesets/{gym['header'][1]:02d}_collision.bin").read_bytes()
blocks=rom[gym['blockdata']:gym['blockdata']+gym['height']*gym['width']]
grid={}
for y in range(gym['height']*2):
    for x in range(gym['width']*2):
        tile=blocks[(y//2)*gym['width']+x//2]
        grid[y,x]=collision[tile*4+(y%2)*2+x%2]
    print(''.join('.' if grid[y,x]==0 else '#' for x in range(gym['width']*2)),flush=True)
if args.phase>=1:
    start=tuple(p.memory[0xdc7d:0xdc7f])
    target=(2,5)
    people=events(rom,gym['events'])['people']
    occupied={(v[1]-4,v[2]-4) for v in people}
    queue=deque([(start,[])])
    seen={start}
    while queue:
        position,path=queue.popleft()
        if position==target:break
        for key,dy,dx in [('up',-1,0),('down',1,0),('left',0,-1),('right',0,1)]:
            nxt=(position[0]+dy,position[1]+dx)
            if grid.get(nxt,7)==0 and nxt not in occupied and nxt not in seen:
                seen.add(nxt);queue.append((nxt,path+[(key,nxt)]))
    else:raise AssertionError(('no route to leader',start,target))
    for key,expected in path:
        previous=tuple(p.memory[0xdc7d:0xdc7f])
        press(key,24)
        actual=tuple(p.memory[0xdc7d:0xdc7f])
        if actual==previous:
            press(key,24)
            actual=tuple(p.memory[0xdc7d:0xdc7f])
        assert actual==expected,('walk',key,expected,actual)
    press('up',24)
    tick(60)
    shot('approach');status()
if args.phase>=2:
    press('a',120)
    shot('conversation');status()
if args.phase>=3:
    for index in range(12):
        press('a',80)
        if index in (2,3,4,5,6):shot('progress_'+str(index))
    shot('battle');status()
if args.phase>=4:
    for _ in range(8):press('a',80)
    shot('moves');status()
if args.phase>=5:
    press('down',24);press('a',120)
    captured=False
    for index in range(60):
        press('a',80)
        if index%5==0:shot('fight_'+str(index))
        if victory and not captured:
            tick(90);shot('victory_text');captured=True
        if completed:
            tick(160)
            break
    shot('result');status()
    print('gym_rematch_completed',bool(completed),'localized_defeat_reached',bool(victory),flush=True)
    assert completed and victory
    assert list(p.memory[0xdc7b:0xdc7f])==[gym['group'],gym['map_id'],2,5]
    hold('down',16)
    print('after_return_walk',list(p.memory[0xdc7b:0xdc7f]),flush=True)
    assert p.memory[0xdc7d]>2
    shot('returned_walk')
p.stop(save=False)
