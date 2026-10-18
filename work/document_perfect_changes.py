"""Extract documentation tables from local stock/released ROMs; never modify ROMs.

RC4 tables are generated from the corrected current ROM (development_only_jp_partial.gbc)
rather than from the English 2020 ROM, so the documented differences match what the
Japanese player actually sees.  Prices and marts are unchanged by RC4 and are still
read from the English stock / 2020-patched pair.
"""
from collections import Counter
from hashlib import sha1, sha256
import json
from pathlib import Path
import re

from dialogue_mapping import japanese_chars
from map_layout import ROOT, map_names
from trainer_party_layout import trainer_groups

WORK = ROOT / 'work'
RELEASE = WORK / 'release'
RELEASE.mkdir(exist_ok=True)

jp = (ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
ue = (ROOT / 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
pc = (WORK / 'perfect_crystal_ue_patched.gbc').read_bytes()
current = (WORK / 'development_only_jp_partial.gbc').read_bytes()
ips = (WORK / 'development_only_jp_partial.ips').read_bytes()
assert sha1(jp).hexdigest() == '95127b901bbce2407daf43cce9f45d4c27ef635d'
assert sha1(ue).hexdigest() == 'f2f52230b536214ef7c9924f483392993e226cfb'
assert sha1(pc).hexdigest() == 'dd00b737fbd18d2e8ae064097a36e8fd4b16855d'

# Cumulative thresholds and slot indices, checked in all actual inputs.
probabilities = bytes.fromhex('1e003c0250045a065f08630a640c3c005a026404')
for rom in (jp, ue, pc, current):
    assert rom.count(probabilities) == 1, 'wild encounter slot weights differ'
chars = japanese_chars()
chars.update({0x50: '', 0xeb: 'ェ', 0xf4: 'ォ', 0xef: '♂', 0xf5: '♀'})


def decode(data, katakana=False):
    text = ''.join(chars.get(b, f'<{b:02x}>') for b in data.split(b'\x50')[0])
    if katakana:
        text = ''.join(chr(ord(c) + 0x60) if 'ぁ' <= c <= 'ゖ' else c for c in text)
    return text


species = {i + 1: decode(jp[0x5341a + i * 5:0x5341a + (i + 1) * 5], True) for i in range(251)}
assert [species[i] for i in (1, 2, 3, 151, 251)] == ['フシギダネ', 'フシギソウ', 'フシギバナ', 'ミュウ', 'セレビィ']


def strings(offset, count):
    names = {}
    for i in range(1, count + 1):
        end = jp.index(0x50, offset)
        names[i] = decode(jp[offset:end])
        offset = end + 1
    return names


items = strings(0x70fa, 256)
moves = strings(0x4163b, 251)
classes = strings(0x2d319, 67)
for key, value in list(classes.items()):
    classes[key] = value.replace('ジムりーダー', 'ジムリーダー').replace('エりート', 'エリート').replace('ギタりスト', 'ギタリスト')
items[0] = 'なし'
moves[0] = 'なし'
for key, value in list(items.items()):
    items[key] = value.replace('りーフ', 'リーフ').replace('りカバー', 'リカバー').replace('ラブりー', 'ラブリー').replace('みずたまりボン', 'みずたまリボン')
tm_number = 0
for line in (ROOT / 'pokekuristaru/constants/item_constants.asm').read_text().splitlines():
    match = re.match(r'\s*add_tm\s+\w+\s*;\s*\$([0-9A-F]+)', line)
    if match:
        tm_number += 1
        items[int(match[1], 16)] = f'わざマシン{tm_number:02d}'

locations = map_names(True)

# Wild encounters: compare Japanese stock to the corrected current ROM.
# (table, jp_old_start, current_start, old_count, new_count, width)
wild = []
for table, jstart, cstart, old_count, new_count, width in (
    ('ジョウト陸上', 0x2a60c, 0x2a60c, 61, 61, 47),
    ('ジョウト水上', 0x2b140, 0x2b140, 38, 38, 9),
    ('カントー陸上', 0x2b297, 0x2b297, 30, 33, 47),
    ('カントー水上', 0x2b81a, 0x2bd04, 24, 26, 9),
):
    # Terminator follows each table in both ROMs.
    assert jp[jstart + old_count * width] == 0xff
    assert current[cstart + new_count * width] == 0xff
    before = {tuple(jp[jstart + i * width:jstart + i * width + 2]):
              jp[jstart + i * width:jstart + (i + 1) * width] for i in range(old_count)}
    for i in range(new_count):
        row = current[cstart + i * width:cstart + (i + 1) * width]
        key = tuple(row[:2])
        old = before.get(key)
        if old == row:
            continue
        modes = range(3) if width == 47 else range(1)
        for mode in modes:
            count_slots = 7 if width == 47 else 3
            header = 5 if width == 47 else 3
            index = header + mode * count_slots * 2
            rates = (30, 30, 20, 10, 5, 4, 1) if width == 47 else (60, 30, 10)

            def group(record):
                if record is None:
                    return []
                totals = Counter()
                for slot, chance in enumerate(rates):
                    level, mon = record[index + 2 * slot:index + 2 * slot + 2]
                    totals[(mon, level)] += chance
                return [dict(species=species[mon], level=level, percent=chance) for (mon, level), chance in totals.items()]

            oldslots = old[index:index + 2 * count_slots] if old else None
            changed = oldslots != row[index:index + 2 * count_slots] or (old is not None and old[2 + mode] != row[2 + mode])
            if changed:
                wild.append(dict(table=table, map=locations[key], mode=('朝', '昼', '夜')[mode] if width == 47 else '全時間帯',
                                 old_rate=old[2 + mode] if old else None, new_rate=row[2 + mode], old=group(old), new=group(row)))

# Prices and marts are unchanged by RC4; read from the English stock / 2020-patched pair.
prices = []
for item in range(1, 256):
    old = ue[0x67c1 + (item - 1) * 7:0x67c1 + item * 7]
    new = pc[0x67a7 + (item - 1) * 7:0x67a7 + item * 7]
    if old[:2] != new[:2]:
        prices.append(dict(id=item, name=items[item], old=int.from_bytes(old[:2], 'little'), new=int.from_bytes(new[:2], 'little')))
assert len(prices) == 11

marts = []
for number in range(34):
    def mart(rom, table):
        off = int.from_bytes(rom[table + number * 2:table + number * 2 + 2], 'little') + 0x10000
        return list(rom[off + 1:off + 1 + rom[off]])

    old, new = mart(jp, 0x164c3), mart(pc, 0x160a9)
    if old != new:
        marts.append(dict(id=number, old=[items[i] for i in old], new=[items[i] for i in new],
                          added=[items[i] for i in new if i not in old], removed=[items[i] for i in old if i not in new]))
assert [m['id'] for m in marts] == [5, 23, 25, 26]

# Trainers: compare Japanese stock to the corrected current ROM.
jgroups = trainer_groups(jp, 0x399ba, 0x3b700)
cgroups = trainer_groups(current, 0x399ba, 0x3b775)
trainerset = []


def party(rom, record):
    _, _, kind, width, members = record
    result = []
    for off in members:
        level, mon = rom[off:off + 2]
        pos = off + 2
        item = rom[pos] if kind & 2 else 0
        if kind & 2:
            pos += 1
        moveset = list(rom[pos:pos + 4]) if kind & 1 else None
        result.append(dict(species=species[mon], level=level, item=items[item],
                           moves=[moves[i] for i in moveset] if moveset is not None else None))
    return result


for g, (jg, cg) in enumerate(zip(jgroups, cgroups), 1):
    for t, (jr, cr) in enumerate(zip(jg, cg), 1):
        old, new = party(jp, jr), party(current, cr)
        if old == new and jr[2] == cr[2]:
            continue
        name = decode(jp[jr[0]:jr[1]], True)
        trainerset.append(dict(group=g, trainer_class=classes[g], index=t, name=name,
                               old=old, new=new, old_type=jr[2], new_type=cr[2]))
assert len(trainerset) == 212

leaders = []
for g in (1, 3, 2, 4, 7, 6, 5, 8, 17, 18, 19, 21, 26, 35, 46, 64):
    record = jgroups[g - 1][0]
    leaders.append(dict(name=decode(jp[record[0]:record[1]], True), party=party(current, cgroups[g - 1][0])))

result = dict(wild=wild, prices=prices, marts=marts, trainers=trainerset, leaders=leaders,
              species=species, items=items, moves=moves)
(WORK / 'perfect_2020_documentation_data.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')

MAP_JA = {
    'BurnedTowerB1F': 'やけたとう B1F',
    'CeruleanCave1F': 'ハナダのどうくつ 1F',
    'CeruleanCave2F': 'ハナダのどうくつ 2F',
    'CeruleanCaveB1': 'ハナダのどうくつ B1F',
    'DarkCaveVioletEntrance': 'くらやみのほらあな（キキョウ側）',
    'IcePathB3F': 'こおりのぬけみち B3F',
    'IlexForest': 'ウバメのもり',
    'Route10North': '10番道路（北側・発電所付近）',
    'SilverCaveItemRooms': 'シロガネやま（道具のある小部屋）',
    'SilverCaveOutside': 'シロガネやま入口の屋外',
    'SilverCaveRoom1': 'シロガネやま（第1の洞窟）',
    'SilverCaveRoom2': 'シロガネやま（第2の洞窟）',
    'SilverCaveRoom3': 'シロガネやま頂上（レッドの部屋）',
    'TinTower2F': 'スズのとう 2F',
    'UnionCaveB1F': 'つながりのどうくつ B1F',
    'WhirlIslandB2F': 'うずまきじま B2F',
    'WhirlIslandLugiaChamber': 'うずまきじま（ルギアの部屋）',
}
for row in wild:
    if re.fullmatch(r'Route\d+', row['map']):
        MAP_JA[row['map']] = row['map'][5:] + '番道路'
assert all(row['map'] in MAP_JA for row in wild)
assert len(wild) == 66 and len(set(row['map'] for row in wild)) == 27


def describe(mon):
    text = f"{mon['species']} Lv{mon['level']}"
    if mon['item'] != 'なし':
        text += f"（{mon['item']}）"
    return text


def encounters(entries):
    return '、'.join(f"{e['species']} Lv{e['level']}：{e['percent']}%" for e in entries) if entries else '新規追加'


lines = ['## データ変更の全一覧', '',
         '以下の表は、ローカルの日本語原版と**RC4 修正済み日本語 ROM**から抽出した値です。',
         '英語 2020 配布版との差異は、RC4 で意図的に上書きした野生出現率・レッドのレベル・殿堂入り装飾品フラグを除き、',
         '2020 配布版の移植内容と一致しています。',
         '種族・道具・技・トレーナー名も日本語原版から復号しています。', '',
         '### RC4 で追加した実ゲーム補正', '',
         '| 項目 | 内容 |',
         '|---|---|',
         '| 野生出現率 | チコリータ 31番道路 朝 10%（維持）、ヒノアラシ くらやみのほらあな（キキョウ側）夜 40%、ワニノコ 32番道路 昼 20%、ゼニガメ つながりのどうくつ B1F 朝・昼 各 10%（なみのり中は 40% のまま）、カブト うずまきじま（ルギアの部屋）夜 10% |',
         "| レッド | 6 匹全員 Lv100（種族・持ち物・技・個体値・日本語名は 2020 版維持） |",
         '| 殿堂入り装飾品 | 実際に入手可能なアイテム 41 種 + ポスター表示用フラグ 1 個 = 合計 42 フラグ。追加はピカチュウのぬいぐるみ（0x2B7） |',
         '',
         '### 店の全商品（変更された4売場）', '',
         '| 売場 | 原版の商品 | 2020版で追加する商品 |',
         '|---|---|---|']
shops = {5: 'コガネデパート2F・薬売場', 23: 'タマムシデパート2F・薬売場', 25: 'タマムシデパート3F', 26: 'タマムシデパート4F'}
for row in marts:
    assert not row['removed']
    lines.append(f"| {shops[row['id']]} | {'、'.join(row['old'])} | {'、'.join(row['added'])} |")
lines += ['', '原版の商品と追加商品を合わせたものが2020版の全在庫です。わざマシン09は「じこあんじ」、10は「めざめるパワー」、11は「にほんばれ」、17は「まもる」、18は「あまごい」、37は「すなあらし」。', '',
          '### 基本価格の全変更11件', '',
          '| 道具 | 原版 | 2020版 |', '|---|---:|---:|']
for row in prices:
    lines.append(f"| {row['name']} | {row['old']:,}円 | {row['new']:,}円 |")
lines += ['', '原版の0円や10円は、売場での販売実績ではなく道具データに保存されていた基本価格です。', '',
          '### ジムリーダー16人の初戦・再戦パーティ', '',
          '再戦も初戦と同じ編成です。持ち物の記載がない個体は持ち物なし。', '',
          '| リーダー | 2020版のパーティ（登場順） |', '|---|---|']
for row in leaders:
    lines.append(f"| {row['name']} | {'、'.join(describe(m) for m in row['party'])} |")

lines += ['', '### 野生出現の全変更表（27マップ・66行）', '',
          '確率は**野生ポケモンに遭遇したときの種族・レベルの選択割合**で、1歩ごとの遭遇率ではありません。',
          '陸上は草むら・洞窟床など、水上はなみのり中の遭遇です。水上表には朝昼夜の区別がありません。',
          '同じ種族・レベルの複数枠は合算。変化した時間帯／方法だけを掲載し、行内では変更前後の全出現枠を示します。',
          '原版に存在しないハナダのどうくつの行は「新規追加」と表記。固定Lv70ミュウツーはこの野生抽選表とは別です。', '',
          '<details>', '<summary>全66行を開く</summary>', '',
          '| 場所 | 方法・時間 | 原版 | RC4版 |', '|---|---|---|---|']
for row in wild:
    assert sum(e['percent'] for e in row['new']) == 100
    assert not row['old'] or sum(e['percent'] for e in row['old']) == 100
    method = '陸上' if '陸上' in row['table'] else '水上'
    oldtext = encounters(row['old'])
    newtext = encounters(row['new'])
    if row['old_rate'] is not None and row['old_rate'] != row['new_rate']:
        oldtext += f"（遭遇率データ {row['old_rate']}）"
        newtext += f"（遭遇率データ {row['new_rate']}）"
    lines.append(f"| {MAP_JA[row['map']]} | {method}・{row['mode']} | {oldtext} | {newtext} |")
lines += ['', '</details>', '',
          '### トレーナーの全変更表（212レコード）', '',
          '各行は1つの編成データです。同じ人物の電話再戦・御三家による分岐なども別レコードとして数えます。',
          '「編成」はクラス番号-クラス内編成番号、「n匹目」は手持ちの登場順です。記載のない項目は原版と同じです。',
          'ライバルの「?」はデータ内の仮名で、ゲーム画面ではプレイヤーが付けた名前になります。',
          '技の「自動設定」は種族・レベルから技を決める形式。通常トレーナーのレベル上昇に伴う自動技の変化もこの形式に従います。',
          '個別の持ち物指定と、戦闘中にトレーナーが使う回復道具は別の仕組みです。',
          'レッドのレベルは RC4 で全員 Lv100 に変更されています（種族・持ち物・技・個体値は 2020 版維持）。', '',
          '<details>', '<summary>全212レコードを開く</summary>', '',
          '| トレーナー | 編成 | パーティデータの変更 |', '|---|---:|---|']
from itertools import zip_longest
for row in trainerset:
    changes = []
    for slot, (old, new) in enumerate(zip_longest(row['old'], row['new']), 1):
        prefix = f'{slot}匹目：'
        if old is None:
            changes.append(prefix + '追加 ' + describe(new) + '、技 ' + ('／'.join(new['moves']) if new['moves'] is not None else '自動設定'))
            continue
        if new is None:
            changes.append(prefix + '削除 ' + describe(old) + '、技 ' + ('／'.join(old['moves']) if old['moves'] is not None else '自動設定'))
            continue
        delta = []
        if old['species'] != new['species']:
            delta.append(f"{old['species']} → {new['species']}")
        if old['level'] != new['level']:
            delta.append(f"Lv{old['level']} → Lv{new['level']}")
        if old['item'] != new['item']:
            delta.append(f"持ち物 {old['item']} → {new['item']}")
        if old['moves'] != new['moves']:
            a = '／'.join(old['moves']) if old['moves'] is not None else '自動設定'
            b = '／'.join(new['moves']) if new['moves'] is not None else '自動設定'
            delta.append(f'技 {a} → {b}')
        if delta:
            species_prefix = (old['species'] + ' ') if old['species'] == new['species'] else ''
            changes.append(prefix + species_prefix + '、'.join(delta))
    if not changes:
        assert row['old_type'] != row['new_type']
        changes.append('技・持ち物の指定形式を変更（具体値は同じ）')
    lines.append(f"| {row['trainer_class']}／{row['name']} | {row['group']}-{row['index']} | {'<br>'.join(changes)} |")
lines += ['', '</details>', '']

table = '\n'.join(lines)
assert not re.search(r'<[0-9a-f]{2}>', table), 'undecoded name byte'
start = '<!-- perfect-2020-data:start -->'
end = '<!-- perfect-2020-data:end -->'
status_path = WORK / 'PORTING_STATUS.md'
status = status_path.read_text()
assert status.count(start) == status.count(end) == 1
status = status.split(start)[0] + start + '\n\n' + table + '\n' + end + status.split(end)[1]

# Bounded prose replacements for RC4.  Replacements are idempotent: if the new
# text is already present, no action is taken.  Key anchors are asserted so
# that a stale template fails loudly instead of silently skipping.
def _replace(text, old, new, required=False):
    if new in text:
        return text
    if old in text:
        return text.replace(old, new, 1)
    if required:
        raise RuntimeError(f'required prose pattern not found: {old[:80]!r}')
    print('document_warning', 'pattern not found', old[:60].replace('\n', ' '))
    return text


# Intro section: replace the two paragraphs between the section heading and ### 1.
_intro_old = (
    'この節はゲーム内容の変更一覧です。比較対象は日本語版の原本、仕様の基準は**配布された「Pokemon Perfect Crystal (2020 Update).ips」を英語UE v1.1へ適用した実ROM**です。'
    '公開リポジトリの旧版説明と異なる場合は、実際の2020配布版を優先しています。隠しポケモンの場所や報酬のネタバレを含みます。'
)
_intro_new = (
    'この節はゲーム内容の変更一覧です。比較対象は日本語版の原本です。'
    '2020配布版の戦闘バグ修正・ジム再戦・マート・価格などは配布された「Pokemon Perfect Crystal (2020 Update).ips」を英語UE v1.1へ適用した実ROMを正とします。'
    'RC4では、2020同梱の出現説明と今回指定されたレッド・報酬仕様を優先し、御三家・カブトの出現率、レッドのレベル、殿堂入り装飾品フラグを追加修正しています。'
    '隠しポケモンの場所や報酬のネタバレを含みます。'
)
status = _replace(status, _intro_old, _intro_new)

_historical_intro = (
    '以下の1〜11節とデータ表は2020配布版・RC1の仕様記録です。'
    '追加修正後の現在の挙動は「RC2で追加修正した4項目」と「RC3で修正した持ち物の999上限」を参照してください。'
)
status = _replace(
    status,
    _historical_intro,
    '以下の1〜11節とデータ表は、2020配布版・RC1からRC4までの仕様記録です。'
    '各節では変更の背景と、日本語版への移植方法を示します。'
    '出現率・レッド・殿堂入り報酬はRC4の内容、戦闘バグ修正5件はRC2・RC3の内容を反映しています。'
)

status = _replace(
    status,
    '**現行版はRC3**です。RC2のムーンボール・りゅうのキバ・コイキングの長さ比較・2段階能力低下に加え、RC3で持ち物補正後の999上限を修正しています。',
    '**現行版はRC4**です。RC2のムーンボール・りゅうのキバ・コイキングの長さ比較・2段階能力低下、RC3の持ち物補正後の999上限に加え、RC4で御三家・カブトの野生出現率・レッドのレベル・殿堂入り装飾品フラグを修正しています。'
)

status = _replace(
    status,
    '殿堂入りで模様替え品40種＋表示フラグ1個、レッド勝利で5種の報酬',
    '殿堂入りで模様替え品41種＋表示フラグ1個（計42フラグ）、レッド勝利でピカチュウを含む5種の所持フラグを設定'
)

# The four old bullets are single lines in the original excerpt.
status = _replace(
    status,
    '- **出現率・場所**：旧公開READMEの御三家1%などをそのまま採用しない。実ROMでは、チコリータは31番道路の朝10%、ヒノアラシはくらやみのほらあな・キキョウ側の夜31%（Lv2が30%＋Lv4が1%）、ワニノコは32番道路の昼4%。2020同梱テキストにもヒノアラシ40%・ワニノコ20%とあるが、実ROMの出現枠と一致しない。',
    '- **出現率・場所**：2020同梱説明に従い、チコリータ31番道路朝10%、ヒノアラシくらやみのほらあな（キキョウ側）夜40%（Lv2 30%＋Lv4 10%）、ワニノコ32番道路昼20%、ゼニガメつながりのどうくつB1F陸上朝昼各10%（なみのりは40%のまま）、カブトうずまきじま（ルギアの部屋）夜10%とする。'
)
status = _replace(
    status,
    '- **その他の同梱説明との差**：ゼニガメはつながりのどうくつB1Fの陸上・朝昼で5%（同梱説明10%）、水上は40%。カブトはルギアの部屋の陸上・夜で5%（同梱説明10%）。全値は下表を基準にする。',
    '- **その他の同梱説明との差**：ゼニガメはつながりのどうくつB1Fの陸上・朝昼で10%、水上は40%。カブトはルギアの部屋の陸上・夜で10%。戦闘バグ修正・ジム再戦・マート・価格は2020 IPS実データを正とする。'
)
status = _replace(
    status,
    '- **レッド**：全員Lv100ではなく、上記のLv73〜81の編成。',
    '- **レッド**：RC4で6匹全員Lv100に変更（種族・持ち物・技・個体値・日本語名は2020版維持）。'
)
status = _replace(
    status,
    '- **殿堂入り報酬**：「41品」ではなく40品＋表示フラグ1個。',
    '- **殿堂入り報酬**：41品＋表示フラグ1個＝42フラグ。追加したアイテムはピカチュウのぬいぐるみ（0x2B7）。'
)

# Section 11 intro: update to reflect that encounters/Red/rewards are RC4,
# while the five battle items below are pre-RC4 history.
section11_old = (
    'この節は2020配布版・RC1に残っていた挙動の記録です。'
)
section11_new = (
    'この節は旧版との差異と現在の修正状況を記録しています。'
    '出現率・レッド・報酬はRC4で修正済み、戦闘バグ修正5件はRC2・RC3で修正済みです。'
    '以下の5項目は修正前の記録です。'
)
status = _replace(status, section11_old, section11_new)

# Red section: replace from the heading through the table up to ### 3.
red_old_heading = '**2020配布版のレッドは全員Lv100ではない。**'
red_new_heading = '**RC4 のレッドは全員 Lv100。**'
red_new_table = '''**RC4 のレッドは全員 Lv100。** 種族・追加された持ち物・技・個体値・日本語名は 2020 版を維持する。

| ポケモン | レベル | 追加された持ち物 |
|---|---:|---|
| ピカチュウ | 100 | でんきだま |
| エーフィ | 100 | まがったスプーン |
| カビゴン | 100 | たべのこし |
| フシギバナ | 100 | きせきのタネ |
| リザードン | 100 | もくたん |
| カメックス | 100 | しんぴのしずく |
'''
if red_new_heading not in status:
    assert red_old_heading in status, 'Red old heading not found'
    # Locate the heading after the DV bullet and replace through next ### heading.
    pos = status.find(red_old_heading)
    pre = status[:pos]
    rest = status[pos:]
    next_section = re.search(r'\n### \d', rest)
    assert next_section, 'next section heading not found after Red table'
    post = rest[next_section.start():]
    status = pre + red_new_table + post

# Hall section update.
status = _replace(
    status,
    '#### 殿堂入りで解放するもの\n\n従来の入手経路に加え、殿堂入り時に以下の**40品**の所持フラグを設定する。既に持っている品も含む。',
    '#### 殿堂入りで解放するもの\n\n従来の入手経路に加え、殿堂入り時に以下の**41品**の所持フラグを設定する。既に持っている品も含む。'
)

status = _replace(
    status,
    '| 通常の人形 | なみのりピカチュウ、プリン、フシギダネ、ゼニガメ、ニョロモ、ディグダ、スターミー、コイキング、ナゾノクサ、ゲンガー、シェルダー、ベトベター、ビリリダマ、ビードル、アンノーン、イシツブテ、ワンリキー、メノクラゲ | 18 |',
    '| 通常の人形 | なみのりピカチュウ、プリン、フシギダネ、ゼニガメ、ニョロモ、ディグダ、スターミー、コイキング、ナゾノクサ、ゲンガー、シェルダー、ベトベター、ビリリダマ、ビードル、アンノーン、イシツブテ、ワンリキー、メノクラゲ、ピカチュウ | 19 |'
)

status = _replace(
    status,
    'これとは別にポスター表示用フラグ `EVENT_KRISS_ROOM_POSTER` も設定する。従来の記録の「41種」は正確には**40品＋表示用フラグ1個＝41フラグ**。',
    'これとは別にポスター表示用フラグ `EVENT_KRISS_ROOM_POSTER`（0x2CC）も設定する。正確には**41品＋表示用フラグ1個＝42フラグ**。'
)

# Red defeat reward section: replace the 5-item list with the accurate note.
red_reward_old = (
    '#### レッド撃破で解放する5品\n\n- 金のトロフィー\n- ヒトカゲ人形\n- ピッピ人形\n- ピカチュウ人形\n- 大きなカビゴン人形'
)
red_reward_new = (
    '#### レッド撃破で設定される5つの所持フラグ\n\nレッド勝利時に以下の5つの所持フラグを設定する。'
    'ピカチュウ人形（0x2B7）は殿堂入り時点ですでに取得済みだが、再設定しても害はない。'
    'レッド専用の新規報酬は4種となる。\n\n- 金のトロフィー（レッド専用）\n- ヒトカゲ人形（レッド専用）\n- ピッピ人形（レッド専用）\n- 大きなカビゴン人形（レッド専用）\n- ピカチュウ人形（殿堂入り時点ですでに取得済み）'
)
status = _replace(status, red_reward_old, red_reward_new)

# Final artifact section: regenerate from the current ROM/IPS.
rc3_ref = (WORK / 'rc3_reference.gbc').read_bytes()
final_section = f"""## 最終生成物

- IPS ファイル: `Perfect_Crystal_2020_Japanese_RC4.ips`
- 適用対象: 日本語版『ポケットモンスター クリスタルバージョン』
- 出力 ROM サイズ: {len(current):,} バイト（原版と同じ 2 MiB）
- IPS ファイルサイズ: {len(ips):,} バイト
- 日本語原版からの変更バイト数: {sum(a != b for a, b in zip(jp, current)):,} バイト
- RC3 からの変更バイト数: {sum(a != b for a, b in zip(rc3_ref, current)):,} バイト（うち 2 バイトはグローバルチェックサム）
- 日本語原版 ROM SHA-256: `{sha256(jp).hexdigest()}`
- 出力 ROM SHA-256: `{sha256(current).hexdigest()}`
- IPS SHA-256: `{sha256(ips).hexdigest()}`

### CPU 検証

- RC2/RC3 の CPU 検証レポートは歴史的基盤として保持（`rc2_cpu_verification.json`、`rc3_cpu_verification.json`）。
- RC4 では Hall 装飾品フックの CPU 検証を新規実施（`rc4_cpu_verification.json`）：Hall トリガー・非 Hall トリガー・繰り返し実行の 3 モード。
- 物理機器または冒頭からエンドロールまでの完全プレイスルーは行っていません。
"""
# Replace the existing final artifact section if present.
final_heading = '## 最終生成物'
if final_heading in status:
    pre, rest = status.split(final_heading, 1)
    next_heading = re.search(r'\n## ', rest)
    if next_heading:
        post = rest[next_heading.start():]
    else:
        post = ''
    status = pre + final_section + '\n' + post
else:
    status += '\n' + final_section

status_path.write_text(status)
(RELEASE / 'PORTING_STATUS.md').write_text(status)

# Generate README_JP.md with a concise Japanese explanation of RC4.
readme_jp = f"""# Perfect Crystal（2020 Update）日本語移植版 RC4

この文書は、ビルド済み RC4 ROM から生成された日本語での変更概要です。
本パッチは利用者が所有する日本語版『ポケットモンスター クリスタルバージョン』に適用されます。

## 変更の全体像

- Perfect Crystal 2020 Update（英語版）の内容を日本語 ROM に移植
- RC2/RC3 で要求された戦闘バグ修正はそのまま保持
- RC4 では、2020 同梱の出現説明と今回指定されたレッド・報酬仕様に合わせて追加修正

## RC4 の追加補正

### 野生出現率

| ポケモン | 場所・時間 | RC4 の出現率 | 備考 |
|---|---|---|---|
| チコリータ | 31番道路 朝 | 10% | 変更なし |
| ヒノアラシ | くらやみのほらあな（キキョウ側）夜 | 40% | Lv2 30% + Lv4 10% |
| ワニノコ | 32番道路 昼 | 20% | Lv7 |
| ゼニガメ | つながりのどうくつ B1F 朝・昼 | 各 10% | Lv6（なみのり中は 40% のまま） |
| カブト | うずまきじま（ルギアの部屋）夜 | 10% | Lv27 |

### レッドのパーティ

- 6 匹全員を Lv100 に変更
- 種族・持ち物・技・個体値・日本語名は 2020 版のまま維持

### 殿堂入り装飾品フラグ

- 実際に入手可能なアイテム 41 種 + ポスター表示用フラグ 1 個 = **合計 42 フラグ**
- RC4 で追加したアイテムは **ピカチュウのぬいぐるみ（0x2B7）**

### レッド勝利後の報酬

- レッド専用の新規報酬は 4 種：金のトロフィー、ヒトカゲ人形、ピッピ人形、大きなカビゴン人形
- ピカチュウのぬいぐるみは殿堂入り時点で取得済み。レッド勝利時にも同じ所持フラグを再設定します

## 適用方法

`PC_WORKSPACE` に必要なファイルを配置した上で：

```bash
export PC_WORKSPACE=/path/to/private/workspace
python3 work/apply_jp_patch.py \\
  "$PC_WORKSPACE/Pocket Monsters - Crystal Version (Japan).gbc" \\
  --output "$PC_WORKSPACE/Perfect_Crystal_2020_Japanese_RC4.gbc"
```

または `work/release/Perfect_Crystal_2020_Japanese_RC4.ips` を任意の IPS 適用ツールで日本語原版 ROM に適用してください。

## 主な SHA-256

- 日本語原版 ROM: `{sha256(jp).hexdigest()}`
- RC3 歴史的基盤: `b6f6b73dc7e6d8f4d3223b398fb1202519efae0c0e36959ab7ac43cb8e5a4c21`
- RC4 出力 ROM: `{sha256(current).hexdigest()}`
- RC4 IPS: `{sha256(ips).hexdigest()}`

## 制限事項

- 実機での動作確認は行っていません
- 冒頭からエンドロールまでの完全プレイスルーは行っていません
- 本 README と `PORTING_STATUS.md` は、ローカルビルド済み ROM から `work/document_perfect_changes.py` で再生成してください
"""
(WORK / 'README_JP.md').write_text(readme_jp)
(RELEASE / 'README_JP.md').write_text(readme_jp)

print(json.dumps(dict(wild_changed_rows=len(wild), wild_maps=len(set(r['map'] for r in wild)),
                      prices=len(prices), marts=len(marts), trainers=len(trainerset),
                      leaders=len(leaders), document_lines=len(status.splitlines())), ensure_ascii=False))
