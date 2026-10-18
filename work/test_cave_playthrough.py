"""Boot JP Crystal, traverse all cave floors, and start the Mewtwo battle.

ROM/SRAM are in memory. No adjacent .sav/.ram/.rtc file is read or written.
Test setup adds one party member through actual AddPartyMon, redirects one
bedroom warp, unlocks the guard, disables random encounters, and provides Surf
state for water entry. Every subsequent cave step/warp uses the actual engine.
"""
from pathlib import Path
from io import BytesIO
import argparse
import hashlib
from collections import deque
from pyboy import PyBoy
from map_layout import ROOT, maps, events

parser=argparse.ArgumentParser()
parser.add_argument('rom',nargs='?',default=str(ROOT/'work/development_only_jp_partial.gbc'))
parser.add_argument('--phase',type=int,choices=range(7),default=6,
                    help='0: boot/state only; 1: city; 2: 1F; 3: 2F; 4: B1; 5: dialogue; 6: battle')
parser.add_argument('--no-state',action='store_true',help='do not replace the shared local test state')
args=parser.parse_args()
rom=Path(args.rom).read_bytes()
print('input_rom_sha256',hashlib.sha256(rom).hexdigest(),flush=True)
assert rom[0x8002d:0x80034]==bytes.fromhex('fa50d9fe002810')
import re
pattern=b'\x21..'+re.escape(bytes.fromhex('cb6e20'))+b'.\xfa..'+re.escape(bytes.fromhex('fe04'))
matches=list(re.finditer(pattern,rom[0x94000:0x98000],re.DOTALL))
assert len(matches)==1
wild_disable_flags=int.from_bytes(matches[0].group()[1:3],'little')
warp_matches=list(re.finditer(re.escape(bytes.fromhex('fa7bdcea'))+b'..'+re.escape(bytes.fromhex('fa7cdcea'))+b'..'+re.escape(bytes.fromhex('37c9')),rom[:0x4000],re.DOTALL))
assert len(warp_matches)==1
warp_tail=warp_matches[0].end()-1
assert warp_tail==0x22b0 and wild_disable_flags==0xd83f
p=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
force_surf=False
def tick(n):
    if force_surf:
        for _ in range(n):
            p.memory[0xd950]=4
            p.tick(1,render=True,sound=False)
    else:p.tick(n,render=True,sound=False)
def press(key,n=30):p.button(key,5);tick(n)
def hold(key,n):p.button_press(key);tick(n);p.button_release(key);tick(8)
def shot(name):p.screen.image.save(ROOT/f'work/cave_{name}.png')
def status():
    print('cpu',hex(p.register_file.PC),'map',list(p.memory[0xdc7b:0xdc83]),'menu',hex(p.memory[0xcf9d]),flush=True)

tick(600);press('start',120);press('a',120)
for i in range(130):press('a',30)
shot('intro')
assert tuple(p.memory[0xdc7b:0xdc7f])==(24,7,3,3)
def add_test_party():
    assert rom[0xdae1:0xdae7]==bytes.fromhex('119ddcfa53cf')
    assert p.memory[0xdc9d]==0
    r=p.register_file
    registers={key:getattr(r,key) for key in ('A','B','C','D','E','F','HL','PC','SP')}
    old_bank=p.memory[0xff9d]
    old_ie,old_if=p.memory[0xffff],p.memory[0xff0f]
    stack=bytes(p.memory[0xcffe:0xd000])
    completed=[]
    def returned(_):
        completed.append(True)
        p.memory[0xcffe:0xd000]=stack
        p.memory[0x2000]=old_bank;p.memory[0xff9d]=old_bank
        p.memory[0xffff]=old_ie;p.memory[0xff0f]=old_if
        for key,value in registers.items():setattr(r,key,value)
    p.hook_register(0,0x100,returned,None)
    p.memory[0xd0c8]=160  # Feraligatr, created by actual AddPartyMon
    p.memory[0xd103]=70
    p.memory[0xcf53]=0
    p.memory[0xd25e]=0
    p.memory[0xcffe:0xd000]=[0,1]
    p.memory[0xffff]=0;p.memory[0xff0f]=0
    p.memory[0x2000]=3;p.memory[0xff9d]=3
    r.SP=0xcffe;r.PC=0x5ae1
    for _ in range(12):
        tick(1)
        if completed:break
    p.hook_deregister(0,0x100)
    assert completed and p.memory[0xdc9d]==1 and p.memory[0xdca5]==160
    assert p.memory[0xdca5+31]==70 and any(p.memory[0xdca5+34:0xdca5+36])
    if not args.no_state:
        with (ROOT/'work/cave_test_state.bin').open('wb') as stream:p.save_state(stream)
    print('native_add_party_passed',p.memory[0xdc9d],p.memory[0xdca5],p.memory[0xdca5+31],flush=True)
add_test_party()
if args.phase==0:
    p.stop(save=False)
    raise SystemExit
layout=maps(rom,True,primary_bank=0x60)
collision=(ROOT/'pokekuristaru/tilesets/24_collision.bin').read_bytes()
perfect=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
perfect_layout=maps(perfect,True)
assert collision in rom and collision in perfect
cave_names=('CeruleanCave1F','CeruleanCave2F','CeruleanCaveB1')
grids={};warps={}
blocked=set()
for name in cave_names:
    entry=layout[name];grid={}
    blocks=rom[entry['blockdata']:entry['blockdata']+entry['width']*entry['height']]
    reference=perfect_layout[name]
    assert (entry['width'],entry['height'])==(reference['width'],reference['height'])
    assert blocks==perfect[reference['blockdata']:reference['blockdata']+len(blocks)]
    for y in range(entry['height']*2):
        for x in range(entry['width']*2):
            block=blocks[(y//2)*entry['width']+x//2]
            grid[(y,x)]=collision[block*4+(y%2)*2+x%2]
    grids[entry['map_id']]=grid
    warps[entry['map_id']]=events(rom,entry['events'])['warps']
    assert warps[entry['map_id']]==events(perfect,reference['events'])['warps']
def path_to(start,target):
    q=deque([(start,[])]);seen={start}
    while q:
        state,path=q.popleft()
        if state==target:return path
        mid,y,x=state
        for key,dy,dx in [('up',-1,0),('down',1,0),('left',0,-1),('right',0,1)]:
            if (state,key) in blocked:continue
            ny,nx=y+dy,x+dx
            if grids[mid].get((ny,nx),7) not in (0,0x29,0x70,0x72,0x7b,0xb2):continue
            nxt=(mid,ny,nx)
            for warp in warps[mid]:
                if (warp[0],warp[1])==(ny,nx):
                    if warp[4] not in grids:nxt=None;break
                    destination=warps[warp[4]][warp[2]-1]
                    nxt=(warp[4],destination[0],destination[1]);break
            if nxt is not None and nxt not in seen:
                seen.add(nxt);q.append((nxt,path+[(key,nxt)]))
    for mid in grids:
        print('reachable_map',mid,flush=True)
        for y in range(18):
            print(''.join('+' if (mid,y,x) in seen else {0:'.',7:'#',0x29:'~',0xb2:'-',0x72:'W',0x70:'v'}.get(grids[mid][(y,x)],'?') for x in range(30)),flush=True)
    raise AssertionError(('no path',start,target,'visited',len(seen)))
def navigate(target):
    global force_surf
    for step in range(1200):
        previous=tuple(p.memory[0xdc7c:0xdc7f])
        if previous==target:
            print('navigation_passed',target,'steps',step,'blocked',len(blocked),flush=True)
            return
        key,expect=path_to(previous,target)[0]
        force_surf=expect[0]==previous[0] and grids[previous[0]][expect[1:]]==0x29
        if expect[0]==previous[0] and grids[previous[0]][expect[1:]]==0x29:
            p.memory[0xd950]=4
        press(key,24)
        if expect[0]!=previous[0]:tick(160)
        actual=tuple(p.memory[0xdc7c:0xdc7f])
        if actual==previous:
            if expect[0]==previous[0] and grids[previous[0]][expect[1:]]==0x29:
                p.memory[0xd950]=4
            press(key,24)
            if expect[0]!=previous[0]:tick(160)
            actual=tuple(p.memory[0xdc7c:0xdc7f])
        force_surf=False
        if actual==previous:
            blocked.add((previous,key))
            continue
        assert actual==expect,(key,expect,actual)
    raise AssertionError(('navigation step bound',target))
if args.phase>=1:
    p.memory[wild_disable_flags] |= 0x20
    redirected=[]
    def redirect(_):
        if p.memory[0xdc7b]==24 and p.memory[0xdc7c]==7:
            p.memory[0xd106:0xd109]=[7,7,17]
            redirected.append(True)
    p.hook_register(0,warp_tail,redirect,None)
    # Test-only postgame availability; no game save is read or overwritten.
    p.memory[0xda65+(0x74f//8)] |= 1<<(0x74f%8)
    hold('up',32);hold('right',64);hold('up',32);tick(160)
    assert len(redirected)==1 and tuple(p.memory[0xdc7b:0xdc7f])==(7,17,14,2)
    shot('city');status()
    if args.phase>=2:
        hold('up',16);tick(160)
        assert tuple(p.memory[0xdc7b:0xdc7f])==(7,18,15,25)
        shot('1f');status()
        if args.phase>=3:
            hold('up',96);hold('left',32);hold('up',64);tick(120)
            assert tuple(p.memory[0xdc7b:0xdc7f])==(7,19,7,23)
            shot('stairs');status()
            if args.phase>=4:
                navigate((20,5,3))
                shot('b1');status()
                if args.phase>=5:
                    navigate((20,14,27))
                    press('up',24);press('a',180)
                    shot('mewtwo_dialogue');status()
                    if args.phase>=6:
                        for index in range(12):
                            press('a',120)
                            if index in (0,1,2):shot('mewtwo_dialogue_'+str(index+2))
                        shot('mewtwo_battle');status()
                        assert p.memory[0xd237]==150 and p.memory[0xd244]==70
                        assert p.memory[0xd25e]==1
                        assert p.memory[0xda65+0x105//8] & (1<<(0x105%8))
                        print('mewtwo_battle_passed','species',p.memory[0xd237],
                              'level',p.memory[0xd244],'battle_mode',p.memory[0xd25e],flush=True)
print('cave_playthrough_passed','phase',args.phase,flush=True)
p.stop(save=False)
