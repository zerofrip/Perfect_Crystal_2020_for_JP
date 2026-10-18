"""Local full Silph-guard conversation on the integrated Japanese ROM."""
from collections import deque
from hashlib import sha256
from io import BytesIO
import json
import re
from pyboy import PyBoy
from map_layout import ROOT,maps,events,word

rom=(ROOT/'work/development_only_jp_partial.gbc').read_bytes()
assert sha256(rom).hexdigest()=='bdb8b08177dc6e5a549c5d3ed2499a9835ae7c7c01ad0acafda659072335805e'
entry=maps(rom,True,primary_bank=0x60)['SilphCo1F']
matches=list(re.finditer(re.escape(bytes.fromhex('fa7bdcea'))+b'..'+re.escape(bytes.fromhex('fa7cdcea'))+b'..'+re.escape(bytes.fromhex('37c9')),rom[:0x4000],re.DOTALL))
assert len(matches)==1
p=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
p.set_emulation_speed(0)
with (ROOT/'work/cave_test_state.bin').open('rb') as stream:p.load_state(stream)
def tick(n):p.tick(n,render=True,sound=False)
def press(key,n=30):p.button(key,5);tick(n)
def hold(key,n):p.button_press(key);tick(n);p.button_release(key);tick(8)
def shot(name):p.screen.image.save(ROOT/f'work/remaining_play_{name}.png')
def coord():return tuple(p.memory[0xdc7d:0xdc7f])

def redirect(_):
    if p.memory[0xdc7b]==24 and p.memory[0xdc7c]==7:
        p.memory[0xd106:0xd109]=[1,entry['group'],entry['map_id']]
p.hook_register(0,matches[0].end()-1,redirect,None)
hold('up',32);hold('right',64);hold('up',32);tick(160)
assert list(p.memory[0xdc7b:0xdc7d])==[entry['group'],entry['map_id']]
shot('silph_arrival')
collision=(ROOT/f"pokekuristaru/tilesets/{entry['header'][1]:02d}_collision.bin").read_bytes()
blocks=rom[entry['blockdata']:entry['blockdata']+entry['height']*entry['width']]
grid={(y,x):collision[blocks[(y//2)*entry['width']+x//2]*4+(y%2)*2+x%2]
      for y in range(entry['height']*2) for x in range(entry['width']*2)}
people=events(rom,entry['events'])['people']
guard=people[1]
target=(guard[1]-3,guard[2]-4)
occupied={(v[1]-4,v[2]-4) for v in people}
queue=deque([(coord(),[])])
seen={coord()}
while queue:
    position,path=queue.popleft()
    if position==target:break
    for key,dy,dx in [('up',-1,0),('down',1,0),('left',0,-1),('right',0,1)]:
        nxt=(position[0]+dy,position[1]+dx)
        if grid.get(nxt,7)==0 and nxt not in occupied and nxt not in seen:
            seen.add(nxt);queue.append((nxt,path+[(key,nxt)]))
else:raise AssertionError(('no route to guard',coord(),target,grid))
for key,expected in path:
    previous=coord();press(key,24)
    if coord()==previous:press(key,24)
    assert coord()==expected,('walk',key,expected,coord())
press('up',24);tick(60)
assert coord()==target

# Test fixture starts with the old Upgrade gift flag clear. Snapshot after
# arrival/walking so no map-entry state is confused with conversation effects.
event_address=0xda65+0xde//8
p.memory[event_address]&=~(1<<(0xde%8))
flags_before=bytes(p.memory[0xda65:0xdb65])
command_hits={name:0 for name in ('giveitem','setevent','verbosegiveitem','guard_jump')}
def hit(name):
    def callback(_):command_hits[name]+=1
    return callback
for command,name in ((0x1f,'giveitem'),(0x33,'setevent'),(0x9d,'verbosegiveitem'),(0x51,'guard_jump')):
    p.hook_register(0x25,word(rom,0x96cb1+command*2),hit(name),None)
press('a',160)
shot('silph_notice')
print('notice',coord(),'commands',command_hits,'script_mode',p.memory[0xd428],flush=True)
assert command_hits['guard_jump']==1
for _ in range(3):
    press('a',100)
    if p.memory[0xd428]==0:break
flags_after=bytes(p.memory[0xda65:0xdb65])
assert flags_after==flags_before
assert command_hits=={'giveitem':0,'setevent':0,'verbosegiveitem':0,'guard_jump':1}
assert not p.memory[event_address]&(1<<(0xde%8))
press('down',24)
if coord()==target:press('down',24)
assert coord()==(target[0]+1,target[1]),('return to controls',target,coord())
shot('silph_returned_walk')
evidence={'rom_sha256':sha256(rom).hexdigest(),'map':[entry['group'],entry['map_id']],
          'guard_position':list(target),'after_conversation_walk':list(coord()),
          'script_commands':command_hits,'event_flags_256_bytes_unchanged':flags_before==flags_after,
          'upgrade_flag_0x00de_clear':not bool(p.memory[event_address]&(1<<(0xde%8))),
          'fixture':'cave_test_state.bin; bedroom stair redirect and initially clear Upgrade flag only'}
(ROOT/'work/remaining_play_evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps(evidence,indent=2),flush=True)
p.stop(save=False)
