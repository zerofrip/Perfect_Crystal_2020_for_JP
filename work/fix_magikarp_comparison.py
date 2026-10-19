"""Correct the released-2020 Magikarp comparison after the JP port is applied.

This is an explicitly requested correction beyond released-2020 parity.
All evidence is checked before mutation; only RET NZ replaces the RC1 NOP.
"""
from hashlib import sha1

JP_SHA1 = '95127b901bbce2407daf43cce9f45d4c27ef635d'
UE_SHA1 = 'f2f52230b536214ef7c9924f483392993e226cfb'
PERFECT_SHA1 = 'dd00b737fbd18d2e8ae064097a36e8fd4b16855d'
ENTRY = 0xFBDF5
PATCH = ENTRY + 3
ORIGINAL = bytes.fromhex('78bad8d079bbc9')
RC1 = bytes.fromhex('78bad80079bbc9')
CORRECT = bytes.fromhex('78bad8c079bbc9')


def apply_magikarp_comparison_fix(original, english_stock, perfect, output):
    """Return one (offset, size, label) range after validating RC1 preimages."""
    assert sha1(original).hexdigest() == JP_SHA1, 'wrong Japanese original'
    if english_stock is not None and perfect is not None:
        assert sha1(english_stock).hexdigest() == UE_SHA1, 'wrong English original'
        assert sha1(perfect).hexdigest() == PERFECT_SHA1, 'wrong released 2020 ROM'
    assert len(output) == len(original) == 0x200000, 'wrong output size'
    for rom, anchor, offset in ((original, ORIGINAL, ENTRY),):
        assert rom.count(anchor) == 1 and rom.find(anchor) == offset, 'comparison anchor mismatch'
    if english_stock is not None and perfect is not None:
        for rom, anchor, offset in (
            (english_stock, ORIGINAL, 0xFBC9A),
            (perfect, bytes.fromhex('78bad879bbc9'), 0xFBC9A),
        ):
            assert rom.count(anchor) == 1 and rom.find(anchor) == offset, 'comparison anchor mismatch'
    assert output[ENTRY:ENTRY + len(RC1)] == RC1, 'released-2020 JP comparison not applied or changed'

    # Actual JP caller: read DE from the table, CALL comparison, JR NC .next.
    # Carry means BC < DE; equal and greater must both advance the table.
    caller = bytes.fromhex('2a5f2a57cdf57d3031')
    assert original.count(caller) == 1 and original.find(caller) == 0xFBD9F
    assert output[0xFBD9F:0xFBDA8] == caller, 'comparison caller changed'

    # LD A,B / CP D / RET C / RET NZ / LD A,C / CP E / RET.
    # CP D resolves unequal high bytes. Only equal high bytes compare lows.
    # BC, DE, HL are preserved; C = (BC < DE), Z = (BC == DE).
    output[PATCH] = 0xC0
    return [(PATCH, 1, 'correct_unsigned_16bit_magikarp_length_comparison')]
