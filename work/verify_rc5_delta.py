"""Require the exact RC4 baseline plus only the Japanese-original graphics.

The RC5 gate reconstructs the expected ROM from the hash-gated rc4_reference
snapshot and the restoration layer, then additionally verifies the actual
decompressed graphics against the Japanese originals: the five trainer
pictures the 2020 release replaced, Jynx's front/back pictures, the base
picture plus all three rendered animation frames, the palettes and the
animation command tables.
"""
from hashlib import sha256
import json
from pathlib import Path
import sys

from pc_env import workspace
from apply_japanese_original_sprites import apply_japanese_original_sprites

WORK = workspace() / 'work'
ROOT = workspace()
PIC_POINTERS = 0x120000
TRAINER_POINTERS = 0x128000
RESTORED_TRAINERS = (('beauty', 29), ('sage', 56), ('medium', 57),
                     ('swimmer_f', 39), ('fisher', 37))

baseline = (WORK / 'rc4_reference.gbc').read_bytes()
assert sha256(baseline).hexdigest() == 'f7a0da3b9df33d4d010b05d82c8e6644d09ebd9c42320cc1ee89d4e2fd20ddd6'
stock = (ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
english = (ROOT / 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
reference = (WORK / 'perfect_crystal_ue_patched.gbc').read_bytes()
rom_arg = Path(sys.argv[1]) if len(sys.argv) == 2 else WORK / 'development_only_jp_partial.gbc'
actual = rom_arg.read_bytes()

expected = bytearray(baseline)
ranges = apply_japanese_original_sprites(stock, english, reference, expected)
expected[0x14D] = (-sum(expected[0x134:0x14D]) - 25) & 0xFF
checksum = (sum(expected) - expected[0x14E] - expected[0x14F]) & 0xFFFF
expected[0x14E:0x150] = checksum.to_bytes(2, 'big')
assert actual == expected, 'RC5 differs from the expected graphics restoration'
changed = [i for i, (a, b) in enumerate(zip(baseline, actual)) if a != b]
allowed = ranges + [(0x14D, 3, 'checksums')]
assert all(any(start <= i < start + size for start, size, _ in allowed)
           for i in changed), 'RC5 changed bytes outside the restored ranges'

# Expected RC5 hash computed independently from the unchanged historical
# sprite ranges (supervisor cross-check).
assert sha256(actual).hexdigest() == 'b2fbf4f562e0ea2c73758f3862bf70bc5715e751f6e3492b26dd5d353050f5e7'

# Actual decompressed graphics checks against the Japanese originals.
sys.path.insert(0, str(ROOT / 'work/pokemon-reverse-engineering-tools'))
from pokemontools.lz import Decompressed
Decompressed.__next__ = Decompressed.next


def word(data, offset):
    return int.from_bytes(data[offset:offset + 2], 'little')


def banked(bank, address):
    assert 0x4000 <= address < 0x8000
    return bank * 0x4000 + address - 0x4000


def picture(rom, pointer):
    offset = banked(rom[pointer] + 0x36, word(rom, pointer + 1))
    decoded = Decompressed(rom, start=offset)
    return offset, bytes(decoded.compressed_data), bytes(decoded.output)


def jynx_frames(rom):
    """Read the actual frame pointers and bitmask tile counts, not source ASM."""
    frame_table = banked(0x35, word(rom, 0xD40F6))
    mask_table = banked(0x34, word(rom, 0xD25E5))
    frames = []
    for i in range(3):
        frame = banked(0x35, word(rom, frame_table + 2 * i))
        mask_id = rom[frame]
        assert mask_id < 3
        mask = rom[mask_table + 5 * mask_id:mask_table + 5 * mask_id + 5]
        count = sum(b.bit_count() for b in mask)
        frames.append((mask, bytes(rom[frame + 1:frame + 1 + count])))
    return frames


def rendered_tiles(rom):
    """Reconstruct frame tile selections using the ROM bitmask and tile IDs."""
    image = picture(rom, PIC_POINTERS + 123 * 6)[2]
    assert len(image) % 16 == 0
    count = len(image) // 16
    result = [image[:36 * 16]]
    for mask, replacements in jynx_frames(rom):
        indices = list(range(36))
        replacement = iter(replacements)
        for bit in range(40):
            if mask[bit // 8] & (1 << (bit % 8)):
                assert bit < 36
                index = next(replacement)
                assert index < count
                indices[bit] = index
        assert next(replacement, None) is None
        result.append(b''.join(image[i * 16:i * 16 + 16] for i in indices))
    return result


for name, index in RESTORED_TRAINERS:
    pointer = TRAINER_POINTERS + (index - 1) * 3
    assert picture(actual, pointer)[2] == picture(stock, pointer)[2], name
for side in range(2):
    pointer = PIC_POINTERS + 123 * 6 + side * 3
    assert picture(actual, pointer)[2] == picture(stock, pointer)[2], ('jynx', side)
assert jynx_frames(actual) == jynx_frames(stock)
assert rendered_tiles(actual) == rendered_tiles(stock)
assert actual[0xA88B:0xB198] == stock[0xA88B:0xB198]      # palettes
assert actual[0xD0695:0xD24EF] == stock[0xD0695:0xD24EF]  # animation commands

result = {
    'base_rc4_sha256': sha256(baseline).hexdigest(),
    'verified_rom': rom_arg.name,
    'output_sha256': sha256(actual).hexdigest(),
    'changed_bytes_from_rc4': len(changed),
    'changed_bytes_excluding_checksums': sum(not 0x14D <= i < 0x150 for i in changed),
    'restored_ranges': len(ranges),
    'outside_restored_ranges': 0,
    'ranges': ranges,
    'graphics_checks': [
        'Five 2020-replaced trainer pictures decompress to the Japanese originals.',
        "Jynx front and back pictures decompress to the Japanese originals.",
        'Jynx base picture plus all three rendered animation frames match the Japanese originals.',
        'Palettes and animation command tables match the Japanese originals.',
    ],
    'passed': True,
}
(WORK / 'rc5_delta_verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
