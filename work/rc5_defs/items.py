"""Authored ItemAttributes changes for the JP-only build.

Released-2020 records for the 13 items whose price, held effect,
parameter, permissions, pocket or field-menu byte changes.  Unlisted
items stay Japanese-original.  Each entry is (item_id, (price, effect,
param, permissions, pocket, fieldmenus)) written into the 7-byte JP
record (price serialized little-endian).
"""

JP_TABLE_OFFSET = 0x69fa
ITEM_RECORD_COUNT = 255

CHANGED_ITEMS = [
    (3, (50000, 77, 20, 64, 1, 0)),
    (8, (2100, 0, 0, 64, 1, 80)),
    (30, (50000, 0, 0, 64, 1, 0)),
    (60, (50000, 0, 0, 64, 1, 0)),
    (75, (50000, 0, 0, 64, 1, 0)),
    (96, (50000, 62, 10, 64, 1, 0)),
    (144, (100, 64, 0, 64, 1, 0)),
    (146, (50000, 3, 10, 64, 1, 0)),
    (151, (2100, 0, 10, 64, 1, 0)),
    (163, (50000, 0, 0, 64, 1, 0)),
    (170, (50000, 50, 10, 64, 1, 0)),
    (180, (50000, 0, 0, 64, 1, 0)),
    (200, (3000, 0, 0, 64, 4, 80)),
]
