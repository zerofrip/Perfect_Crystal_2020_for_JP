"""CPU-probe the local Hall decoration hook without running a full game save.

PyBoy calls the breakpoint callback just before the hook's final RET. Exit
there after checking the real event-flag WRAM, since the injected CPU context
does not represent a playable frame.
"""
from pc_env import workspace
from io import BytesIO
import os
from pathlib import Path
import sys
from pyboy import PyBoy

root = workspace()
rom = (root / "work/development_only_jp_partial.gbc").read_bytes()
emulator = PyBoy(BytesIO(rom), window="null", sound_emulated=False)
emulator.tick(600, render=False, sound=False)
trigger = 0x45 if "--nonhall" in sys.argv else 0x44

flag_base = 0xDA65  # actual Japanese home EventFlagAction at $002e41
granted = {flag for flag in range(0x2A4, 0x2D2)
           if flag not in {0x2B7, 0x2B9, 0x2BC, 0x2CD, 0x2CF}}
probed = granted | {0x44, 0x45, 0x2B7, 0x2B9, 0x2BC, 0x2CD, 0x2CF}
for flag in probed:
    address = flag_base + flag // 8
    emulator.memory[address] &= ~(1 << (flag % 8))

# The far-call trampoline uses hROMBank to restore the caller's bank.
emulator.memory[0x2000] = 0x25
emulator.memory[0xFF9D] = 0x25
emulator.memory[0xFFFF] = 0
emulator.memory[0xFF0F] = 0
registers = emulator.register_file
registers.SP = 0xCFFE
emulator.memory[0xCFFE] = 0x72
emulator.memory[0xCFFF] = 0x79
registers.PC = 0x7F92
registers.D = 0
registers.E = trigger
registers.B = 1


def check_before_return(pyboy):
    observed = {flag for flag in probed
                if pyboy.memory[flag_base + flag // 8] & (1 << (flag % 8))}
    expected = granted | {0x44} if trigger == 0x44 else {0x45}
    expected_sp = 0xCFFE if trigger == 0x44 else 0xD000
    good = observed == expected and pyboy.register_file.SP == expected_sp
    print("hall_hook_emulator_check", good, "trigger", f"{trigger:02x}",
          "granted", len(observed) - 1 if trigger == 0x44 else 0,
          "stack", f"{pyboy.register_file.SP:04x}", flush=True)
    os._exit(0 if good else 1)


stop_address = 0x7FCB if trigger == 0x44 else 0x7972
emulator.hook_register(0x25, stop_address, check_before_return, emulator)
emulator.tick(1, render=False, sound=False)
raise RuntimeError("Hall decoration hook did not reach its return instruction")
