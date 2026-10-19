"""Authored Cerulean Cave and city-entrance map definitions (JP-only).

All graphics, tilesets and collision data derive from the JP ROM.  These
definitions hold only what the JP ROM lacks: the three new cave floors
as metatile-ID rows, their header/attribute/event records, the moved
hidden item signpost, the added cave-guard person and warp, and the
changed city-entrance metatile IDs.
"""

# New cave floors in map bank $60.
CAVE_HEADERS = [
    (96, 24, 4, 0, 80, 96, 79, 18, 1),
    (96, 24, 4, 12, 80, 96, 79, 18, 1),
    (96, 24, 4, 24, 80, 96, 79, 18, 1),
]

# 12-byte map attributes per floor (banks/pointers as authored).
CAVE_ATTRS = [
    (29, 9, 15, 96, 0, 81, 96, 0, 84, 2, 84, 0),
    (29, 9, 15, 96, 135, 81, 96, 64, 84, 66, 84, 0),
    (29, 9, 15, 96, 14, 82, 96, 128, 84, 0, 86, 0),
]

# Block layouts as 9 rows of 15 metatile IDs per floor.
CAVE_BLOCKS = [
    [
        [29, 29, 4, 20, 5, 5, 5, 5, 6, 49, 49, 4, 5, 20, 6],
        [27, 26, 12, 13, 13, 13, 13, 18, 14, 24, 29, 12, 48, 13, 14],
        [49, 33, 41, 29, 49, 29, 15, 15, 15, 15, 15, 15, 15, 15, 15],
        [31, 43, 33, 29, 15, 15, 15, 29, 29, 29, 4, 5, 5, 6, 15],
        [4, 5, 5, 6, 15, 4, 5, 5, 5, 6, 8, 7, 16, 54, 15],
        [8, 7, 16, 14, 15, 8, 9, 29, 7, 10, 12, 18, 14, 15, 15],
        [12, 18, 14, 24, 15, 12, 18, 17, 29, 10, 28, 36, 42, 4, 6],
        [28, 2, 42, 29, 15, 15, 15, 12, 18, 14, 2, 36, 36, 12, 14],
        [29, 32, 36, 25, 25, 25, 25, 40, 43, 29, 4, 5, 35, 5, 6],
    ],
    [
        [29, 24, 25, 40, 31, 24, 25, 25, 25, 26, 40, 33, 30, 24, 31],
        [31, 28, 25, 25, 25, 28, 28, 28, 26, 42, 43, 43, 30, 32, 42],
        [42, 25, 25, 25, 28, 25, 40, 25, 30, 24, 40, 34, 43, 33, 28],
        [24, 25, 25, 42, 25, 25, 32, 29, 30, 31, 34, 31, 24, 40, 33],
        [40, 24, 25, 25, 25, 25, 40, 41, 25, 25, 25, 28, 28, 26, 25],
        [30, 31, 28, 25, 25, 26, 30, 25, 25, 25, 25, 40, 26, 30, 30],
        [41, 26, 24, 25, 26, 34, 30, 42, 28, 25, 25, 26, 30, 30, 41],
        [24, 30, 40, 29, 33, 30, 42, 28, 25, 25, 24, 30, 30, 33, 43],
        [28, 25, 25, 43, 33, 41, 40, 25, 25, 25, 28, 25, 25, 40, 34],
    ],
    [
        [4, 5, 5, 5, 5, 5, 5, 6, 4, 5, 6, 4, 5, 5, 6],
        [8, 9, 16, 13, 13, 13, 18, 14, 12, 18, 14, 8, 9, 29, 10],
        [8, 7, 10, 24, 25, 2, 2, 25, 2, 33, 29, 8, 16, 17, 10],
        [12, 13, 14, 40, 4, 5, 5, 5, 6, 4, 5, 29, 10, 12, 54],
        [24, 40, 43, 34, 8, 16, 17, 49, 10, 8, 16, 13, 14, 15, 15],
        [43, 49, 4, 5, 9, 10, 8, 49, 10, 18, 14, 15, 15, 15, 29],
        [41, 30, 12, 13, 18, 14, 12, 48, 14, 15, 49, 15, 4, 5, 6],
        [49, 2, 24, 2, 33, 29, 15, 15, 29, 15, 49, 15, 12, 48, 14],
        [49, 41, 2, 43, 49, 49, 49, 15, 15, 15, 29, 15, 15, 15, 15],
    ],
]

# Event records per floor: warps, xy-triggers, signposts, people.
CAVE_EVENTS = [
    {'filler': (0, 0), 'warps': [(15, 25, 7, 7, 17), (9, 23, 1, 7, 19), (1, 27, 2, 7, 19), (1, 7, 3, 7, 19), (11, 17, 4, 7, 19), (11, 3, 5, 7, 19), (3, 1, 6, 7, 19), (7, 1, 1, 7, 20)], 'xy': [], 'signposts': [], 'people': []},
    {'filler': (0, 0), 'warps': [(7, 23, 2, 7, 18), (1, 29, 3, 7, 18), (1, 9, 4, 7, 18), (7, 19, 5, 7, 18), (11, 3, 6, 7, 18), (3, 1, 7, 7, 18)], 'xy': [], 'signposts': [], 'people': []},
    {'filler': (0, 0), 'warps': [(5, 3, 8, 7, 18)], 'xy': [], 'signposts': [], 'people': [(76, 17, 31, 1, 0, 255, 255, 0, 0, 24, 97, 5, 1)]},
]

# Hidden Berserk Gene signpost moves five tiles south; its event
# flag, item id and payload pointer keep their JP values.
HIDDEN_SIGN_Y = 17

# The added city cave-guard person event (script pointer is patched
# by the builder to its new bank-$61 dialogue).
GUARD_PERSON = (35, 18, 6, 6, 0, 255, 255, 0, 0, 188, 64, 79, 7)

# Extra warp appended to the Cerulean City event table.
NEW_CITY_WARP = (13, 2, 1, 7, 18)

# Changed entrance metatile IDs: (height, width, [(index, old, new)]).
CITY_BLOCK_CHANGES = {
    'CeruleanCity': (18, 20, [
        (100, 43, 44),
        (101, 37, 41),
        (120, 37, 87),
        (121, 67, 112),
        (140, 67, 1),
        (141, 67, 1),
        (160, 67, 31),
        (161, 67, 31),
    ]),
    'Route4': (9, 20, [
        (58, 97, 24),
        (59, 24, 1),
        (79, 67, 31),
    ]),
}
