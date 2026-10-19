"""Correct Moon Ball beyond the released 2020 behavior, as explicitly requested.

Apply after the original 2020 port. All ROMs stay local. This module verifies
both original and 2020 preimages before redirecting the existing JP entry.
"""
from hashlib import sha1

JP_SHA1 = '95127b901bbce2407daf43cce9f45d4c27ef635d'
UE_SHA1 = 'f2f52230b536214ef7c9924f483392993e226cfb'
PERFECT_SHA1 = 'dd00b737fbd18d2e8ae064097a36e8fd4b16855d'
ENTRY = 0xEF52
CAVE = 0xFF80
JP_EVOS = 0x42753
UE_EVOS = 0x425B1
TARGETS = (30, 33, 35, 39, 61, 64, 93)
JP_BEFORE = bytes.fromhex(
    'c5fa35d23d4f060021536709093e10cd2930c1c53e10cd1930fe02c1c0'
    '232323c53e10cd1930fe0ac1c0cb203804cb20300206ffc9')
UE_BEFORE = bytes.fromhex(
    'c5fa04d23d4f060021b16509093e10cd5d30c1c53e10cd4d30fe02c1c0'
    '232323c53e10cd4d30fe0ac1c0cb203804cb20300206ffc9')
JP_2020 = JP_BEFORE[:39] + b'\x08' + JP_BEFORE[40:]
UE_2020 = UE_BEFORE[:39] + b'\x08' + UE_BEFORE[40:]


def evolution_records(rom, table):
    """Read the bounded, variable-length evolution records from actual ROM."""
    all_records = []
    for species in range(251):
        pointer = int.from_bytes(rom[table+2*species:table+2*species+2], 'little')
        assert 0x4000 <= pointer < 0x8000, ('evolution pointer', species+1)
        offset = 0x40000 + pointer - 0x4000
        records = []
        for _ in range(16):
            method = rom[offset]
            if method == 0:
                break
            assert method in (1, 2, 3, 4, 5), ('evolution method', species+1)
            size = 4 if method == 5 else 3
            assert offset+size < 0x44000
            records.append(bytes(rom[offset:offset+size]))
            offset += size
        else:
            raise AssertionError(('unterminated evolution list', species+1))
        all_records.append(records)
    return all_records


def moon_targets(rom, table=JP_EVOS):
    return tuple(i+1 for i, records in enumerate(evolution_records(rom, table))
                 if any(record[:2] == b'\x02\x08' for record in records))


def corrected_routine():
    """Assemble the local loop; keep C and DE unchanged, return catch rate in B."""
    code = bytearray()
    labels = {}
    branches = []

    def emit(hexbytes):
        code.extend(bytes.fromhex(hexbytes))

    def mark(name):
        labels[name] = len(code)

    def jr(opcode, label):
        code.extend((opcode, 0))
        branches.append((len(code)-1, label))

    # PUSH BC; species -> pointer table; GetFarHalfword from bank $10.
    # Leave the saved original B/C on the stack until target determination.
    emit('c5fa35d23d4f060021536709093e10cd2930')
    mark('record')
    emit('3e10cd1930a7')          # Read method with the original GetFarByte.
    jr(0x28, 'no_match')         # Method zero terminates evolutions.
    emit('fe02')
    jr(0x28, 'item')
    emit('fe05')
    jr(0x20, 'skip_three')       # Methods 1..4: three bytes; method 5: four.
    emit('23')
    mark('skip_three')
    emit('232323')
    jr(0x18, 'record')
    mark('item')
    emit('233e10cd1930fe08')     # Item is the NEXT byte, not byte +3.
    jr(0x28, 'match')
    emit('2323')                # Skip destination and move to the next method.
    jr(0x18, 'record')
    mark('no_match')
    emit('c1c9')
    mark('match')
    emit('c1cb20')              # Restore original rate/C, then saturating x4.
    jr(0x38, 'saturate')
    emit('cb20d0')
    mark('saturate')
    emit('06ffc9')
    for offset, label in branches:
        distance = labels[label] - (offset+1)
        assert -128 <= distance <= 127
        code[offset] = distance & 255
    assert CAVE+len(code) <= 0x10000
    return bytes(code)


def apply_moon_ball_fix(original, english_stock, perfect, output):
    """Mutate a previously ported JP ROM; reject ambiguity/conflicts atomically."""
    assert sha1(original).hexdigest() == JP_SHA1, 'unexpected source ROM'
    if english_stock is not None and perfect is not None:
        for rom, digest in ((english_stock, UE_SHA1), (perfect, PERFECT_SHA1)):
            assert sha1(rom).hexdigest() == digest, 'unexpected source ROM'
    assert len(output) == len(original) == 0x200000
    for rom, pattern, offset in ((original, JP_BEFORE, ENTRY),
                                 (output, JP_2020, ENTRY)):
        assert rom.find(pattern) == offset and rom.find(pattern, offset+1) < 0, \
            ('Moon Ball preimage missing or ambiguous', hex(offset))
    if english_stock is not None and perfect is not None:
        for rom, pattern, offset in ((english_stock, UE_BEFORE, 0xECDD),
                                     (perfect, UE_2020, 0xECD8)):
            assert rom.find(pattern) == offset and rom.find(pattern, offset+1) < 0, \
                ('Moon Ball preimage missing or ambiguous', hex(offset))
    readers = bytes.fromhex('e08bf09df5f08bd77ee08bf1d7f08bc9e08bf09df5f08bd72a666ff1d7c9')
    assert original[0x3019:0x3037] == output[0x3019:0x3037] == readers
    pointer_anchor = bytes.fromhex('496964698369a169ba69d569f1690c6a')
    assert original.find(pointer_anchor) == JP_EVOS
    assert original.find(pointer_anchor, JP_EVOS+1) < 0
    assert output[JP_EVOS:JP_EVOS+502] == original[JP_EVOS:JP_EVOS+502]
    if english_stock is not None and perfect is not None:
        assert evolution_records(original, JP_EVOS) == evolution_records(english_stock, UE_EVOS)
        assert evolution_records(output, JP_EVOS) == evolution_records(perfect, UE_EVOS)
    assert moon_targets(output) == TARGETS
    routine = corrected_routine()
    assert original[CAVE:CAVE+len(routine)] == bytes(len(routine)), 'original cave occupied'
    assert output[CAVE:CAVE+len(routine)] == bytes(len(routine)), 'output cave occupied'
    # Mutate only after every input, existing port, and allocated range passed.
    output[CAVE:CAVE+len(routine)] = routine
    output[ENTRY:ENTRY+3] = bytes.fromhex('c3807f')
    return [(CAVE, len(routine), 'moon_ball_complete_evolution_scan'),
            (ENTRY, 3, 'moon_ball_corrected_entry')]
