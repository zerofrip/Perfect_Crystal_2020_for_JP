"""Headless boot comparison; all ROM and save bytes remain local."""
from pc_env import workspace
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from pyboy import PyBoy

root = workspace()
for name, path in (
    ('stock_jp', root / 'Pocket Monsters - Crystal Version (Japan).gbc'),
    ('partial_jp', root / 'work/development_only_jp_partial.gbc'),
):
    rom = BytesIO(path.read_bytes())
    emulator = PyBoy(rom, window='null', sound_emulated=False)
    for count in (120, 480):
        active = emulator.tick(count, render=True, sound=False)
        frame_hash = sha256(bytes(emulator.screen.raw_buffer)).hexdigest()
        print(name, 'frames', count, 'active', active, 'screen_sha256', frame_hash)
    if name == 'partial_jp':
        emulator.screen.image.save(root / 'work/partial_jp_title_smoke.png')
    emulator.stop(save=False)
