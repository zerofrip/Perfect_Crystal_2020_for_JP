# Perfect Crystal 2020 Japanese port

このリポジトリは、『ポケットモンスター クリスタルバージョン』（日本語版）向けに、Perfect Crystal 2020 Update の内容を移植するために、この移植作業で作成したソースコードです。

**本リポジトリには ROM、画像、音声、抽出データ、または第三者のソースツリーは含まれていません。** 必要な入力ファイルと第三者ツールは、利用者がローカル環境で別途準備してください。

## 概要

- ターゲット：日本語版ポケットモンスター クリスタルバージョン
- ベース Perfect Crystal 2020 Update（英語版）の内容を日本語 ROM に移植
- RC5 は RC4 までの全内容を引き継ぎ、グラフィックを日本語原版仕様に戻した版です
- 検証済み RC5 成果物の SHA-256: `b2fbf4f562e0ea2c73758f3862bf70bc5715e751f6e3492b26dd5d353050f5e7`
- 検証済み RC5 IPS の SHA-256: `f000003c68aa41f4ac9358fa454ab4495bc667a7208f35e0510ea8b3d167ce00`

ゲーム内容の変更一覧と遊び方は、**[PORTING_STATUS.md](PORTING_STATUS.md)（プレイヤーズガイド）** を参照してください。

2020 同梱の出現説明と今回指定されたレッド・報酬仕様に合わせて修正を加えます：

- **出現率調整**
  - チコリータ：31番道路 朝 10%（変更なし）
  - ヒノアラシ：くらやみのほらあな（キキョウ側）夜 40%（Lv2 30% + Lv4 10%）
  - ワニノコ：32番道路 昼 20%（Lv7）
  - ゼニガメ：つながりのどうくつ B1F 陸上 朝・昼 各 10%（Lv6）。なみのり中の出現は 40% のまま変更なし
  - カブト：うずまきじま（ルギアの部屋）夜 10%（Lv27）
- **レッドのパーティ**：6 匹全員 Lv100（種族・持ち物・技・個体値・日本語名は維持）
- **殿堂入り装飾品フラグ**：実際に入手可能なアイテム 41 種 + ポスター表示用フラグ 1 個 = 合計 42 フラグ。追加したアイテムはピカチュウのぬいぐるみ（0x2B7）

## RC5 での追加変更

RC5 は、ポケモン・トレーナーの画像を**日本語原版仕様**に戻します：

- 2020 配布版が差し替えていた対象のうち、日本語原版と描き分けられていた**女性スイマー（ビキニのおねえさん）とルージュラの正面画像**を日本語原版に復帰。ルージュラの3枚目のアニメーションフレームと付随する画像の保管域・ポインタも含む
- 5 種の対象トレーナー画像・ルージュラの前後画像・基本画像＋3フレームの描画結果・パレット・アニメーション命令が、すべて日本語原版と一致することを検証済み
- チェックサムを除き、他の RC4 バイトは一切変更なし（RC4 からの差分は 1,100 バイト）

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
│   ├── build_partial_jp_patch.py        RC5 統合ビルダー
│   ├── package_jp_patch.py              検証済み IPS のパッケージング
│   ├── apply_jp_patch.py                ユーザー所有 ROM への IPS 適用
│   ├── prepare_pokemontools.py          pokemontools 互換性修正
│   ├── trainer_party_layout.py          トレーナーデータの再配置ロジック
│   ├── apply_rc4_corrections.py         RC4 補正層
│   ├── apply_japanese_original_sprites.py  RC5 画像復元層
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

# 2. ローカルでの RC5 統合ビルド
python3 work/build_partial_jp_patch.py

# 3. ガイドとドキュメントの生成
python3 work/document_perfect_changes.py

# 4. 検証済み IPS のパッケージング
python3 work/package_jp_patch.py

# 5. ユーザー所有 ROM への IPS 適用
python3 work/apply_jp_patch.py \
  "$PC_WORKSPACE/Pocket Monsters - Crystal Version (Japan).gbc" \
  --output /path/to/private/output.gbc
```

`package_jp_patch.py` は、ビルド済みの `development_only_jp_partial.gbc` / `development_only_jp_partial.ips`、CPU 検証レポート、ドキュメント（`README_JP.md`、`PORTING_STATUS.md`）を `PC_WORKSPACE/work/` から読み込み、パッケージング結果を `PC_WORKSPACE/work/release/` に書き出します。過去のリリース検証には `verify_rc2_release.py` / `verify_rc3_release.py` が `PC_WORKSPACE/work/release/RC1_metadata` および `RC2_metadata` を追加で参照します。これらの入力ファイルはソースオンリーな本リポジトリには含まれていないため、パッケージングにはそれらを別途用意したプライベートワークスペースが必要です。

`work/document_perfect_changes.py` は、リポジトリルートの `PORTING_STATUS.md`（チェックイン済みガイド）をテンプレートとして、実ROMからデータ表と最終生成物のマーカー区間のみを再生成し、`PC_WORKSPACE/work/PORTING_STATUS.md` と `PC_WORKSPACE/work/README_JP.md` を更新します。実行にはビルド済みの RC5 ROM（`development_only_jp_partial.gbc`）が必要です。`--update-source` を付けると、再生成結果をチェックイン済みの `PORTING_STATUS.md` にも書き戻します。マーカー区間以外の文章は書き換えません：

```bash
python3 work/document_perfect_changes.py
python3 work/document_perfect_changes.py --update-source
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
