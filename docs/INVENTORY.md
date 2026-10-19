# 移行ファイル対照表

## 収録ソースと文書

| カテゴリ | 件数 | 説明 |
|----------|------|------|
| Python ビルド/ポート/修正/検証/調査スクリプト | 163 件 | `work/*.py`。既定の JPオンリー ビルダー `work/build_rc5_from_jp.py`、パッケージング `work/package_rc5_from_jp.py`、共有変更レイヤー `work/rc5_layers.py`、歴史的ビルダー `work/build_partial_jp_patch.py`、ヘルパー `work/pc_env.py`・`work/prepare_pokemontools.py` を含む |
| JPオンリー 用の作成済み定義 | 8 件 | `work/rc5_defs/`（charmap、マップ索引、出現、トレーナー、持ち物、洞窟/街レイアウト、Hall フックエミッタ） |
| ビルドスクリプト | 1 件 | `work/build_hall_hook.sh`（フック ASM の独立検証用・任意） |
| Ghidra スクリプト | 5 件 | `work/ghidra_scripts/*.java` |
| RGBDS フック ASM | 1 件 | `work/hall_decorations_hook.asm`（フックエミッタの照合元・任意検証用） |
| プレイヤーズガイド | 1 件 | `PORTING_STATUS.md`（リポジトリルート・RC5 総合ガイド、データ表はマーカー区間のみ自動生成） |
| ソースのみテスト | 2 件 | `tests/test_source_only.py`、`tests/test_jp_only_build.py` |
| **合計** | **181 件** | ソースのみ |

## 意図的に移行しなかったファイル

元の `work/` ディレクトリからは、以下のファイル種別を一切移行していません。

| 種別 | 例 | 除外理由 |
|------|-----|----------|
| ROM/GBC/GB ファイル | `*.gbc`, `*.gb` | 著作権で保護されたバイナリ |
| IPS/BPS パッチ | `*.ips`, `*.bps` | 配布物/生成物 |
| セーブ/RTC/RAM | `*.sav`, `*.ram`, `*.rtc` | プライベートランタイムデータ |
| 画像/スクリーンショット | `*.png` | 著作権/個人データ |
| オブジェクト/リンク出力 | `*.o`, `*.sym`, `*.map` | RGBDS 生成物 |
| 生成逆アセンブル | `*_pokemontools.asm`, `*_actual.asm` | pokemontools 出力 |
| 生成 JSON ダンプ | `*_ranges.json`, `*_results.json`, `*_verification.json` | 検証実行結果 |
| パッチ/差分ファイル | `*.patch`, `*.diff` | 生成物 |
| リリースディレクトリ | `work/release/` | パッケージング出力 |
| 第三者ソースツリー | `pokemon-reverse-engineering-tools/`, `pokekuristaru/` など | 依存関係として別途取得 |

## 完全ファイルリスト

```
PORTING_STATUS.md
tests/test_jp_only_build.py
tests/test_source_only.py
work/apply_jp_patch.py
work/apply_japanese_original_sprites.py
work/apply_rc4_corrections.py
work/archive_rc1_release.py
work/archive_rc2_release.py
work/audit_base_stats.py
work/audit_encounter_tables.py
work/audit_initial_rom_candidates.py
work/audit_item_attributes.py
work/audit_map_and_move_data.py
work/audit_match_baseline.py
work/audit_remaining_features.py
work/audit_source_base.py
work/audit_species_records.py
work/battle_coverage_baseline.py
work/battle_coverage_commands.py
work/battle_coverage_items.py
work/battle_coverage_scan.py
work/battle_coverage_source_diff.py
work/battlefix_inspect.py
work/battlefix_more_scan.py
work/battlefix_scan.py
work/build_hall_hook.sh
work/build_partial_jp_patch.py
work/build_rc5_from_jp.py
work/classify_ips_records.py
work/clockreset_analyse.py
work/clockreset_ui.py
work/compare_marts.py
work/compare_other_encounters.py
work/compare_perfect_encounters.py
work/compare_red.py
work/compare_trainers_binary.py
work/dialogue_gym_playthrough.py
work/dialogue_mapping.py
work/dialogue_visual_probe.py
work/disassemble_event_runtime.py
work/disassemble_jp_event_flag_action.py
work/disassemble_map_loader.py
work/disassemble_misc_fixes.py
work/document_perfect_changes.py
work/dragon_fang_disassemble.py
work/find_ai_random_fail.py
work/find_ai_rng_calls.py
work/find_badge_routines.py
work/find_bank05_free.py
work/find_bank15_cave.py
work/find_bank20_free.py
work/find_clock_reset.py
work/find_jp_marts.py
work/find_jp_red.py
work/find_jp_tm_routine.py
work/find_red_person_event.py
work/find_tm_code_anchor.py
work/find_trainer_bank_free.py
work/finish_rc2_rom.py
work/fix_dragon_fang.py
work/fix_held_item_stat_cap.py
work/fix_magikarp_comparison.py
work/fix_moon_ball.py
work/fix_requested_issues.py
work/fix_sharp_stat_drop.py
work/ghidra_scripts/CrystalFixProbe.java
work/ghidra_scripts/CrystalHeldCapProbe.java
work/ghidra_scripts/CrystalMapProbe.java
work/ghidra_scripts/CrystalProbe.java
work/ghidra_scripts/CrystalTargetProbe.java
work/gym_bank_caves.py
work/gym_disassemble_handlers.py
work/gym_inspect.py
work/gym_text_engine.py
work/gym_text_evidence.py
work/hall_decorations_hook.asm
work/held_cap_audit_review.py
work/held_cap_audit_rom.py
work/held_cap_audit_smoke.py
work/held_item_stat_cap_inspect.py
work/inspect_cerulean.py
work/inspect_gs_flow.py
work/inspect_landmark_cursor.py
work/inspect_landmarks.py
work/inspect_map_scripts.py
work/inspect_map_space.py
work/inspect_misc_fixes.py
work/inspect_wild_tables.py
work/japanese_text.py
work/locate_red_script.py
work/magikarp_comparison_analyse.py
work/map_layout.py
work/moon_ball_fix_inspect.py
work/nonbattle_event_fields_audit.py
work/nonbattle_source_audit.py
work/package_jp_patch.py
work/package_rc5_from_jp.py
work/pc_env.py
work/prepare_pokemontools.py
work/port_battle_bugfixes.py
work/port_cerulean_cave.py
work/port_clock_reset.py
work/port_dialogue_updates.py
work/port_gym_rematches.py
work/port_item_attributes.py
work/port_misc_fixes.py
work/port_remaining_features.py
work/port_restored_sprites.py
work/prepare_expected_johto_grass.py
work/prepare_expected_johto_water.py
work/rc5_defs/__init__.py
work/rc5_defs/cave.py
work/rc5_defs/charmap.py
work/rc5_defs/encounters.py
work/rc5_defs/hall_hook.py
work/rc5_defs/items.py
work/rc5_defs/maps.py
work/rc5_defs/trainers.py
work/rc5_layers.py
work/remaining_disassemble.py
work/remaining_play_names.py
work/remaining_playthrough.py
work/remaining_probe.py
work/remaining_source_inventory.py
work/run_pokemontools_entry.py
work/scan_johto_grass.py
work/scan_red_event.py
work/scan_red_flag.py
work/scan_trade_evolutions.py
work/sharp_stat_drop_disassemble.py
work/smoke_boot_partial.py
work/sprite_cpu.py
work/sprite_inspect.py
work/test_cave_playthrough.py
work/test_clock_save_roundtrip.py
work/test_event_scripts_emulator.py
work/test_gs_ball_playthrough.py
work/test_hall_hook_emulator.py
work/test_landmark_cursor_emulator.py
work/test_map_port_emulator.py
work/trainer_party_layout.py
work/verify_battlefix_binary.py
work/verify_battlefix_capture_cpu.py
work/verify_battlefix_cpu.py
work/verify_battlefix_length_cpu.py
work/verify_cerulean_cave.py
work/verify_clockreset_build.py
work/verify_clockreset_emulator.py
work/verify_dialogue_cpu.py
work/verify_dialogue_updates.py
work/verify_dragon_fang_fix_cpu.py
work/verify_gs_ball_binary.py
work/verify_gym_cpu.py
work/verify_gym_rematches.py
work/verify_gym_text_cpu.py
work/verify_held_item_stat_cap_cpu.py
work/verify_held_item_stat_cap.py
work/verify_kanto_wild_binary.py
work/verify_magikarp_comparison_build.py
work/verify_magikarp_comparison_cpu.py
work/verify_misc_cpu.py
work/verify_moon_ball_fix_cpu.py
work/verify_moon_ball_fix.py
work/verify_partial_jp_patch.py
work/verify_rc2_cpu_reports.py
work/verify_rc2_release.py
work/verify_rc3_cpu_reports.py
work/verify_rc3_delta.py
work/verify_rc3_release.py
work/verify_rc4_cpu_reports.py
work/verify_rc4_delta.py
work/verify_rc5_delta.py
work/verify_red_rewards_binary.py
work/verify_remaining_cpu.py
work/verify_remaining_features.py
work/verify_requested_fixes.py
work/verify_restored_sprites.py
work/verify_sharp_stat_drop_cpu.py
work/verify_sharp_stat_drop.py
work/verify_trainer_binary.py
work/verify_wild_binary.py
```
