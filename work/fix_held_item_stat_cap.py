"""Apply the requested mathematical held-stat caps after the RC2 feature set.

Metal Powder originally runs on packed 8-bit attack/defense after truncation.
Move that adjustment before truncation so its 999 bound applies to the actual
16-bit defense. Keep species/item/Transform selection and Truncate unchanged.
"""
from hashlib import sha1

JP_SHA1 = '95127b901bbce2407daf43cce9f45d4c27ef635d'
UE_SHA1 = 'f2f52230b536214ef7c9924f483392993e226cfb'
PERFECT_SHA1 = 'dd00b737fbd18d2e8ae064097a36e8fd4b16855d'
SPECIES_CAVE = 0x37F70
METAL_CAVE = 0x37F82
WRAPPER = 0x37FCA
SPECIES_2020 = bytes.fromhex('cb25cb143e03bc38043ee7bdd026032ee7c9')
METAL_2020 = bytes.fromhex('37cb193e03b838043ee7b9d006030ee7c9')
# Compare high bytes first. RET NZ returns only when high < 3 because JR C
# already handled high > 3. Only equal high bytes require low-byte comparison.
SPECIES_FIXED = bytes.fromhex('cb25cb143e03bc3805c03ee7bdd021e703c9')
METAL_FIXED = bytes.fromhex('3e03b83805c03ee7b9d001e703c9') + bytes(3)
METAL_ARITH_ORIGINAL = bytes.fromhex('79cb3f814fd0cb3878a720010437cb19c9')
METAL_ARITH_2020 = METAL_ARITH_ORIGINAL[:13] + bytes.fromhex('c3827f00')
# HL = floor(BC/2); HL += BC; BC = HL; JP pure BC cap.
# Valid screened input is at most 1998, so the sum fits in 16 bits.
METAL_ARITH_FIXED = bytes.fromhex('6069cb3ccb1d09444dc3827f') + bytes(5)
# Preserve selected attack in HL across real party/item lookup, then run the
# unchanged truncation. D (move power) and E are untouched by the new math.
WRAPPER_CODE = bytes.fromhex('e5cdb152e1c34d53')


def apply_held_item_stat_cap_fix(original, english_stock, perfect, output):
    """Validate all preimages first, then mutate output and return write ranges."""
    assert sha1(original).hexdigest() == JP_SHA1, 'unexpected source ROM'
    if english_stock is not None and perfect is not None:
        for data, digest in ((english_stock, UE_SHA1), (perfect, PERFECT_SHA1)):
            assert sha1(data).hexdigest() == digest, 'unexpected source ROM'
    assert len(output) == len(original) == 0x200000

    def unique(data, expected, offset, label):
        assert data.find(expected) == offset and data.find(expected, offset+1) < 0, label

    if perfect is not None:
        unique(perfect, SPECIES_2020, 0x353F4, 'released species cap anchor')
        unique(perfect, METAL_2020, 0x352CE, 'released Metal cap anchor')
    unique(output, SPECIES_2020, SPECIES_CAVE, 'ported species cap anchor')
    unique(output, METAL_2020, METAL_CAVE, 'ported Metal cap anchor')
    unique(original, bytes.fromhex('e5cd037e7ee1bac0cb25cb14c9'), 0x353E9, 'JP species entry')
    unique(original, METAL_ARITH_ORIGINAL, 0x352CB, 'JP Metal arithmetic')
    assert original[0x353F1:0x353F6] == bytes.fromhex('cb25cb14c9')
    assert output[0x353F1:0x353F6] == bytes.fromhex('c3707f0000')
    gate = bytes.fromhex('3e00cd0c39f0e4a77e2003fa35d2fe84c0c5cd127e7efe23c1c0')
    unique(original, gate, 0x352B1, 'original Metal species/item gate')
    unique(output, gate, 0x352B1, 'ported Metal species/item gate')
    # Only the two normal-damage calls move. Confusion's third Truncate call
    # and the shared Truncate body keep their original behavior.
    assert original[0x34000:0x38000].count(bytes.fromhex('cdb152')) == 2
    assert output[0x34000:0x38000].count(bytes.fromhex('cdb152')) == 2
    assert original[0x3534D:0x35378] == output[0x3534D:0x35378]
    assert original[0x3560A:0x3560D] == output[0x3560A:0x3560D] == bytes.fromhex('cd4d53')
    edits = [
        (SPECIES_CAVE, bytes(18), SPECIES_2020, SPECIES_FIXED, 'correct_species_999_cap'),
        (METAL_CAVE, bytes(17), METAL_2020, METAL_FIXED, 'correct_metal_16bit_999_cap'),
        (0x352CB, METAL_ARITH_ORIGINAL, METAL_ARITH_2020, METAL_ARITH_FIXED,
         'metal_powder_16bit_multiply'),
        (WRAPPER, bytes(8), bytes(8), WRAPPER_CODE, 'metal_before_truncate_wrapper'),
    ]
    for start, level in ((0x3533F, '2fc6'), (0x35453, '44d2')):
        anchor = bytes.fromhex('cd4d53fa'+level+'5fcdb1523e01a7c9')
        unique(original, anchor, start, 'original normal damage callsite')
        unique(output, anchor, start, 'ported normal damage callsite')
        edits.extend([
            (start, anchor[:3], anchor[:3], bytes.fromhex('cdca7f'), 'metal_before_truncate_call'),
            (start+7, bytes.fromhex('cdb152'), bytes.fromhex('cdb152'), bytes(3),
             'remove_metal_after_truncate_call'),
        ])
    occupied = set()
    for offset, old, ported, after, label in edits:
        assert len(old) == len(ported) == len(after), label
        unique_range = set(range(offset, offset+len(after)))
        assert not occupied.intersection(unique_range), ('overlapping edits', label)
        occupied.update(unique_range)
        assert original[offset:offset+len(old)] == old, ('original preimage', label)
        assert output[offset:offset+len(ported)] == ported, ('RC2 preimage', label)
    for offset, _, _, after, _ in edits:
        output[offset:offset+len(after)] = after
    return [(offset, len(after), label) for offset, _, _, after, label in edits]
