"""Render actual received trade-name buffers with the integrated JP text engine.

Only the in-memory emulator fixture has driver code and a RAM-text template.
The ROM's nickname helper and Japanese text engine run without alteration.
"""
from hashlib import sha256
from io import BytesIO
import json
import os
from pyboy import PyBoy
from map_layout import ROOT

original=(ROOT/'work/development_only_jp_partial.gbc').read_bytes()
assert sha256(original).hexdigest()=='bdb8b08177dc6e5a549c5d3ed2499a9835ae7c7c01ad0acafda659072335805e'
rom=bytearray(original)
drivers=[(0xfffa0,bytes.fromhex('3e03ea57cf218a4e11f5c6cd807fc9')),
         (0xfffb0,bytes.fromhex('3e05ea57cf21aa4e11fbc6cd807fc9')),
         (0x198000,bytes.fromhex('005001f5c6004f5001fbc60057')),
         (0x97fd0,bytes.fromhex('fb3e3f21a07fcf3e3f21b07fcf3e66210040cd7c310e04cd6804c30001'))]
for offset,driver in drivers:
    assert rom[offset:offset+len(driver)]==bytes(len(driver))
    rom[offset:offset+len(driver)]=driver
p=PyBoy(BytesIO(rom),window='null',sound_emulated=False)
p.set_emulation_speed(0)
with (ROOT/'work/cave_test_state.bin').open('rb') as stream:p.load_state(stream)
p.memory[0xcffe]=0;p.memory[0xcfff]=1
p.register_file.SP=0xcffe
p.memory[0x2000]=p.memory[0xff9d]=0x25
p.register_file.PC=0x7fd0


def finish(_):
    dodrio=bytes(p.memory[0xc6f5:0xc6fb])
    aero=bytes(p.memory[0xc6fb:0xc700])
    assert dodrio==bytes.fromhex('13e313d88450')
    assert aero==bytes.fromhex('4292a55050')
    p.screen.image.save(ROOT/'work/remaining_play_trade_names.png')
    evidence={'rom_sha256':sha256(original).hexdigest(),'dodrio_buffer':dodrio.hex(),
              'aerodactyl_buffer':aero.hex(),'nickname_copy':'actual bank 3f helper and original CopyBytes',
              'render':'actual FarPrintText $317c and Japanese TX_RAM command',
              'fixture':'in-memory driver only; no real trade animation'}
    (ROOT/'work/remaining_play_names_evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2),flush=True)
    os._exit(0)


p.hook_register(0,0x100,finish,None)
for _ in range(300):p.tick(1,render=True,sound=False)
p.screen.image.save(ROOT/'work/remaining_play_names_timeout.png')
raise RuntimeError(('trade-name render timed out',hex(p.register_file.PC)))
