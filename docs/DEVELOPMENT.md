# 開発・検証フロー

## 準備

1. プライベートワークスペースを準備し、必要な ROM と第三者ツリーを配置します。
2. `PC_WORKSPACE` 環境変数を設定するか、リポジトリルートにファイルを配置します。
3. `work/prepare_pokemontools.py` を実行し、ディスアセンブルユーティリティに Python 3 互換性修正を適用します（メインビルドには不要）。

## Hall Decoration Hook のビルド

`work/build_partial_jp_patch.py` は `work/hall_decorations_hook.gb` を読み込むため、メインビルドより先にフックをビルドしてください。

```bash
export PC_WORKSPACE=/path/to/private/workspace
export PC_RGBDS=/path/to/rgbds-0.2.5
bash work/build_hall_hook.sh
```

出力は `PC_WORKSPACE/work/hall_decorations_hook.gb` に書き出されます。

## ローカルビルド

```bash
python3 work/build_partial_jp_patch.py
```

このスクリプトは以下を生成します（すべて `.gitignore` で無視されます）。

- `work/development_only_jp_partial.gbc`
- `work/development_only_jp_partial.ips`
- 各種 `work/*_ranges.json`
- `work/rc1_reference.gbc`、`work/rc2_reference.gbc`、`work/rc3_reference.gbc`、`work/rc4_reference.gbc`

## ドキュメント生成

ビルド済み ROM から、リポジトリルートの `PORTING_STATUS.md`（チェックイン済みガイド）をテンプレートとして、データ表と最終生成物のマーカー区間のみを再生成し、`work/PORTING_STATUS.md` と `work/README_JP.md` を書き出します。マーカー区間以外の文章は書き換えません。パッケージングの前に実行してください。

```bash
python3 work/document_perfect_changes.py            # work/ と work/release/ 配下を更新
python3 work/document_perfect_changes.py --update-source  # リポジトリルートの PORTING_STATUS.md も更新
```

## パッケージング

検証スクリプトをすべて通過した後、`work/package_jp_patch.py` でリリース用 IPS を作成します。

```bash
python3 work/package_jp_patch.py
```

このスクリプトは `PC_WORKSPACE/work/` からビルド済み ROM/IPS、CPU 検証レポート、ドキュメント（`README_JP.md`、`PORTING_STATUS.md`）を読み込み、パッケージング結果を `PC_WORKSPACE/work/release/` に書き出します。`verify_rc2_release.py` / `verify_rc3_release.py` は追加で `PC_WORKSPACE/work/release/RC1_metadata` および `RC2_metadata` を参照します。

## ユーザー ROM への適用

```bash
python3 work/apply_jp_patch.py \
  "$PC_WORKSPACE/Pocket Monsters - Crystal Version (Japan).gbc" \
  --output /path/to/output.gbc
```

## 検証

各 `verify_*.py` スクリプトは、二進数レベルで ROM または中間ファイルを検証します。`package_jp_patch.py` はこれらを順次呼び出します。

主要な検証項目：

- `verify_partial_jp_patch.py` — RC3 基盤・RC4 修正層・RC5 画像復元の全層を検証
- `verify_rc4_delta.py` — RC3 からの限定した変更範囲。引数に `rc4_reference.gbc` を渡すと歴史的 RC4 スナップショットを検証
- `verify_rc5_delta.py` — RC4 スナップショットからの限定した復元範囲と、実際に展開した画像・アニメーション・パレットの日本語原版一致
- `verify_cerulean_cave.py` — ハナダの洞窟のマップ/イベント/テキスト
- `verify_gs_ball_binary.py` — ジーエスボールイベントの分岐
- `verify_red_rewards_binary.py` — レッド戦後の装飾品フラグ
- `verify_trainer_binary.py`、`compare_red.py` — レッドを含むトレーナー改変
- `audit_encounter_tables.py` — RC4 野生出現率の検証
- `verify_requested_fixes.py` — RC2 要求修正（ムーンボール、りゅうのキバ、コイキング長さ、2段階能力低下）
- `verify_held_item_stat_cap.py` — RC3 持ち物ステータス上限修正
- `verify_gym_rematches.py`、`verify_dialogue_updates.py`、`verify_remaining_features.py` — ジム再戦/テキスト/その他機能
- `verify_rc4_cpu_reports.py` — Hall フックの Hall/非 Hall/繰り返し 3 モード CPU 検証。`--revision RC5` で `rc5_cpu_verification.json` を出力

## 既知の制限

- 実機での動作確認は行われていません。
- 全ストーリー最初から最後までのプレイスルー検証は行われていません。
- 歴史的検証実績：RC2 CPU 参照 24 件、RC3 CPU 6245 件 + 独立 smoke 7 件
- RC4/RC5 の CPU 検証：Hall フック 3 モード（RC5 は RC4 からフックコード無変更を確認の上で再実施）

## 環境変数まとめ

| 変数 | デフォルト | 用途 |
|------|------------|------|
| `PC_WORKSPACE` | リポジトリルート | プライベートワークスペース全体 |
| `PC_RGBDS` | `$PC_WORKSPACE/rgbds-0.2.5` | RGBDS バイナリディレクトリ |
