# Perfect Crystal 2020 Japanese port

このリポジトリは、『ポケットモンスター クリスタルバージョン』（日本語版）向けに、Perfect Crystal 2020 Update の内容を移植するために、この移植作業で作成したソースコードです。

**本リポジトリには ROM、画像、音声、抽出データ、または第三者のソースツリーは含まれていません。** 必要な入力ファイルと第三者ツールは、利用者がローカル環境で別途準備してください。

## 概要

- ターゲット：日本語版ポケットモンスター クリスタルバージョン
- ベース Perfect Crystal 2020 Update（英語版）の内容を日本語 ROM に移植
- RC4 は RC3 に追加修正を適用した版です
- 歴史的 RC3 成果物の SHA-256: `b6f6b73dc7e6d8f4d3223b398fb1202519efae0c0e36959ab7ac43cb8e5a4c21`
- 検証済み RC4 成果物の SHA-256: `f7a0da3b9df33d4d010b05d82c8e6644d09ebd9c42320cc1ee89d4e2fd20ddd6`
- 検証済み RC4 IPS の SHA-256: `9f824af58ad219a6b5c8ddde0306e17e81b29723a3c7ffd1db90343039a83b3c`
- 歴史的 RC2 成果物の SHA-256: `96b08ba49bc42096b2156a6795c86f1b47f40afe8786a6569da764d8c493163c`
- 歴史的 RC1 成果物の SHA-256: `bdb8b08177dc6e5a549c5d3ed2499a9835ae7c7c01ad0acafda659072335805e`

## RC4 での追加変更

RC4 は、2020 同梱の出現説明と今回指定されたレッド・報酬仕様に合わせて修正を加えます：

- **出現率調整**
  - チコリータ：31番道路 朝 10%（変更なし）
  - ヒノアラシ：くらやみのほらあな（キキョウ側）夜 40%（Lv2 30% + Lv4 10%）
  - ワニノコ：32番道路 昼 20%（Lv7）
  - ゼニガメ：つながりのどうくつ B1F 陸上 朝・昼 各 10%（Lv6）。なみのり中の出現は 40% のまま変更なし
  - カブト：うずまきじま（ルギアの部屋）夜 10%（Lv27）
- **レッドのパーティ**：6 匹全員 Lv100（種族・持ち物・技・個体値・日本語名は維持）
- **殿堂入り装飾品フラグ**：実際に入手可能なアイテム 41 種 + ポスター表示用フラグ 1 個 = 合計 42 フラグ。追加したアイテムはピカチュウのぬいぐるみ（0x2B7）

## ソース構成

```
.
├── LICENSE                              Apache 2.0
├── README.md                            このファイル
├── requirements.txt                     Python 依存関係（オプション含む）
├── .gitignore                           追跡禁止ファイルの定義
├── work/                                主要な Python スクリプト
│   ├── pc_env.py                        ワークスペース解決ヘルパー
│   ├── build_partial_jp_patch.py        RC4 統合ビルダー
│   ├── package_jp_patch.py              検証済み IPS のパッケージング
│   ├── apply_jp_patch.py                ユーザー所有 ROM への IPS 適用
│   ├── prepare_pokemontools.py          pokemontools 互換性修正
│   ├── trainer_party_layout.py          トレーナーデータの再配置ロジック
│   ├── apply_rc4_corrections.py         RC4 補正層
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
    └── test_source_only.py              ソースのみの健全性チェック
```

## 動作に必要な環境

- Python 3.11 以上（開発時は Python 3.14.4 でテスト済み）
- 利用者が所有する日本語版 Crystal ROM（SHA-1: `95127b901bbce2407daf43cce9f45d4c27ef635d`）
- 同じく利用者が所有する英語版 Crystal ROM V1.1（SHA-1: `f2f52230b536214ef7c9924f483392993e226cfb`）
- Perfect Crystal 2020 Update 適用済み英語版 ROM（SHA-1: `dd00b737fbd18d2e8ae064097a36e8fd4b16855d`）
- 以下の第三者ツリー/ライブラリ（詳細は `docs/DEPENDENCIES.md`）
  - `lazy_ips`（ルート直下）
  - `pokemon-reverse-engineering-tools`（`work/` 直下）
  - `pokekuristaru`（ルート直下、マップ名・charmap・tileset 参照に必須）
  - `perfect_crystal_source`（ルート直下、マップ名参照に必須）
  - `rgbds-0.2.5`（Hall Decoration Hook のビルドに必須）

## ワークスペースの設定

スクリプトは `PC_WORKSPACE` 環境変数で指定されたプライベートワークスペースを使用します。未設定の場合はリポジトリルートが使用されますが、実際のビルドには ROM 等のプライベートファイルが必要です。

依存関係は固定の相対レイアウトで解決されます。

```
$PC_WORKSPACE/
  ├── Pocket Monsters - Crystal Version (Japan).gbc
  ├── Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc
  ├── lazy_ips/
  ├── pokekuristaru/
  ├── perfect_crystal_source/
  ├── rgbds-0.2.5/
  └── work/
        ├── perfect_crystal_ue_patched.gbc
        └── pokemon-reverse-engineering-tools/
```

RGBDS のみ `PC_RGBDS` 環境変数で別のパスを指定できます。

## 主なコマンド例

```bash
export PC_WORKSPACE=/path/to/private/workspace
export PC_RGBDS=/path/to/rgbds-0.2.5

# 0. pokemontools 互換性修正（ディスアセンブルユーティリティを使う場合）
python3 work/prepare_pokemontools.py

# 1. Hall Decoration Hook のビルド（メインビルドより先に実施）
bash work/build_hall_hook.sh

# 2. ローカルでの RC4 統合ビルド
python3 work/build_partial_jp_patch.py

# 3. 検証済み IPS のパッケージング
python3 work/package_jp_patch.py

# 4. ユーザー所有 ROM への IPS 適用
python3 work/apply_jp_patch.py \
  "$PC_WORKSPACE/Pocket Monsters - Crystal Version (Japan).gbc" \
  --output /path/to/private/output.gbc
```

`package_jp_patch.py` は、ビルド済みの `development_only_jp_partial.gbc` / `development_only_jp_partial.ips`、CPU 検証レポート、ドキュメント（`README_JP.md`、`PORTING_STATUS.md`）を `PC_WORKSPACE/work/` から読み込み、パッケージング結果を `PC_WORKSPACE/work/release/` に書き出します。過去のリリース検証には `verify_rc2_release.py` / `verify_rc3_release.py` が `PC_WORKSPACE/work/release/RC1_metadata` および `RC2_metadata` を追加で参照します。これらの入力ファイルはソースオンリーな本リポジトリには含まれていないため、パッケージングにはそれらを別途用意したプライベートワークスペースが必要です。

`work/document_perfect_changes.py` は `PC_WORKSPACE/work/PORTING_STATUS.md` と `README_JP.md` を更新します。実行にはビルド済みの RC4 ROM（`development_only_jp_partial.gbc`）が必要です：

```bash
python3 work/document_perfect_changes.py
```

## ソースのみの検証

```bash
python3 -m unittest tests/test_source_only.py
```

## 公開制限

- ROM、画像、音声、オブジェクトファイル、Ghidra プロジェクトなどの著作権/実行資産をリポジトリに追加しないでください。
- 個人を特定できる絶対パス、ホスト名、トークン、メールアドレスをソースに残さないでください。
- 検証済みバイナリの SHA-256 値は文書化できますが、バイナリ自体は一切公開しないでください。
- 第三者のオープンソースツールやソースツリーは同梱せず、利用者が個別に取得してください。

## 謝辞

- Perfect Crystal 2020 Update: https://github.com/Superegz/Pokemon-Perfect-Crystal
- pokekuristaru: https://github.com/PikalaxALT/pokekuristaru
- pret/pokecrystal: https://github.com/pret/pokecrystal
- pret/pokemon-reverse-engineering-tools: https://github.com/pret/pokemon-reverse-engineering-tools
- lazy_ips: https://github.com/btimofeev/lazy_ips
