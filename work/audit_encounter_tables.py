"""Compare complete encounter records in the actual integrated JP artifact.

RC4 intentionally diverges from the 2020 UE patch for four starter encounter
records and only within specific 2-byte slot spans.  All other bytes in those
records (map IDs, encounter rates, unchanged time periods and unchanged slots)
remain identical to the 2020 release, and all water tables are unchanged.
"""
from map_layout import ROOT
from apply_rc4_corrections import (
    JOHTO_GRASS_START, RECORD_WIDTH, _UNION_CAVE_B1F, _WHIRL_ISLAND_LUGIA,
    _DARK_CAVE_VIOLET, _ROUTE_32, SLOT_WEIGHTS,
)

jp = (ROOT / 'work/development_only_jp_partial.gbc').read_bytes()
pc = (ROOT / 'work/perfect_crystal_ue_patched.gbc').read_bytes()

# Water tables and the Kanto grass extension are unchanged by RC4.
for name, a, b, count, width in (
    ('johto_water', 0x2B140, 0x2B11D, 38, 9),
    ('kanto_grass', 0x2B297, 0x2B274, 33, 47),
    ('kanto_water', 0x2BD04, 0x2B884, 26, 9),
):
    size = count * width + 1
    assert jp[a:a + size] == pc[b:b + size], name
    assert jp[a + size - 1] == 0xff
    print(name, 'records', count, 'match_released_2020', True)

# Johto grass: compare record by record, allowing only the declared RC4 slots.
rc4_records = {
    _UNION_CAVE_B1F[0]: {
        'map_id': _UNION_CAVE_B1F[1],
        'allowed': {(0, 3), (0, 4), (1, 3), (1, 4)},
    },
    _WHIRL_ISLAND_LUGIA[0]: {
        'map_id': _WHIRL_ISLAND_LUGIA[1],
        'allowed': {(2, 3), (2, 5), (2, 6)},
    },
    _DARK_CAVE_VIOLET[0]: {
        'map_id': _DARK_CAVE_VIOLET[1],
        'allowed': {(2, 3), (2, 6)},
    },
    _ROUTE_32[0]: {
        'map_id': _ROUTE_32[1],
        'allowed': {(1, 2), (1, 5)},
    },
}

for index in range(61):
    offset = JOHTO_GRASS_START + index * RECORD_WIDTH
    ue_offset = 0x2A5E9 + index * RECORD_WIDTH
    if offset not in rc4_records:
        assert jp[offset:offset + RECORD_WIDTH] == pc[ue_offset:ue_offset + RECORD_WIDTH], (
            f'johto_grass record {index} at {offset:06x} differs'
        )
        continue
    info = rc4_records[offset]
    assert jp[offset:offset + 2] == info['map_id'], f'map ID mismatch at {offset:06x}'
    # Header and encounter rates must match exactly.
    assert jp[offset:offset + 5] == pc[ue_offset:ue_offset + 5], (
        f'johto_grass header at {offset:06x} differs'
    )
    # Within each time period, unchanged slots must match exactly.
    for period in range(3):
        base = offset + 5 + period * 14
        ue_base = ue_offset + 5 + period * 14
        for slot in range(7):
            if (period, slot) in info['allowed']:
                continue
            span = base + slot * 2
            ue_span = ue_base + slot * 2
            assert jp[span:span + 2] == pc[ue_span:ue_span + 2], (
                f'johto_grass record {index} period {period} slot {slot} at {span:06x} differs'
            )

print('johto_grass', 'records', 61, 'unchanged_records', 61 - len(rc4_records))

# Verify the exact RC4 probabilities in the changed records.
def _rate_at(offset, period, species, level):
    base = offset + 5 + period * 14
    total = 0
    for slot, weight in enumerate(SLOT_WEIGHTS):
        if jp[base + slot * 2] == level and jp[base + slot * 2 + 1] == species:
            total += weight
    return total

assert _rate_at(_UNION_CAVE_B1F[0], 0, 7, 6) == 10
assert _rate_at(_UNION_CAVE_B1F[0], 1, 7, 6) == 10
assert _rate_at(_WHIRL_ISLAND_LUGIA[0], 2, 140, 27) == 10
assert _rate_at(_DARK_CAVE_VIOLET[0], 2, 155, 2) == 30
assert _rate_at(_DARK_CAVE_VIOLET[0], 2, 155, 4) == 10
assert _rate_at(_ROUTE_32[0], 1, 158, 7) == 20
assert _rate_at(_ROUTE_32[0], 1, 69, 7) == 4
print('rc4_starter_encounter_probabilities', 'verified', 7)
