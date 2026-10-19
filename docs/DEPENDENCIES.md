# 依存関係の準備方法

このリポジトリは、第三者リソースを同梱せず、利用者が個別に取得・配置します。

既定のビルド（`work/build_rc5_from_jp.py`）に必要なのは **lazy_ips と日本語版 ROM だけ** です。それ以外のツリー（公開逆アセンブリ、RGBDS など）は歴史的な参照ビルドや監査ツールのための任意依存です。

## 必須（既定の JPオンリー ビルド）

### 1. lazy_ips

IPS パッチの作成と再適用検証に使用します。

```bash
git clone https://github.com/btimofeev/lazy_ips.git "$PC_WORKSPACE/lazy_ips"
```

- 参照コミット: `2a4918b4b0a4ad9bb139c2907c00decfa0cf9188`

さらに、利用者が所有する日本語版 Crystal ROM を `$PC_WORKSPACE/Pocket Monsters - Crystal Version (Japan).gbc` に配置します。既定のビルドは `PC_WORKSPACE` 内の固定された相対パスで解決され、それ以外の入力（英語版 ROM、2020 年版 IPS、過去のスナップショット、CPU 検証レポート、`pokekuristaru` などの公開ソースツリー）は一切読みません。

## 任意（歴史的参照ビルド・監査用）

`work/build_partial_jp_patch.py`（英語版参照チェック付きの歴史的統合ビルダー）と `work/package_jp_patch.py`（CPU 検証レポートを参照する歴史的パッケージング）を使用する場合のみ必要です。`PC_WORKSPACE` 以外の個別パス上書きは `PC_RGBDS` のみです。

```
$PC_WORKSPACE/
  ├── lazy_ips/
  ├── pokekuristaru/
  ├── perfect_crystal_source/
  ├── rgbds-0.2.5/
  └── work/
        └── pokemon-reverse-engineering-tools/
```

### 2. pokemon-reverse-engineering-tools (pokemontools)

GBZ80 逆アセンブルや LZ77 伸長などに使用します。`work/` 直下に配置します。

```bash
git clone https://github.com/pret/pokemon-reverse-engineering-tools.git \
    "$PC_WORKSPACE/work/pokemon-reverse-engineering-tools"
```

- 参照コミット: `652269b739710f873d3def461aa2aa36db9e68da`

### 3. pokekuristaru

日本語版 Crystal のラベル、charmap、tileset 定義の参照。歴史的参照ビルドの検証と `map_layout.py` の完全なマップ名解決で使用します（既定ビルドでは同梱の `work/rc5_defs/` 定義を使用するため不要）。

```bash
git clone https://github.com/PikalaxALT/pokekuristaru.git "$PC_WORKSPACE/pokekuristaru"
```

- 参照コミット: `2fb3ee8f8c06aeaa89c37defbea8b85466f61260`

### 4. perfect_crystal_source

Perfect Crystal 2020 Update のマップ名などの参照。歴史的参照ビルドで使用します。

```bash
git clone https://github.com/Superegz/Pokemon-Perfect-Crystal.git \
    "$PC_WORKSPACE/perfect_crystal_source"
```

- 参照コミット: `9ceb36e6cb1984b8ee1ac7378b5d366ff0705317`

### 5. RGBDS 0.2.5

`work/hall_decorations_hook.asm` のビルドに使用します。歴史的参照ビルドでも、フックと同じ機械語を共有レイヤー内の検証済みエミッタ（`work/rc5_defs/hall_hook.py`）が作成するため**不要**です。RGBDS によるビルドは、生成フックをアセンブリと照合する独立検証にのみ使用します。

```bash
export PC_RGBDS=/path/to/rgbds-0.2.5
bash work/build_hall_hook.sh
```

新しいバージョンでも構文が互換であれば動作しますが、生成バイナリの同一性は保証されません。

### 6. gb-asm-tools

銀行単位の差分ツール（`gbdiff.sh`）。`verify_rc2_release.py` / `verify_rc3_release.py` で使用します。

- 参照コミット: `5ff0fead255a093d33baddb46c77a4943bb929d7`

### 7. pokecrystal (pret)

ベースライン比較用の英語版ポケットモンスター クリスタルソースです。

```bash
git clone https://github.com/pret/pokecrystal.git "$PC_WORKSPACE/pokecrystal"
```

- 参照コミット: `3bc8daa4173e96a7f4011dad3922eb6fa5dad5c6`

## Python ライブラリ

```bash
python3 -m pip install -r requirements.txt
```

`pokemontools` は pip パッケージとして配布されていないため、上記の git clone と `PYTHONPATH` による解決を推奨します。`work/prepare_pokemontools.py` は、ディスアセンブルユーティリティを Python 3 で動作させるための最小限の互換性修正を行います（既定ビルドの IPS 生成には不要です）。
