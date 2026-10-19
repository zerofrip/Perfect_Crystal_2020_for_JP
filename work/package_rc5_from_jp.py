"""Package the JP-only RC5 candidate; never include or upload a ROM.

Default JP-only packager: verifies the built ROM/IPS against the exact known
RC5 hashes, checks the lazy_ips round-trip, and writes the release IPS plus a
manifest into PC_WORKSPACE/work/release/.  Unlike the historical
package_jp_patch.py, it does not require CPU reports, RC snapshots, English
audit scripts or generated documents.
"""
import argparse
from hashlib import sha1, sha256
from io import BytesIO
import json
from pathlib import Path
import sys

from build_rc5_from_jp import (INPUT_SHA1, INPUT_SHA256, ROM_SIZE,
                               EXPECTED_ROM_SHA256, EXPECTED_IPS_SHA256)
from pc_env import workspace

ROOT = workspace()
WORK = ROOT / 'work'
DEFAULT_ROM = 'Pocket Monsters - Crystal Version (Japan).gbc'


def _publish(parser, target, data, protected_inputs):
    """Write staged bytes only: refuse aliasing with any input (symlink or
    hardlink), preserve differing existing files, accept identical ones."""
    if target.is_symlink():
        parser.error(f'出力先がシンボリックリンクです: {target}')
    if target.exists():
        for protected in protected_inputs:
            try:
                if target.samefile(protected):
                    parser.error(f'出力先が入力ファイルと同じです: {target}')
            except OSError:
                pass
        if target.read_bytes() != data:
            parser.error(f'出力先は既に別の内容で存在します: {target}')
        return  # identical: idempotent republish
    target.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(
        description='Package the verified RC5 IPS built by build_rc5_from_jp.py.')
    parser.add_argument('rom', type=Path, nargs='?', default=None,
                        help=f'Original Pocket Monsters - Crystal Version (Japan).gbc '
                             f'(default: {DEFAULT_ROM} in the private workspace)')
    args = parser.parse_args()
    original = (args.rom or (ROOT / DEFAULT_ROM)).read_bytes()
    output = (WORK / 'development_only_jp_partial.gbc').read_bytes()
    patch = (WORK / 'development_only_jp_partial.ips').read_bytes()

    if len(original) != ROM_SIZE or len(output) != ROM_SIZE:
        parser.error('ROMサイズが想定と異なります。パッケージングを中止します。')
    if sha1(original).hexdigest() != INPUT_SHA1 or sha256(original).hexdigest() != INPUT_SHA256:
        parser.error('入力ROMのハッシュが一致しません。日本語版の原本が必要です。')
    if sha256(output).hexdigest() != EXPECTED_ROM_SHA256:
        parser.error('ビルド済みROMのSHA-256が既知のRC5と一致しません。先に build_rc5_from_jp.py を実行してください。')
    if sha256(patch).hexdigest() != EXPECTED_IPS_SHA256:
        parser.error('IPSのSHA-256が既知のRC5と一致しません。古い/未検証のIPSです。')

    sys.path.insert(0, str(ROOT / 'lazy_ips'))
    from lazy_ips.patch import ips
    roundtrip = bytearray(original)
    for record in ips.read_patch(BytesIO(patch)):
        end = record.offset + len(record.data)
        if end > len(roundtrip):
            parser.error('IPS書込先が入力ROMサイズを超えています。')
        roundtrip[record.offset:end] = record.data
    if bytes(roundtrip) != output:
        parser.error('IPSが検証済みROMを再現しません。')

    release = WORK / 'release'
    release.mkdir(exist_ok=True)
    filename = 'Perfect_Crystal_2020_Japanese_RC5.ips'
    manifest = {
        'name': 'Perfect Crystal (2020 Update) Japanese port',
        'status': 'release_candidate',
        'revision': 'RC5',
        'requested_corrections': [
            'Moon Ball: scan all evolution records; 4x catch rate capped at 255 for Moon Stone species.',
            'Dragon Fang: held effect amount 10 for Dragon moves.',
            'Magikarp length: unsigned 16-bit comparison.',
            'Sharp stat drops: decrease two stages, clamped at stage minimum.',
            'Held-item stat caps: exact minimum with 999; Metal Powder boosts 16-bit defense before damage-stat truncation.',
            'Starter encounter rates: Chikorita Route 31 morning 10%; Cyndaquil Dark Cave Violet entrance night 40%; Totodile Route 32 day 20%; Squirtle Union Cave B1F land morning/day 10%; Kabuto Whirl Island Lugia chamber night 10%.',
            "Red's party: all six Pokemon at level 100, preserving species/items/moves/DVs/Japanese name.",
            'Hall of Fame decoration flags: 42 flags (41 actual item flags plus separate poster-display flag), adding Pikachu doll (0x2B7) to the existing 41.',
            'RC5: graphics remain the Japanese originals for all five target trainer pictures, Jynx front/back, its animation frames, palettes and animation commands.',
        ],
        'rom_size': len(output),
        'input_sha1': sha1(original).hexdigest(),
        'input_sha256': sha256(original).hexdigest(),
        'ips_file': filename,
        'ips_sha256': sha256(patch).hexdigest(),
        'output_sha256': sha256(output).hexdigest(),
        'changed_bytes': sum(a != b for a, b in zip(original, output)),
        'build': 'JP-only: original Japanese ROM plus authored definitions (build_rc5_from_jp.py)',
        'limitations': ['Not tested on physical hardware.', 'Not a complete start-to-credits playthrough.'],
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')
    protected = (args.rom or (ROOT / DEFAULT_ROM),
                 WORK / 'development_only_jp_partial.gbc',
                 WORK / 'development_only_jp_partial.ips')
    _publish(parser, release / filename, patch, protected)
    _publish(parser, release / 'manifest.json', manifest_bytes, protected)
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
