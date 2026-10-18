"""Local game-menu save, RTC reset, and power-cycle regression test."""
from pc_env import workspace
from pathlib import Path
from io import BytesIO
import argparse,hashlib,json
from pyboy import PyBoy
from port_clock_reset import CAVE,clock_reset_payload

ROOT=workspace()
parser=argparse.ArgumentParser()
parser.add_argument('rom',nargs='?',default=str(ROOT/'work/development_only_jp_partial.gbc'))
args=parser.parse_args()
rom=Path(args.rom).read_bytes()
payload,labels=clock_reset_payload()
assert rom[CAVE:CAVE+len(payload)]==payload
print('input_sha256',hashlib.sha256(rom).hexdigest(),flush=True)
p=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
with (ROOT/'work/cave_test_state.bin').open('rb') as stream:p.load_state(stream)

def tick(n):p.tick(n,render=True,sound=False)
def press(key,n=60):p.button(key,5);tick(n)
def shot(label):p.screen.image.save(ROOT/f'work/clock_save_{label}.png')
def status(label):
    print(label,'PC',hex(p.register_file.PC),'map',list(p.memory[0xdc7b:0xdc7f]),'cursor',p.memory[0xcf9d],'time',p.memory[0xff94],p.memory[0xff96],flush=True)
def profile():
    return {'name':bytes(p.memory[0xd48e:0xd494]),'id':bytes(p.memory[0xd48c:0xd48e]),
            'party_count':p.memory[0xdc9d],'party':bytes(p.memory[0xdca5:0xdcd5]),
            'party_ot':bytes(p.memory[0xddc5:0xddcb]),'party_name':bytes(p.memory[0xdde9:0xddef]),
            'map':bytes(p.memory[0xdc7b:0xdc7f]),'events':bytes(p.memory[0xda65:0xdb65])}
def power_cycle(label):
    global p
    ram,rtc=BytesIO(),BytesIO()
    p.stop(save=True,ram_file=ram,rtc_file=rtc)
    (ROOT/f'work/clock_save_{label}.ram').write_bytes(ram.getvalue())
    (ROOT/f'work/clock_save_{label}.rtc').write_bytes(rtc.getvalue())
    ram.seek(0);rtc.seek(0)
    p=PyBoy(BytesIO(rom),ram_file=ram,rtc_file=rtc,window='null',sound_emulated=False)
    return ram.getvalue(),rtc.getvalue()
def sram_snapshot(size):
    p.memory[0]=0x0a
    blocks=[]
    for bank in range(size//0x2000):
        p.memory[0x4000]=bank
        blocks.append(bytes(p.memory[0xa000:0xc000]))
    p.memory[0]=0
    return b''.join(blocks)

tick(60);press('start');shot('menu');status('menu')
for _ in range(3):press('down',20)
press('a',150);shot('save_question');status('save_question')
press('a',200);shot('saved');status('saved')
baseline=profile()
initial_ram,initial_rtc=power_cycle('initial')
assert len(initial_ram)>=0x8000
print('saved_sram_bytes',len(initial_ram),'rtc_bytes',len(initial_rtc),flush=True)
tick(600);press('start',120)
p.button_press('down');p.button_press('b');p.button_press('select');tick(5)
p.button_release('down');p.button_release('b');p.button_release('select');tick(240)
shot('reset_question');status('reset_question')
press('down',30);press('a',120);shot('reset_requested');status('reset_requested')
requested_ram=sram_snapshot(len(initial_ram))
request_changes=[index for index,(a,b) in enumerate(zip(initial_ram,requested_ram)) if a!=b]
assert request_changes==[0xc80] and requested_ram[0xc80]==0x80,request_changes
press('a',360);press('start',120);press('a',120)
shot('continue');status('continue')
press('a',120);shot('save_info');status('save_info')
press('a',180);shot('clock_warning');status('clock_warning')
press('a',180);shot('clock_edit');status('clock_edit')
press('a',180);shot('clock_controls');status('clock_controls')
target=(3,17,42)
for index,value in enumerate(target):
    address=0xd21e+index
    for _ in range(65):
        if p.memory[address]==value:break
        press('up',24)
    assert p.memory[address]==value,(index,p.memory[address])
    if index<2:press('right',24)
assert tuple(p.memory[0xd21e:0xd221])==target
shot('clock_selected')
press('a',180);shot('clock_confirm');status('clock_confirm')
press('a',180);shot('clock_done');status('clock_done')
press('a',240);shot('resumed');status('resumed')
actual=profile()
print('profile_fields_changed',[key for key in baseline if baseline[key]!=actual[key]],flush=True)
assert actual==baseline
assert (p.memory[0xd4be]%7,p.memory[0xff94],p.memory[0xff96])==target
press('start',60)
for _ in range(6):
    if p.memory[0xcf9d]==4:break
    press('down',24)
assert p.memory[0xcf9d]==4
press('a',150);press('a',200);press('a',200)
shot('resaved');status('resaved')
final_ram,final_rtc=power_cycle('final')
print('rtc_request_flag',hex(final_ram[0xc80]),flush=True)
assert final_ram[0xc80]&0x80==0
tick(600);press('start',120);press('a',120)
shot('final_main_menu');status('final_main_menu')
press('a',120);press('a',240)
shot('final_resumed');status('final_resumed')
print('final_profile_fields_changed',[key for key in baseline if baseline[key]!=profile()[key]],flush=True)
assert profile()==baseline
assert (p.memory[0xd4be]%7,p.memory[0xff94],p.memory[0xff96])==target
print('clock_save_roundtrip_passed','weekday',target[0],'hour',target[1],'minute',target[2],flush=True)
evidence={
    'passed':True,'rom_sha256':hashlib.sha256(rom).hexdigest(),
    'sram_bytes':len(initial_ram),'rtc_bytes':len(initial_rtc),
    'reset_request_changed_sram_offsets':request_changes,
    'clock_weekday_hour_minute':list(target),'final_rtc_request_flag':final_ram[0xc80],
    'preserved_fields':list(baseline),
    'initial_sram_sha256':hashlib.sha256(initial_ram).hexdigest(),
    'final_sram_sha256':hashlib.sha256(final_ram).hexdigest(),
    'game_menu_saves':2,'power_cycles':2,
    'setup':'Fresh new-game emulator state with one test party member; no user saves loaded',
}
(ROOT/'work/clock_save_evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
p.stop(save=False)
