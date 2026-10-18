# 依存関係の準備方法

このリポジトリは、以下の第三者リソースを必要とします。いずれもリポジトリには同梱せず、利用者が個別に取得・配置してください。

すべての依存関係は `PC_WORKSPACE` 環境変数で指定されたディレクトリ内の固定された相対パスで解決されます。`PC_WORKSPACE` 以外の個別パス上書きはありません。

```
$PC_WORKSPACE/
  ├── lazy_ips/
  ├── pokekuristaru/
  ├── perfect_crystal_source/
  ├── rgbds-0.2.5/
  └── work/
        └── pokemon-reverse-engineering-tools/
```

## 必須（メインビルド）

### 1. lazy_ips

IPS パッチの作成・適用に使用します。

```bash
git clone https://github.com/btimofeev/lazy_ips.git "$PC_WORKSPACE/lazy_ips"
```

- 参照コミット: `2a4918b4b0a4ad9bb139c2907c00decfa0cf9188`

### 2. pokemon-reverse-engineering-tools (pokemontools)

GBZ80 逆アセンブルや LZ77 伸長などに使用します。`work/` 直下に配置します。

```bash
git clone https://github.com/pret/pokemon-reverse-engineering-tools.git \
    "$PC_WORKSPACE/work/pokemon-reverse-engineering-tools"
```

- 参照コミット: `652269b739710f873d3def461aa2aa36db9e68da`

### 3. pokekuristaru

日本語版 Crystal のラベル、charmap、tileset 定義などを参照します。`map_layout.py` と `japanese_text.py` で必須です。

```bash
git clone https://github.com/PikalaxALT/pokekuristaru.git "$PC_WORKSPACE/pokekuristaru"
```

- 参照コミット: `2fb3ee8f8c06aeaa89c37defbea8b85466f61260`

### 4. perfect_crystal_source

Perfect Crystal 2020 Update のマップ名などを参照します。`map_layout.py` で必須です。

```bash
git clone https://github.com/Superegz/Pokemon-Perfect-Crystal.git \
    "$PC_WORKSPACE/perfect_crystal_source"
```

- 参照コミット: `9ceb36e6cb1984b8ee1ac7378b5d366ff0705317`

### 5. RGBDS 0.2.5

`work/hall_decorations_hook.asm` のビルドに必要です。`PC_RGBDS` 環境変数で別のパスを指定できます。

```bash
export PC_RGBDS=/path/to/rgbds-0.2.5
bash work/build_hall_hook.sh
```

新しいバージョンでも構文が互換であれば動作しますが、生成バイナリの同一性は保証されません。

## 任意（参考・比較用）

### 6. gb-asm-tools

銀行単位の差分ツール（`gbdiff.sh`）に使用されます。`verify_rc2_release.py` および `verify_rc3_release.py` で使用します。

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

`pokemontools` は pip パッケージとして配布されていないため、上記の git clone と `PYTHONPATH` による解決を推奨します。`work/prepare_pokemontools.py` は、ディスアセンブルユーティリティを Python 3 で動作させるための最小限の互換性修正を行います（メインビルドの LZ 伸縮には不要です）。
