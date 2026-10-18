"""Local emulator-only screenshot of Japanese text through the actual engine."""
from io import BytesIO
import os
import sys
from pyboy import PyBoy
from map_layout import ROOT,file_offset,word
from port_gym_rematches import apply_gym_rematches
from port_dialogue_updates import apply_dialogue_updates
from verify_gym_rematches import inputs

original,en,perfect=inputs()
rom=bytearray(original)
apply_gym_rematches(original,en,perfect,rom)
apply_dialogue_updates(original,en,perfect,rom)
entry=file_offset(0x62,word(rom,0x61c0a+2))
question=word(rom,entry+6)
# Local harness only: EI ensures that abandoning a frame-boundary interrupt
# context cannot strand text rendering's DelayFrame calls with IME disabled.
harness=(bytes.fromhex('fb3e6221')+question.to_bytes(2,'little')+
         bytes.fromhex('cd7c310e04cd6804c30001'))
assert rom[0x97fd0:0x97fd0+len(harness)]==bytes(len(harness))
rom[0x97fd0:0x97fd0+len(harness)]=harness
emulator=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
emulator.set_emulation_speed(0)
emulator.tick(600,render=True,sound=False)
for _ in range(4):
    emulator.button_press('start')
    emulator.tick(20,render=True,sound=False)
    emulator.button_release('start')
    emulator.tick(120,render=True,sound=False)
emulator.screen.image.save(str(ROOT/'work/dialogue_probe_menu.png'))
if len(sys.argv)==1:
    print('saved menu screenshot')
    emulator.stop(save=False)
    raise SystemExit

# Display the first rematch invitation after the normal menu loads JP font.
emulator.memory[0xcffe]=0
emulator.memory[0xcfff]=1
emulator.register_file.SP=0xcffe
emulator.memory[0x2000]=emulator.memory[0xff9d]=0x25
emulator.register_file.PC=0x7fd0


def done(pyboy):
    pyboy.screen.image.save(str(ROOT/'work/dialogue_gym_falkner_actual.png'))
    print('rendered original JP text engine rematch invitation',flush=True)
    os._exit(0)


emulator.hook_register(0,0x100,done,emulator)
for frame in range(240):
    emulator.tick(1,render=True,sound=False)
emulator.screen.image.save(str(ROOT/'work/dialogue_gym_falkner_actual.png'))
print('render probe timed out at',hex(emulator.register_file.PC))
emulator.stop(save=False)
