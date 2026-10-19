# Perfect Crystal 2020 Japanese port

このリポジトリは、『ポケットモンスター クリスタルバージョン』（日本語版）向けに、Perfect Crystal 2020 Update の内容を移植するために、この移植作業で作成したソースコードです。

**本リポジトリには ROM、画像、音声、抽出データ、または第三者のソースツリーは含まれていません。** 必要な入力ファイルと第三者ツールは、利用者がローカル環境で別途準備してください。

## 概要

- ターゲット：日本語版ポケットモンスター クリスタルバージョン
- ベース Perfect Crystal 2020 Update（英語版）の内容を日本語 ROM に移植
- ベース Perfect Crystal 2020 Update（英語版）の全内容を引き継ぎ、グラフィックを日本語原版仕様に戻した版です

ゲーム内容の変更一覧と遊び方は、**[PORTING_STATUS.md](PORTING_STATUS.md)（プレイヤーズガイド）** を参照してください。

## ソース構成

```
.
├── LICENSE                              Apache 2.0
├── README.md                            このファイル
├── PORTING_STATUS.md                    プレイヤーズガイド（変更一覧・遊び方・技術記録）
├── requirements.txt                     Python 依存関係（オプション含む）
├── .gitignore                           追跡禁止ファイルの定義
├── work/                                主要な Python スクリプト
│   ├── pc_env.py                        ワークスペース解決ヘルパー
│   ├── build_rc5_from_jp.py             既定の JPオンリー RC5 ビルダー
│   ├── package_rc5_from_jp.py           既定の JPオンリー パッケージング
│   ├── rc5_layers.py                    共有の変更レイヤー（両ビルダーで使用）
│   ├── rc5_defs/                        作成済みの意味的変更定義（日本語 ROM のみで使用）
│   ├── build_partial_jp_patch.py        歴史的統合ビルダー（英語版参照が必要・任意）
│   ├── package_jp_patch.py              歴史的パッケージング（CPU レポート等が必要・任意）
│   ├── apply_jp_patch.py                ユーザー所有 ROM への IPS 適用
│   ├── trainer_party_layout.py          トレーナーデータの再配置ロジック
│   ├── port_*.py                        各種移植モジュール
│   ├── fix_*.py                         RC2/RC3 修正モジュール
│   ├── verify_*.py                      二進数/CPU 検証スクリプト
│   ├── audit_*.py                       監査/比較ヘルパー
│   ├── ghidra_scripts/                  ローカル Ghidra 調査スクリプト（5 件）
│   └── hall_decorations_hook.asm        殿堂入り装飾品フラグ用 RGBDS フック
├── docs/
│   ├── DEPENDENCIES.md                  第三者依存関係の準備方法
│   ├── DEVELOPMENT.md                   開発・検証フロー
│   └── INVENTORY.md                     移行ファイルと除外ファイルの対照表
└── tests/
    ├── test_source_only.py              ソースのみの健全性チェック
    └── test_jp_only_build.py            JPオンリー ビルドの契約テスト
```

## 動作に必要な環境

- Python 3.11 以上（開発時は Python 3.14.4 でテスト済み）
- 利用者が所有する日本語版 Crystal ROM（SHA-1: `95127b901bbce2407daf43cce9f45d4c27ef635d`）
- `lazy_ips`（IPS 生成と再適用検証に使用。詳細は `docs/DEPENDENCIES.md`）

**既定のビルドに英語版 ROM、2020 年版 IPS、過去のスナップショット、検証レポート、公開逆アセンブリツリーは不要です。** すべての変更は `work/rc5_defs/` の人間が読める定義と作成済みの機械語として同梱され、未変更データは日本語 ROM からそのまま読み込まれます。

歴史的な参照ビルド（`build_partial_jp_patch.py`）だけが、英語版 ROM と Perfect Crystal 2020 適用済み英語版 ROM、`pokekuristaru` などのツリーを使用します（任意）。

## ワークスペースの設定

スクリプトは `PC_WORKSPACE` 環境変数で指定されたプライベートワークスペースを使用します。未設定の場合はリポジトリルートが使用されますが、実際のビルドには ROM 等のプライベートファイルが必要です。

既定のビルドに必要なレイアウト:

```
$PC_WORKSPACE/
  ├── Pocket Monsters - Crystal Version (Japan).gbc
  └── lazy_ips/
```

歴史的ビルド（任意）は、さらに英語版 ROM、`work/perfect_crystal_ue_patched.gbc`、`pokekuristaru/`、`perfect_crystal_source/` などを同じ固定レイアウトで必要とします（`docs/DEPENDENCIES.md` 参照）。

## 主なコマンド例

```bash
export PC_WORKSPACE=/path/to/private/workspace

# 1. 既定の JPオンリー RC5 ビルド（日本語 ROM と lazy_ips のみを使用）
python3 work/build_rc5_from_jp.py

# 2. 検証済み IPS のパッケージング（release/ に manifest を生成）
python3 work/package_rc5_from_jp.py

# 3. ユーザー所有 ROM への IPS 適用
python3 work/apply_jp_patch.py \
  "$PC_WORKSPACE/Pocket Monsters - Crystal Version (Japan).gbc" \
  --output /path/to/private/output.gbc
```

`build_rc5_from_jp.py` は、入力 ROM のサイズとハッシュを検証し、完全な結果をメモリ上で組み立ててから既知の RC5 出力/IPS ハッシュと照合し、最後に `lazy_ips` での再適用が一致することを確認してから書き出します。間違った入力や結果は最終出力を書き込む前に拒否されます。既存の同一出力は冪等に再生成され、異なる内容が既にある場合は拒否されます。

`package_rc5_from_jp.py` は、`PC_WORKSPACE/work/` のビルド済み ROM/IPS を検証し、`PC_WORKSPACE/work/release/` に `Perfect_Crystal_2020_Japanese_RC5.ips` と `manifest.json`（`rom_size`、`input_sha1`、`input_sha256`、`ips_file`、`ips_sha256`、`output_sha256`）を書き出します。この manifest は `apply_jp_patch.py` がそのまま使用します。

歴史的な参照ビルド（任意）。Hall 装飾品フックも共有レイヤー内の検証済みエミッタ（`work/rc5_defs/hall_hook.py`）が作成するため、`build_hall_hook.sh` と RGBDS は不要です（`work/hall_decorations_hook.asm` からの独立検証にのみ使用します）:

```bash
export PC_WORKSPACE=/path/to/private/workspace

# 0. pokemontools 互換性修正（ディスアセンブルユーティリティを使う場合）
python3 work/prepare_pokemontools.py

# 1. 歴史的 RC5 統合ビルド（英語版参照チェック付き）
python3 work/build_partial_jp_patch.py

# 2. 歴史的パッケージング（CPU 検証レポート等を参照）
python3 work/package_jp_patch.py
```

`work/document_perfect_changes.py` は、リポジトリルートの `PORTING_STATUS.md`（チェックイン済みガイド）をテンプレートとして、実ROMからデータ表と最終生成物のマーカー区間のみを再生成し、`PC_WORKSPACE/work/PORTING_STATUS.md` と `PC_WORKSPACE/work/README_JP.md` を更新します。ただしこのツール自体は、英語版オリジナル/2020適用済みROM、RC4スナップショット、公開ソースツリーを参照する**開発者・参照環境向け**であり、JPオンリーのパッチ生成には不要です。`--update-source` を付けると、再生成結果をチェックイン済みの `PORTING_STATUS.md` にも書き戻します。マーカー区間以外の文章は書き換えません：

```bash
python3 work/document_perfect_changes.py
python3 work/document_perfect_changes.py --update-source
```

## ソースのみの検証

```bash
python3 -m unittest tests/test_source_only.py tests/test_jp_only_build.py
```

## 公開制限

- ROM、画像、音声、オブジェクトファイル、Ghidra プロジェクトなどの著作権/実行資産をリポジトリに追加しないでください。
- 個人を特定できる絶対パス、ホスト名、トークン、メールアドレスをソースに残さないでください。
- 第三者のオープンソースツールやソースツリーは同梱せず、利用者が個別に取得してください。

## 謝辞

- Perfect Crystal 2020 Update: https://github.com/Superegz/Pokemon-Perfect-Crystal
- pokekuristaru: https://github.com/PikalaxALT/pokekuristaru
- pret/pokecrystal: https://github.com/pret/pokecrystal
- pret/pokemon-reverse-engineering-tools: https://github.com/pret/pokemon-reverse-engineering-tools
- lazy_ips: https://github.com/btimofeev/lazy_ips
