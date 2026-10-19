"""Default RC5 builder: reproduce the exact release from the Japanese ROM only.

Requires ONLY the user's original Japanese Crystal ROM (plus the public
lazy_ips dependency for the round-trip check).  No English ROM, released
2020 IPS, historical snapshot, CPU report, public disassembly tree or
extracted asset is read.  All changes are authored machine instructions and
semantic definitions (rc5_defs); unchanged data is preserved by reading the
JP ROM.

Outputs (in the private workspace work/ directory):
  - development_only_jp_partial.gbc
  - development_only_jp_partial.ips
"""
import argparse
from hashlib import sha1, sha256
from pathlib import Path
import sys

from pc_env import workspace

INPUT_SHA1 = '95127b901bbce2407daf43cce9f45d4c27ef635d'
INPUT_SHA256 = '136ada06cb68656b7de475fa4b278d37dbeff8f5257e7dfdf7f4a4aec19a90f3'
ROM_SIZE = 2 * 1024 * 1024
EXPECTED_ROM_SHA256 = 'b2fbf4f562e0ea2c73758f3862bf70bc5715e751f6e3492b26dd5d353050f5e7'
EXPECTED_IPS_SHA256 = 'f000003c68aa41f4ac9358fa454ab4495bc667a7208f35e0510ea8b3d167ce00'


def build(original):
    """Apply every authored layer to the JP ROM and return the RC5 bytes."""
    output = bytearray(original)

    from rc5_layers import (
        apply_ai_fixes, apply_badge_boosts, apply_b_button_run, apply_encounter_tables,
        apply_gs_ball, apply_hall_hook, apply_marts,
        apply_red_rewards, apply_reusable_tm, apply_signature_moves,
        apply_tm_quantity, apply_trade_evolutions, rebuild_trainers,
    )
    apply_encounter_tables(original, output)
    apply_trade_evolutions(original, output)
    apply_signature_moves(original, output)
    apply_hall_hook(original, output)
    apply_gs_ball(original, output)
    apply_red_rewards(original, output)
    apply_reusable_tm(original, output)
    apply_tm_quantity(original, output)
    apply_b_button_run(original, output)
    apply_marts(original, output)
    rebuild_trainers(original, output)
    apply_badge_boosts(original, output)
    apply_ai_fixes(original, output)

    from port_cerulean_cave import apply_cave_port
    apply_cave_port(original, None, None, output)
    print('cerulean_cave_maps', 3, 'localized_events', 3)

    from port_clock_reset import apply_clock_reset
    apply_clock_reset(original, None, None, output)
    print('clock_reset', 'Japanese title confirmation and native RTC setup')

    from port_battle_bugfixes import apply_battle_bugfixes
    battle_ranges = apply_battle_bugfixes(original, None, None, output)
    print('battle_bugfixes', len(battle_ranges), 'validated write ranges')

    from port_gym_rematches import apply_gym_rematches
    apply_gym_rematches(original, None, None, output)
    print('gym_rematches', 16, 'Japanese dialogue')

    from port_misc_fixes import apply_misc_fixes
    misc_ranges = apply_misc_fixes(original, None, None, output)
    print('misc_fixes', len(misc_ranges), 'validated write ranges')

    from port_dialogue_updates import apply_dialogue_updates
    apply_dialogue_updates(original, None, None, output)
    print('dialogue_updates', 6, 'Japanese explanations')

    from port_item_attributes import apply_item_attributes
    item_ranges = apply_item_attributes(original, None, None, output)
    print('item_attribute_updates', len(item_ranges), 'prices and held effects')

    from port_remaining_features import apply_remaining_features
    apply_remaining_features(original, None, None, output)
    print('remaining_features', 5, 'evolution scan, HP pixels, Red DVs, trade names and Silph dialogue')

    from fix_requested_issues import apply_requested_fixes
    requested_ranges = apply_requested_fixes(original, None, None, output)
    print('requested_rc2_corrections', 4, 'validated write ranges', len(requested_ranges))

    from fix_held_item_stat_cap import apply_held_item_stat_cap_fix
    cap_ranges = apply_held_item_stat_cap_fix(original, None, None, output)
    print('requested_rc3_held_item_cap', 'validated write ranges', len(cap_ranges))

    from apply_rc4_corrections import apply_rc4_corrections
    rc4_ranges = apply_rc4_corrections(original, None, None, output)
    print('requested_rc4_corrections', 'validated write ranges', len(rc4_ranges))

    # RC5 ships the Japanese-original graphics, which the JP base already
    # holds: the historical sprite port+restore layers are intentionally
    # skipped.  Game Boy ROM header and global checksums.
    output[0x14D] = (-sum(output[0x134:0x14D]) - 25) & 0xFF
    global_sum = (sum(output) - output[0x14E] - output[0x14F]) & 0xFFFF
    output[0x14E:0x150] = global_sum.to_bytes(2, "big")
    return output


def build_ips_bytes(original, output):
    """Minimal IPS records, split at 65535 bytes if needed."""
    import io
    buffer = io.BytesIO()
    buffer.write(b"PATCH")
    index = 0
    while index < len(original):
        if original[index] == output[index]:
            index += 1
            continue
        start = index
        while index < len(original) and original[index] != output[index] and index - start < 65535:
            index += 1
        data = output[start:index]
        buffer.write(start.to_bytes(3, "big"))
        buffer.write(len(data).to_bytes(2, "big"))
        buffer.write(data)
    buffer.write(b"EOF")
    return buffer.getvalue()


def _publish(parser, target, data, input_rom):
    """Write staged bytes only: refuse input aliasing (symlink/hardlink),
    preserve differing existing files, accept identical ones idempotently."""
    if target.is_symlink():
        parser.error(f'出力先がシンボリックリンクです: {target}')
    if target.exists():
        if target.samefile(input_rom):
            parser.error(f'出力先が入力ROMと同じファイルです: {target}')
        existing = target.read_bytes()
        if existing != data:
            parser.error(f'出力先は既に別の内容で存在します: {target}')
        return  # identical: idempotent republish
    target.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(
        description='Build the RC5 Japanese port from the original Japanese ROM only.')
    parser.add_argument('rom', type=Path, nargs='?', default=None,
                        help='Original Pocket Monsters - Crystal Version (Japan).gbc '
                             '(default: the private workspace copy)')
    args = parser.parse_args()
    root = workspace()
    rom_path = args.rom or (root / "Pocket Monsters - Crystal Version (Japan).gbc")
    original = rom_path.read_bytes()
    if len(original) != ROM_SIZE:
        parser.error(f'入力ROMサイズが{ROM_SIZE}バイトではありません（切り詰められた/異なるROM）。')
    if sha1(original).hexdigest() != INPUT_SHA1 or sha256(original).hexdigest() != INPUT_SHA256:
        parser.error('入力ROMのハッシュが一致しません。日本語版クリスタルの原本が必要です。')

    output = build(original)
    actual_rom_sha256 = sha256(output).hexdigest()
    if actual_rom_sha256 != EXPECTED_ROM_SHA256:
        parser.error('ビルド結果のSHA-256が既知のRC5と一致しません。出力しません。')

    # Stage the IPS in memory and reapply it with the required lazy_ips reader
    # before anything is written to disk.
    sys.path.insert(0, str(root / "lazy_ips"))
    from io import BytesIO
    from lazy_ips.patch import ips
    ips_bytes = build_ips_bytes(original, output)
    roundtrip = bytearray(original)
    for record in ips.read_patch(BytesIO(ips_bytes)):
        end = record.offset + len(record.data)
        if end > len(roundtrip):
            parser.error('lazy_ips によるIPS検証に失敗しました。')
        roundtrip[record.offset:end] = record.data
    if bytes(roundtrip) != bytes(output):
        parser.error('lazy_ips によるIPS再適用が元のビルドと一致しません。')
    actual_ips_sha256 = sha256(ips_bytes).hexdigest()
    if actual_ips_sha256 != EXPECTED_IPS_SHA256:
        parser.error('IPSのSHA-256が既知のRC5と一致しません。')

    # Everything validated: publish (refuses aliasing, idempotent).
    work = root / 'work'
    work.mkdir(exist_ok=True)
    _publish(parser, work / "development_only_jp_partial.gbc", output, rom_path)
    _publish(parser, work / "development_only_jp_partial.ips", ips_bytes, rom_path)
    print("development_rom_sha256", actual_rom_sha256)
    print("development_ips_sha256", actual_ips_sha256)
    print("changed_bytes", sum(a != b for a, b in zip(original, output)))
    print("rc5_build_verified", "exact")


if __name__ == '__main__':
    main()
