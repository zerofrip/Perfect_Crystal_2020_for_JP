"""RC4 corrections layered after the exact RC3 snapshot.

These are self-contained byte patches on the integrated Japanese ROM.  All
guards run against a candidate copy; only after every assertion succeeds is
the result copied back to `output`, so a failed guard never leaves a partial
mutation.
"""
from trainer_party_layout import trainer_groups

# Japanese output encounter table location and record layout.
JOHTO_GRASS_START = 0x2A60C
RECORD_WIDTH = 47
HEADER = 5
SLOTS_PER_PERIOD = 7
PERIOD_WIDTH = SLOTS_PER_PERIOD * 2

# Supervisor-verified target record offsets and map IDs in the Japanese output ROM.
_UNION_CAVE_B1F = (0x2A8FC, bytes((3, 38)))
_WHIRL_ISLAND_LUGIA = (0x2ACD7, bytes((3, 73)))
_DARK_CAVE_VIOLET = (0x2ADC2, bytes((3, 78)))
_ROUTE_31 = (0x2AE7E, bytes((26, 2)))
_ROUTE_32 = (0x2AEAD, bytes((10, 1)))

# Hall decoration hook installed by build_partial_jp_patch.py.
HALL_HOOK_START = 0x97F92
HALL_HOOK_SIZE = 0x3D

# Slot weights for Johto grass; used for synthetic probability assertions.
SLOT_WEIGHTS = (30, 30, 20, 10, 5, 4, 1)


def _period_offset(record_start, period):
    return record_start + HEADER + period * PERIOD_WIDTH


def _read_slots(candidate, record_start, period):
    base = _period_offset(record_start, period)
    return list(candidate[base:base + PERIOD_WIDTH])


def _write_slots(candidate, record_start, period, slots):
    base = _period_offset(record_start, period)
    candidate[base:base + PERIOD_WIDTH] = bytes(slots)


def _slot_span(record_start, period, slot, label="encounter_slot"):
    start = _period_offset(record_start, period) + slot * 2
    return (start, 2, label)


def _validate_unique_map_id(candidate, record_start, map_id):
    assert candidate[record_start:record_start + 2] == map_id, (
        f"map ID mismatch at {record_start:06x}"
    )
    matches = 0
    for index in range(61):
        offset = JOHTO_GRASS_START + index * RECORD_WIDTH
        if candidate[offset:offset + 2] == map_id:
            matches += 1
    assert matches == 1, f"map ID {map_id.hex()} appears {matches} times, expected 1"


def _percentages(slots):
    """Return species->level->total percent from a 14-byte slot list."""
    totals = {}
    for slot, weight in enumerate(SLOT_WEIGHTS):
        level, species = slots[slot * 2], slots[slot * 2 + 1]
        totals[(species, level)] = totals.get((species, level), 0) + weight
    return totals


def apply_encounter_corrections(candidate):
    """Adjust starter encounter rates to match the bundled 2020 descriptions."""
    ranges = []

    # Union Cave B1F: morning and day, swap slots 3 (Onix Lv8 10%) and
    # 4 (Squirtle Lv6 5%) so Squirtle becomes 10% and Onix becomes 5%.
    record_start, map_id = _UNION_CAVE_B1F
    _validate_unique_map_id(candidate, record_start, map_id)
    for period in (0, 1):
        slots = _read_slots(candidate, record_start, period)
        assert slots == [8, 74, 6, 41, 8, 41, 8, 95, 6, 7, 8, 19, 8, 19], (
            f"Union Cave B1F period {period} does not match RC3"
        )
        slots[6:8], slots[8:10] = slots[8:10], slots[6:8]
        _write_slots(candidate, record_start, period, slots)
        ranges.append(_slot_span(record_start, period, 3, "union_cave_slot3"))
        ranges.append(_slot_span(record_start, period, 4, "union_cave_slot4"))
    # Synthetic probability check: Squirtle (7) Lv6 is now 10%, Onix (95) Lv8 is 5%.
    for period in (0, 1):
        totals = _percentages(_read_slots(candidate, record_start, period))
        assert totals.get((7, 6)) == 10, f"Union Cave Squirtle Lv6 rate is {totals.get((7, 6))}%"
        assert totals.get((95, 8)) == 5, f"Union Cave Onix Lv8 rate is {totals.get((95, 8))}%"

    # Whirl Island Lugia chamber: night, move one Kabuto (140) Lv27 from the
    # 4%/1% slots to the 10% slot and restore Krabby (98) Lv27 to the vacated
    # 4%/1% slots.
    record_start, map_id = _WHIRL_ISLAND_LUGIA
    _validate_unique_map_id(candidate, record_start, map_id)
    slots = _read_slots(candidate, record_start, 2)
    assert slots == [25, 98, 26, 41, 25, 98, 27, 98, 28, 42, 27, 140, 27, 140], (
        "Whirl Island Lugia chamber night does not match RC3"
    )
    slots[6:8] = [27, 140]            # slot 3 <- Kabuto Lv27
    slots[10:14] = [27, 98, 27, 98]   # slots 5,6 <- Krabby Lv27
    _write_slots(candidate, record_start, 2, slots)
    ranges.append(_slot_span(record_start, 2, 3, "whirl_island_slot3"))
    ranges.append(_slot_span(record_start, 2, 5, "whirl_island_slot5"))
    ranges.append(_slot_span(record_start, 2, 6, "whirl_island_slot6"))
    totals = _percentages(_read_slots(candidate, record_start, 2))
    assert totals.get((140, 27)) == 10, f"Whirl Island Kabuto Lv27 rate is {totals.get((140, 27))}%"
    assert totals.get((98, 27)) == 5, f"Whirl Island Krabby Lv27 rate is {totals.get((98, 27))}%"

    # Dark Cave Violet entrance: night, swap slots 3 (Geodude Lv4 10%) and
    # 6 (Cyndaquil Lv4 1%) so Cyndaquil becomes 30%+10%=40% at night.
    record_start, map_id = _DARK_CAVE_VIOLET
    _validate_unique_map_id(candidate, record_start, map_id)
    slots = _read_slots(candidate, record_start, 2)
    assert slots == [3, 74, 2, 155, 2, 74, 4, 74, 2, 41, 4, 206, 4, 155], (
        "Dark Cave Violet entrance night does not match RC3"
    )
    slots[6:8], slots[12:14] = slots[12:14], slots[6:8]
    _write_slots(candidate, record_start, 2, slots)
    ranges.append(_slot_span(record_start, 2, 3, "dark_cave_slot3"))
    ranges.append(_slot_span(record_start, 2, 6, "dark_cave_slot6"))
    totals = _percentages(_read_slots(candidate, record_start, 2))
    assert totals.get((155, 2)) == 30, f"Dark Cave Cyndaquil Lv2 rate is {totals.get((155, 2))}%"
    assert totals.get((155, 4)) == 10, f"Dark Cave Cyndaquil Lv4 rate is {totals.get((155, 4))}%"

    # Route 31: Chikorita already 10% in the morning; assert and leave unchanged.
    record_start, map_id = _ROUTE_31
    _validate_unique_map_id(candidate, record_start, map_id)
    slots = _read_slots(candidate, record_start, 0)
    assert slots[2 * 3:2 * 3 + 2] == [5, 152], (
        "Route 31 morning Chikorita slot does not match RC3"
    )
    totals = _percentages(slots)
    assert totals.get((152, 5)) == 10, f"Route 31 Chikorita Lv5 rate is {totals.get((152, 5))}%"

    # Route 32: day, swap slots 2 (Bellsprout Lv7 20%) and 5 (Totodile Lv7 4%).
    record_start, map_id = _ROUTE_32
    _validate_unique_map_id(candidate, record_start, map_id)
    slots = _read_slots(candidate, record_start, 1)
    assert slots == [4, 23, 5, 19, 7, 69, 6, 179, 7, 16, 7, 158, 7, 187], (
        "Route 32 day does not match RC3"
    )
    slots[4:6], slots[10:12] = slots[10:12], slots[4:6]
    _write_slots(candidate, record_start, 1, slots)
    ranges.append(_slot_span(record_start, 1, 2, "route_32_slot2"))
    ranges.append(_slot_span(record_start, 1, 5, "route_32_slot5"))
    totals = _percentages(_read_slots(candidate, record_start, 1))
    assert totals.get((158, 7)) == 20, f"Route 32 Totodile Lv7 rate is {totals.get((158, 7))}%"
    assert totals.get((69, 7)) == 4, f"Route 32 Bellsprout Lv7 rate is {totals.get((69, 7))}%"

    return ranges


def apply_red_level_correction(candidate):
    """Set Red's six party members to level 100 while preserving species/items/moves/DVs."""
    groups = trainer_groups(candidate, 0x399BA, 0x3B775)
    red = groups[62][0]
    start, type_offset, kind, width, members = red
    assert kind == 3, f"Red trainer kind is {kind}, expected 3"
    assert len(members) == 6, f"Red has {len(members)} members, expected 6"
    expected_species = (25, 196, 143, 3, 6, 9)
    expected_initial_levels = (81, 73, 75, 77, 77, 77)
    ranges = []
    for member, species, initial in zip(members, expected_species, expected_initial_levels):
        assert candidate[member + 1] == species, (
            f"Red species mismatch at {member:06x}: {candidate[member + 1]} != {species}"
        )
        assert candidate[member] == initial, (
            f"Red level mismatch at {member:06x}: {candidate[member]} != {initial}"
        )
        candidate[member] = 100
        ranges.append((member, 1, "red_level"))
    return ranges


def apply_hall_hook_correction(candidate):
    """Neutralize the hook's skip for flag 0x2B7 so Pikachu doll is granted."""
    hook = candidate[HALL_HOOK_START:HALL_HOOK_START + HALL_HOOK_SIZE]
    assert hook[:4] == bytes.fromhex("7aa72036")
    assert hook[-3:] == bytes.fromhex("c3412e")
    # The hook is assembled from hall_decorations_hook.asm unchanged; the
    # "cp $b7 / jr z, .next" sequence is at a fixed offset inside the hook.
    skip_offset = HALL_HOOK_START + 20
    assert candidate[skip_offset:skip_offset + 4] == bytes.fromhex("feb72817")
    candidate[skip_offset:skip_offset + 4] = bytes(4)
    return [(skip_offset, 4, "hall_decoration_hook_include_2b7")]


def apply_rc4_corrections(original, english_stock, perfect, output):
    """Apply the complete RC4 correction layer and return modified ranges.

    Arguments match the other apply_* helpers for drop-in use.  Only `output`
    is modified; the other ROMs are available for future guards.  Changes are
    staged on a candidate copy and committed only after every guard passes.
    """
    candidate = bytearray(output)
    ranges = []
    ranges.extend(apply_encounter_corrections(candidate))
    ranges.extend(apply_red_level_correction(candidate))
    ranges.extend(apply_hall_hook_correction(candidate))
    output[:] = candidate
    return ranges
