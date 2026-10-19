"""Authored hall-decoration hook, built from work/hall_decorations_hook.asm.

The hook mirrors the released-2020 Hall of Fame script: after the original
EVENT_BEAT_ELITE_FOUR action runs, it grants the remaining decoration flags
($02a4..$02d1) except the five flags awarded elsewhere (0x2b7/0x2b9/0x2bc/
0x2cd/0x2cf).  It is called at $25:796f in place of the original direct call
$2e41; .normal preserves registers and flags by jumping straight back.

Instructions mirror the authored RGBDS source one for one; JR displacements
are fixed up after emission so the byte layout stays identical to the
assembled hook.
"""

CAVE_OFFSET = 0x97F92
HOOK_SIZE = 0x3D
ORIGINAL_CALL = 0x2e41
START_FLAG = 0x02a4
END_FLAG = 0x02d2
SKIPPED_FLAGS = (0x2b7, 0x2b9, 0x2bc, 0x2cd, 0x2cf)


def hall_hook_code():
    data = bytearray()
    labels = {}
    branches = []  # (displacement position, target label)

    def emit(hexbytes):
        data.extend(bytes.fromhex(hexbytes))

    def label(name):
        labels[name] = len(data)

    def jump(opcode, name):
        data.append(opcode)
        data.append(0)  # JR displacement placeholder
        branches.append((len(data) - 1, name))

    def call_original():
        # call $2e41 -- the original Japanese SetEventFlag routine
        emit('cd')
        data.extend(ORIGINAL_CALL.to_bytes(2, 'little'))

    # ld a,d / and a / jr nz,.normal  -- high byte of the event id must be 0
    emit('7a a7')
    jump(0x20, 'normal')
    # ld a,e / cp EVENT_BEAT_ELITE_FOUR / jr nz,.normal
    emit('7b fe 44')
    jump(0x20, 'normal')
    # original action first, preserving its registers/flags on the stack
    call_original()
    emit('f5 c5 d5 e5')          # push af, bc, de, hl
    # ld de, START_FLAG
    emit('11')
    data.extend(START_FLAG.to_bytes(2, 'little'))
    label('loop')
    # ld a,e once, then the five skipped flags jump straight to .next
    emit('7b')
    for flag in SKIPPED_FLAGS:
        emit('fe')
        data.append(flag & 0xff)
        jump(0x28, 'next')
    # push de / ld b,1 / SetEventFlag / pop de
    emit('d5 06 01')
    call_original()
    emit('d1')
    label('next')
    # inc de / ld a,e / cp END_FLAG / jr nz,.loop
    emit('13 7b fe')
    data.append(END_FLAG & 0xff)
    jump(0x20, 'loop')
    # restore and return to the script engine
    emit('e1 d1 c1 f1 c9')
    label('normal')
    # jp $2e41 -- .normal jumps back to the original routine
    emit('c3')
    data.extend(ORIGINAL_CALL.to_bytes(2, 'little'))

    for position, name in branches:
        distance = labels[name] - (position + 1)
        assert -128 <= distance <= 127, (name, distance)
        data[position] = distance & 0xff
    assert len(data) == HOOK_SIZE
    assert data[:4] == bytes.fromhex('7aa72036')
    assert data[-3:] == bytes.fromhex('c3412e')
    return bytes(data)
