# 開発・検証フロー

## 準備

1. プライベートワークスペースに日本語版 ROM と `lazy_ips` を配置します（詳細は `docs/DEPENDENCIES.md`）。
2. `PC_WORKSPACE` 環境変数を設定するか、リポジトリルートにファイルを配置します。

既定のビルドは日本語 ROM と `lazy_ips` だけで完結します。英語版 ROM や公開ソースツリーは不要です。

## 既定の JPオンリー ビルド

```bash
export PC_WORKSPACE=/path/to/private/workspace

python3 work/build_rc5_from_jp.py
```

このスクリプトは:

1. 入力 ROM のサイズ（2 MiB）と SHA-1/SHA-256 を検証し、不一致なら出力を書き込まずに中断します。
2. `work/rc5_layers.py` の共有変更レイヤーと `work/rc5_defs/` の作成済み定義を日本語 ROM に適用します（未変更データは日本語 ROM からそのまま読み込みます。歴史的スプライト移植/復元レイヤーは日本語原版が最初から維持されるためスキップします）。
3. 完全な結果をメモリ上で組み立て、ヘッダー/グローバルチェックサムを更新し、既知の RC5 出力 ROM SHA-256 と照合します。
4. IPS をメモリ上で生成し、既知の IPS SHA-256 と照合した後、`lazy_ips` での再適用が元のビルドと一致することを確認します。
5. すべての検証が通ってから `work/development_only_jp_partial.gbc` と `work/development_only_jp_partial.ips` を書き出します（既存の同一出力は冪等に再生成、異なる内容が既にある場合は拒否、入力 ROM とのパスエイリアスは拒否）。

## パッケージング

```bash
python3 work/package_rc5_from_jp.py
```

ビルド済み ROM/IPS と入力 ROM を検証し、`lazy_ips` ラウンドトリップを確認した後、`work/release/` に `Perfect_Crystal_2020_Japanese_RC5.ips` と `manifest.json`（`rom_size`、`input_sha1`、`input_sha256`、`ips_file`、`ips_sha256`、`output_sha256`）を書き出します。書き出しポリシーはビルダーと同じです（エイリアス拒否・異なる既存ファイルの保護・同一出力の冪等）。この manifest は `apply_jp_patch.py` がそのまま使用します。

## ユーザー ROM への適用

```bash
python3 work/apply_jp_patch.py \
  "$PC_WORKSPACE/Pocket Monsters - Crystal Version (Japan).gbc" \
  --output /path/to/output.gbc
```

## ドキュメント生成（開発者・参照環境のみ）

`work/document_perfect_changes.py` は、リポジトリルートの `PORTING_STATUS.md`（チェックイン済みガイド）をテンプレートとして、データ表と最終生成物のマーカー区間のみを実ROMから再生成します。ただしこのツール自体は、英語版オリジナル/2020適用済みROM、RC4スナップショット、公開ソースツリー（`pokekuristaru` など）を参照する**開発者・参照環境向け**のものです。JPオンリーのパッチ生成には不要で、既定ビルドの実行には何の影響もありません。

```bash
python3 work/document_perfect_changes.py            # work/ と work/release/ 配下を更新
python3 work/document_perfect_changes.py --update-source  # リポジトリルートの PORTING_STATUS.md も更新
```

## 歴史的な参照ビルド（任意）

英語版 ROM と Perfect Crystal 2020 適用済み英語版 ROM による参照チェック付きの歴史的ビルドです。依存関係の準備方法は `docs/DEPENDENCIES.md` を参照してください。

```bash
export PC_WORKSPACE=/path/to/private/workspace

# 歴史的 RC5 統合ビルド（RC1〜RC4 スナップショットのハッシュ検証を含む）
python3 work/build_partial_jp_patch.py

# 歴史的パッケージング（CPU 検証レポートを参照）
python3 work/package_jp_patch.py
```

`build_partial_jp_patch.py` は `build_rc5_from_jp.py` と同じ `work/rc5_layers.py` の変更レイヤーを使用し、英語版参照との照合を追加で実行します。Hall 装飾品フックも共有レイヤー内の検証済みエミッタ（`work/rc5_defs/hall_hook.py`）が作成するため、`build_hall_hook.sh` と RGBDS は不要です。`work/hall_decorations_hook.asm` から生成したフックとの独立検証にのみ使用します。

## ソースのみの検証

```bash
python3 -m unittest tests/test_source_only.py tests/test_jp_only_build.py
```

- `tests/test_source_only.py` — 公開ツリーの健全性（コンパイル、禁止ファイル、依存関係の解決）。
- `tests/test_jp_only_build.py` — JPオンリー ビルドの契約（不正入力の拒否と出力なし、`python -O` でも同一、歴史的依存の非参照、検証済みフックのバイト一致）。

## 環境変数まとめ

| 変数 | デフォルト | 用途 |
|------|------------|------|
| `PC_WORKSPACE` | リポジトリルート | プライベートワークスペース全体 |
| `PC_RGBDS` | `$PC_WORKSPACE/rgbds-0.2.5` | RGBDS バイナリディレクトリ（ASM フックの独立検証のみ・任意） |

## 既知の制限

- 実機での動作確認は行われていません。
- 全ストーリー最初から最後までのプレイスルー検証は行われていません。
- 歴史的検証実績：RC2 CPU 参照 24 件、RC3 CPU 6245 件 + 独立 smoke 7 件
- RC4/RC5 の CPU 検証：Hall フック 3 モード（RC5 は RC4 からフックコード無変更を確認の上で再実施）
