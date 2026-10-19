"""RC5: restore Japanese-original graphics on top of the exact RC4 snapshot.

RC1..RC4 carried the released-2020 replacements for swimmer_f and Jynx's front
picture (plus its third animation frame, the extended picture-bank table and
the bank-$64 assets).  RC5 reverts exactly those bytes to the Japanese
original, leaving every other RC4 byte intact.  The historical
``apply_restored_sprites`` function is reused unchanged to compute the same
ranges it wrote in RC1..RC4; this module only verifies that the current output
still holds those probe bytes and then puts the Japanese originals back.

The restoration is staged on a candidate copy: a failed guard never leaves a
partial mutation.
"""
from hashlib import sha1


def stage_restored_ranges(candidate, original, probe, ranges):
    """Return (staged, restored) restoring `original` bytes in `ranges`.

    Every range must currently hold the historical restoration probe bytes.
    `candidate` is never mutated; the restored result is returned separately.
    """
    staged = bytearray(candidate)
    restored = []
    for start, size, label in ranges:
        assert size > 0 and start >= 0 and start + size <= len(staged), (
            'invalid range', label)
        assert candidate[start:start + size] == probe[start:start + size], (
            'output bytes differ from the historical sprite probe', label)
        staged[start:start + size] = original[start:start + size]
        restored.append((start, size, label))
    return staged, restored


def apply_japanese_original_sprites(original, english_stock, perfect, output):
    """Restore the Japanese-original graphics and return the reverted ranges.

    Arguments match the other apply_* helpers for drop-in use.  Only `output`
    is modified, and only after every guard passes.
    """
    assert sha1(original).hexdigest() == '95127b901bbce2407daf43cce9f45d4c27ef635d'
    assert sha1(english_stock).hexdigest() == 'f2f52230b536214ef7c9924f483392993e226cfb'
    assert sha1(perfect).hexdigest() == 'dd00b737fbd18d2e8ae064097a36e8fd4b16855d'
    assert len(output) == len(original) == 0x200000

    # Import lazily so source-only audits can import this module without the
    # private pokemontools tree; the historical function itself stays unchanged.
    from port_restored_sprites import apply_restored_sprites

    # Historical sprite-only probe: the bytes RC1..RC4 held in these ranges.
    probe = bytearray(original)
    probe_ranges = apply_restored_sprites(original, english_stock, perfect, probe)

    staged, restored = stage_restored_ranges(bytearray(output), original,
                                             probe, probe_ranges)

    # No out-of-range byte may move: outside the restored ranges the RC4
    # output is preserved bit-for-bit.
    changed = [i for i, (a, b) in enumerate(zip(output, staged)) if a != b]
    assert all(any(start <= i < start + size for start, size, _ in restored)
               for i in changed), 'RC5 moved bytes outside the restored ranges'
    output[:] = staged
    return restored
