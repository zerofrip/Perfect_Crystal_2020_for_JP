"""Port only binary-verified released-2020 battle fixes to the original JP ROM.

Source references help name routines, but all preimages and changes below are
checked against the actual supplied ROMs. No Japanese text is replaced.
"""
from hashlib import sha1


JP_SHA1 = '95127b901bbce2407daf43cce9f45d4c27ef635d'
UE_SHA1 = 'f2f52230b536214ef7c9924f483392993e226cfb'
PERFECT_SHA1 = 'dd00b737fbd18d2e8ae064097a36e8fd4b16855d'
BELLY_CAVE = 0x37F33
SPECIES_CAVE = BELLY_CAVE + 61
METAL_CAVE = SPECIES_CAVE + 18


def apply_battle_bugfixes(original, english_stock, perfect, output):
    """Mutate output and return exact (file offset, size, label) write ranges.

    english_stock/perfect are optional historical references; when supplied,
    the authored changes are cross-checked against the released 2020 ROM.
    """
    if english_stock is not None:
        assert sha1(english_stock).hexdigest() == UE_SHA1
    if perfect is not None:
        assert sha1(perfect).hexdigest() == PERFECT_SHA1
    assert sha1(original).hexdigest() == JP_SHA1
    assert len(output) == len(original) == 0x200000
    ranges = []

    def unique(data, pattern, expected):
        assert data.find(pattern) == expected
        assert data.find(pattern, expected + 1) < 0

    def write(offset, before, after, label):
        assert len(before) == len(after)
        assert original[offset:offset + len(before)] == before, label
        assert output[offset:offset + len(before)] == before, ('overlap', label)
        output[offset:offset + len(after)] = after
        ranges.append((offset, len(after), label))

    # Only one byte differs in each complete released multiplier routine.
    # Preserve all JP WRAM, far-call targets and evolution/flee-table pointers.
    # The relative byte offset inside each routine is authored from the
    # released change layout; the JP routines share the English instruction
    # structure (verified by the JP anchor preimages below).
    ball_changes = (
        ('moon_ball', 39, 0xECDD, 0xECD8, 0xEF52, 53, 0x0A, 0x08,
         'c5fa35d23d4f060021536709093e10cd2930'),
        ('love_ball', 68, 0xED12, 0xED0D, 0xEF87, 86, 0xC0, 0xC8,
         'fa35d24ffa36d2b9c0c5fa36d2eac8d0'),
        ('fast_ball', 21, 0xED68, 0xED63, 0xEFDD, 36, 0x0A, 0xF3,
         'fa35d24f21994516033e0fcd193023feff'),
    )
    for name, i, ue, pc, jp, size, before, after, anchor in ball_changes:
        unique(original, bytes.fromhex(anchor), jp)
        assert original[jp + i] == before, (name, 'JP preimage mismatch')
        if english_stock is not None and perfect is not None:
            delta = [j for j in range(size) if english_stock[ue+j] != perfect[pc+j]]
            assert delta == [i], (name, delta)
            assert (english_stock[ue+i], perfect[pc+i]) == (before, after)
        write(jp+i, bytes((before,)), bytes((after,)), name)

    belly_before = bytes.fromhex(
        'cdc861fa5bc6a7202c219a4c3e0fcf21d94c3e0fcf301ec5cd527ec1'
        '213a4c3e0fcfcd44393e05f5cdc861f13d20f8214853c3623acdc87ec39f73')
    unique(original, belly_before, 0x37C6B)
    if perfect is not None:
        # The actual relocated English routine, including the two added BC saves.
        released_belly = bytes.fromhex(
            '219f4c3e0fcf21de4c3e0fcf3029c5cdac61c1fa67c6a7201ec5cdb27dc1'
            '213f4c3e0fcfcd95393e05f5cdac61f13d20f821e457c3d53acd287ec3fd72')
        unique(perfect, released_belly, 0x37BC9)
    assert len(belly_before) == 59
    belly = bytearray(belly_before[9:23] + b'\xc5' + belly_before[:3] +
                      b'\xc1' + belly_before[3:9] + belly_before[23:])
    belly[13] = 0x29  # HP failure -> the new routine's .failed at +55
    belly[24] = 0x1E  # Attack-stage failure -> same .failed
    assert belly[:25] == bytes.fromhex(
        '219a4c3e0fcf21d94c3e0fcf3029c5cdc861c1fa5bc6a7201e')
    write(BELLY_CAVE, bytes(len(belly)), belly, 'belly_drum_checked_hp_routine')
    write(0x37C6B, belly_before[:3], bytes.fromhex('c3337f'), 'belly_drum_entry')

    # Released-2020 behavior is intentionally reproduced byte-for-byte. Its
    # cap compares the low byte even when high < 3; it is not a mathematically
    # perfect min(stat,999). Changing that would exceed this port's scope.
    species_tail = bytes.fromhex('cb25cb143e03bc38043ee7bdd026032ee7c9')
    assert len(species_tail) == 18
    unique(original, bytes.fromhex('e5cd037e7ee1bac0cb25cb14c9'), 0x353E9)
    if perfect is not None:
        unique(perfect, species_tail, 0x353F4)
    write(SPECIES_CAVE, bytes(18), species_tail, 'light_ball_thick_club_cap_routine')
    write(0x353F1, bytes.fromhex('cb25cb14c9'),
          bytes((0xC3, SPECIES_CAVE & 255, 0x7F, 0, 0)), 'species_item_cap_entry')
    metal_tail = bytes.fromhex('37cb193e03b838043ee7b9d006030ee7c9')
    assert len(metal_tail) == 17
    unique(original, bytes.fromhex('79cb3f814fd0cb3878a720010437cb19c9'), 0x352CB)
    if perfect is not None:
        unique(perfect, metal_tail, 0x352CE)
    write(METAL_CAVE, bytes(17), metal_tail, 'metal_powder_cap_routine')
    write(0x352D8, bytes.fromhex('37cb19c9'),
          bytes((0xC3, METAL_CAVE & 255, 0x7F, 0)), 'metal_powder_cap_entry')

    magikarp_before = bytes.fromhex(
        'fa35d2fe81204b113dd2018cd421727d3e3ecffa1bd2fe06201ccd5e2ffe0c3815'
        'fa1cd2fe5030b0cd5e2ffe323807fa1cd2fe4030a2fa7bdcfe092815fa7cdcfe06'
        '280ecd5e2ffe643807fa1bd2fe043886')
    unique(original, magikarp_before, 0x3E9D7)
    # English block has identical instruction sizes and branch displacements,
    # so the authored relative change list applies to the JP block directly.
    magikarp_changes = [(23, 6, 5), (37, 0x50, 3), (51, 0x40, 2),
                        (59, 0x28, 0x20), (66, 0x28, 0x20)]
    if english_stock is not None and perfect is not None:
        stock_block = english_stock[0x3E9C8:0x3EA1A]
        released_block = perfect[0x3E9C6:0x3EA18]
        changes = [(i, a, b) for i, (a,b) in enumerate(zip(stock_block, released_block)) if a != b]
        assert changes == magikarp_changes, changes
    for i, a, b in magikarp_changes:
        assert original[0x3E9D7+i] == a, ('magikarp JP preimage', i)
        write(0x3E9D7+i, bytes((a,)), bytes((b,)), 'magikarp_size_area_'+str(i))

    heal_before = bytes.fromhex('fa57c621d9d2013000cdca30af77ea45d22165c6cb86c9')
    unique(original, heal_before, 0x384EC)
    if perfect is not None and english_stock is not None:
        released_heal = bytes.fromhex('fa63c621a8d2013000cdfe30af77ea14d2216dc6cb862171c6cb86c9')
        unique(perfect, released_heal, 0x384E0)
        assert english_stock[0x384E0:0x384F7] == released_heal[:17]+released_heal[22:]
    # The main builder uses earlier original-zero bytes for expanded trainer
    # parties; reserve $0e:7800 beyond that output and require no overlap.
    heal_after = heal_before[:17] + bytes.fromhex('2161c6cb86') + heal_before[17:]
    write(0x3B800, bytes(len(heal_after)), heal_after, 'ai_heal_nightmare_routine')
    write(0x384EC, heal_before[:3], bytes.fromhex('c30078'), 'ai_heal_nightmare_entry')

    mean_before = bytes.fromhex('fa65c6cb472017fa5cc6e6c92010')
    unique(original, mean_before, 0x38E26)
    if english_stock is not None and perfect is not None:
        assert english_stock[0x38E08:0x38E16] == bytes.fromhex('fa71c6cb472017fa68c6e6c92010')
        assert perfect[0x38E0D:0x38E1B] == bytes.fromhex('fa6cc6cb472017fa68c6e6c92010')
    write(0x38E27, b'\x65', b'\x60', 'ai_mean_look_player_toxic')

    pp_before = bytes.fromhex(
        '3ea5ead7c6fa69c6a7212ac6200b2ab623b623b6e63fc01815cb37e60f471605af'
        '1528084e230528f8b118f5a7c0212e4bcd623a0e3ccd6804afc9')
    unique(original, pp_before, 0x3E795)
    if perfect is not None:
        released_pp = bytes.fromhex(
            '3ea5eae3c6fa75c6a72134c6200b2ab623b623b6e63fc01816cb37e60f471605af'
            '1528084e230528f8b118f5e63fc021844ccdd53a0e3ccd6804afc9')
        unique(perfect, released_pp, 0x3E783)
    assert pp_before[44] == 0xA7 and len(pp_before) == 59
    pp_after = bytearray(pp_before[:44]+bytes.fromhex('e63f')+pp_before[45:])
    pp_after[24] = 0x16  # no-PP path skips the one-byte longer .done mask
    write(0x3FF3D, bytes(len(pp_after)), pp_after, 'disabled_moves_pp_mask_routine')
    write(0x3E795, pp_before[:3], bytes.fromhex('c33d7f'), 'disabled_moves_pp_mask_entry')

    defense_before = bytes.fromhex('02030405066207080990ab0d0e0f101112907f8dff')
    unique(original, defense_before, 0x27864)
    defense_after = defense_before[:17]+defense_before[18:]
    if english_stock is not None and perfect is not None:
        unique(english_stock, defense_before, 0x2750B)
        assert perfect[0x2750B:0x2750B+len(defense_after)] == defense_after
    # Keep subsequent script pointers stable. The extra $ff follows endmove.
    write(0x27864, defense_before, defense_after+b'\xff', 'defense_down_hit_single_chance')

    # Released 2020 removes this premature RET NC in the length calculation's
    # comparison helper. NOP preserves all original JP routine addresses and
    # the Japanese millimetre display; the remaining release semantics match.
    length_before=bytes.fromhex('78bad8d079bbc9')
    length_after=bytes.fromhex('78bad879bbc9')
    unique(original,length_before,0xFBDF5)
    if english_stock is not None and perfect is not None:
        unique(english_stock,length_before,0xFBC9A)
        unique(perfect,length_after,0xFBC9A)
    write(0xFBDF8,b'\xd0',b'\x00','magikarp_length_low_byte_comparison')

    # Initial Perfect changes extend beyond the later named Bugfixes commit.
    # The released catch formula restores the status byte after testing the
    # sleep/freeze bits, so poison/burn/paralysis receive the +5 bonus.
    status_before=bytes.fromhex('47fa45d2e6270e0a2007a70e0520020e00788130023eff')
    unique(original,status_before,0xEC16)
    if english_stock is not None and perfect is not None:
        unique(english_stock,bytes.fromhex('47fa14d2e6270e0a2007a70e0520020e00788130023eff'),0xE960)
        status_released=bytes.fromhex('47fa14d2e6270e0a200afa14d2a70e0520020e00788130023eff')
        unique(perfect,status_released,0xE962)
    status_after=bytearray(status_before[:10]+bytes.fromhex('fa45d2')+status_before[10:])
    status_after[9]=0x0a
    status_after+=bytes.fromhex('c32d6c')
    write(0xFF50,bytes(len(status_after)),status_after,'catch_status_bonus_routine')
    write(0xEC16,status_before[:4],bytes.fromhex('c3507f00'),'catch_status_bonus_entry')

    # GetItemHeldEffect consumes B, while the far-call setup overwrites A.
    unique(original,bytes.fromhex('57d5fa23c63e0d21217ecf78fe46'),0xEC2D)
    if perfect is not None:
        unique(perfect,bytes.fromhex('57d5fa2dc6473e0d21817dcf78fe46'),0xE97C)
    held_after=bytes.fromhex('fa23c647c9')
    write(0xFF70,bytes(len(held_after)),held_after,'catch_held_item_argument_routine')
    write(0xEC2F,bytes.fromhex('fa23c6'),bytes.fromhex('cd707f'),'catch_held_item_argument_entry')

    # A transformed target retains its original species and saved original
    # DVs. Redirect the old branch over the forced-Ditto assignment; the
    # untransformed path still takes the original JP DV-backup instructions.
    transform_before=bytes.fromhex('2165c67ef5cbdecb5f200218073e84ea35d2180dcbde21e6c6fa3dd222fa3ed277')
    unique(original,transform_before,0xECBC)
    if english_stock is not None and perfect is not None:
        unique(english_stock,bytes.fromhex('2171c67ef5cbdecb5f200218073e84ea04d2180dcbde21f2c6fa0cd222fa0dd277'),0xEA06)
        unique(perfect,bytes.fromhex('2171c67ef5cbdecb5f200b21f2c6fa0cd222fa0dd277'),0xEA0C)
    write(0xECC6,b'\x02',b'\x16','captured_transform_species_dv_branch')

    # Reproduce the released branch polarity, including its boundary cases.
    # The main builder independently disables the later AI failure sampler.
    unique(original,bytes.fromhex('fa00c7e6f0280405200104f0e4a72823'),0x36305)
    if perfect is not None:
        unique(perfect,bytes.fromhex('fa0cc7e6f0280405280104cd2773'),0x362E9)
    write(0x3630D,b'\x20',b'\x28','stat_down_released_sharp_branch')
    return ranges
