"""Exercise the real title-to-menu path and capture local Japanese UI."""
from pc_env import workspace
from pathlib import Path
from io import BytesIO
from pyboy import PyBoy
from port_clock_reset import clock_reset_payload
ROOT=workspace()
_,labels=clock_reset_payload()
p=PyBoy(BytesIO((ROOT/'work/clockreset_test.gbc').read_bytes()),window='null',sound_emulated=False)
hits=[]
def hit(name):hits.append(name)
for name in ('input','menu','decision','request'):
    p.hook_register(1,labels[name],hit,name)
p.tick(600,render=True,sound=False)
p.button('start',5)
p.tick(120,render=True,sound=False)
if 'input' not in hits:
    p.button('a',5)
    p.tick(120,render=True,sound=False)
assert 'input' in hits, (p.register_file.PC,hits)
p.button_press('down');p.button_press('b');p.button_press('select')
p.tick(5,render=True,sound=False)
p.button_release('down');p.button_release('b');p.button_release('select')
p.tick(240,render=True,sound=False)
assert 'menu' in hits, hits
p.screen.image.save(ROOT/'work/clockreset_question.png')
p.button('down',5);p.tick(30,render=True,sound=False)
p.button('a',5);p.tick(120,render=True,sound=False)
assert 'request' in hits,hits
p.screen.image.save(ROOT/'work/clockreset_success.png')
p.memory[0]=0x0a;p.memory[0x4000]=0
assert p.memory[0xac80]==0x80
p.memory[0]=0
print('clock_reset_ui_flow_passed',sorted(set(hits)))
p.stop(save=False)
