"""CPU-probe the local Hall decoration hook without running a full game save.

PyBoy calls the breakpoint callback just before the hook's final RET. Exit
there after checking the real event-flag WRAM, since the injected CPU context
does not represent a playable frame.

Usage:
    python3 work/test_hall_hook_emulator.py [hall|nonhall|repeat|--nonhall]

Modes:
    hall    - trigger with EVENT_BEAT_ELITE_FOUR (0x44), expect 41 actual item
              flags plus the separate poster-display flag (42 Hall flags total).
    nonhall - trigger with EVENT_BEAT_CHAMPION (0x45), expect no Hall flags.
    repeat  - clear all flags, preset the 42 Hall flags + trigger, execute
              again and verify idempotence and preservation of the preset.
"""
from pc_env import workspace
from io import BytesIO
import os
from pathlib import Path
import sys

root = workspace()
rom = (root / "work/development_only_jp_partial.gbc").read_bytes()

raw_mode = sys.argv[1] if len(sys.argv) > 1 else "hall"
mode = "nonhall" if raw_mode == "--nonhall" else raw_mode
if mode == "nonhall":
    trigger = 0x45
elif mode in ("hall", "repeat"):
    trigger = 0x44
else:
    raise SystemExit(f"unknown mode {mode!r}; use hall, nonhall or repeat")

flag_base = 0xDA65  # actual Japanese home EventFlagAction at $002e41

# Red-exclusive decoration flags are never granted by the Hall hook.
red_only = {0x2B9, 0x2BC, 0x2CD, 0x2CF}
# Hall hook grants every decoration flag in 0x2A4..0x2D1 except Red's.
hall_flags = set(range(0x2A4, 0x2D2)) - red_only
# 0x2CC is the poster-display flag; the other 41 are actual item flags.
poster_flag = 0x2CC
item_flags = hall_flags - {poster_flag}
# Probe the full decoration range plus the two possible trigger flags.
probed = set(range(0x2A4, 0x2D2)) | {0x44, 0x45}


def run_check():
    from pyboy import PyBoy
    emulator = PyBoy(BytesIO(rom), window="null", sound_emulated=False)
    emulator.tick(600, render=False, sound=False)

    # Deterministic initial state: clear every probed flag first.
    for flag in probed:
        address = flag_base + flag // 8
        emulator.memory[address] &= ~(1 << (flag % 8))

    if mode == "repeat":
        for flag in hall_flags | {0x44, 0x45}:
            address = flag_base + flag // 8
            emulator.memory[address] |= 1 << (flag % 8)

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

    result = {"passed": False}

    def check_before_return(pyboy):
        observed = {flag for flag in probed
                    if pyboy.memory[flag_base + flag // 8] & (1 << (flag % 8))}
        if trigger == 0x44:
            expected = hall_flags | {0x44}
            if mode == "repeat":
                expected |= {0x45}
            expected_sp = 0xCFFE
        else:
            expected = {0x45}
            expected_sp = 0xD000
        good = observed == expected and pyboy.register_file.SP == expected_sp
        result["passed"] = good
        result["observed"] = sorted(observed)
        result["expected"] = sorted(expected)
        result["item_flag_count"] = len(item_flags)
        result["poster_flag_count"] = 1
        result["hall_flag_count"] = len(hall_flags)
        result["stack"] = pyboy.register_file.SP
        result["trigger"] = trigger
        result["mode"] = mode
        print("hall_hook_emulator_check", good, "mode", mode, "trigger", f"{trigger:02x}",
              "item_flags", len(item_flags), "poster_flags", 1,
              "hall_flags", len(hall_flags), "stack", f"{result['stack']:04x}", flush=True)
        os._exit(0 if good else 1)

    stop_address = 0x7FCB if trigger == 0x44 else 0x7972
    emulator.hook_register(0x25, stop_address, check_before_return, emulator)
    emulator.tick(1, render=False, sound=False)
    raise RuntimeError("Hall decoration hook did not reach its return instruction")


if __name__ == "__main__":
    run_check()
