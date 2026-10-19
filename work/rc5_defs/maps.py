"""Authored map indices for the JP-only build (public map_names data).

GROUP_COUNTS lists how many map headers each of the 26 groups holds in
the original Japanese ROM (388 total).  NAMES maps the map names the
build needs to their (group, map_id) indices; all other headers are read
from the JP ROM by index.  The released-2020 extended primary table
holds 391 entries: the three Cerulean Cave floors join group 7 as map
ids 18/19/20, shifting every later group-7 map by three.
"""

GROUP_COUNTS = (14, 7, 91, 9, 10, 8, 17, 7, 6, 17, 24, 13, 6, 8, 12, 8, 13, 14, 4, 6, 26, 16, 13, 13, 15, 11)

NAMES = {
    'CeruleanCity': (7, 17),
    'Route4': (7, 12),
    'VictoryRoad': (3, 91),
    'SilverCaveRoom1': (3, 74),
    'SilphCo1F': (25, 10),
    'GoldenrodDeptStore4F': (11, 14),
    'CeladonDeptStore3F': (21, 7),
    'Route8': (18, 1),
    'SaffronPokeCenter1F': (25, 6),
    'VermilionCity': (12, 3),
    'VioletGym': (10, 7),
    'AzaleaGym': (8, 5),
    'GoldenrodGym': (11, 3),
    'EcruteakGym': (4, 7),
    'CianwoodGym': (22, 5),
    'OlivineGym': (1, 2),
    'MahoganyGym': (2, 2),
    'BlackthornGym1F': (5, 1),
    'PewterGym': (14, 4),
    'CeruleanGym': (7, 6),
    'VermilionGym': (12, 11),
    'CeladonGym': (21, 21),
    'FuchsiaGym': (17, 8),
    'SaffronGym': (25, 4),
    'SeafoamGym': (6, 4),
    'ViridianGym': (23, 4),
}

CAVE_GROUP = 7
CAVE_MAP_IDS = (18, 19, 20)
JP_TOTAL_MAPS = 388
EXTENDED_TOTAL_MAPS = 391
