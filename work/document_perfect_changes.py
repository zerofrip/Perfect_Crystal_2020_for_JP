"""Extract documentation tables from local stock/released ROMs; never modify ROMs."""
from collections import Counter
from hashlib import sha1
import json
from pathlib import Path
import re

from dialogue_mapping import japanese_chars
from map_layout import ROOT, map_names
from trainer_party_layout import trainer_groups

WORK = ROOT / 'work'
jp = (ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
ue = (ROOT / 'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
pc = (WORK / 'perfect_crystal_ue_patched.gbc').read_bytes()
assert sha1(jp).hexdigest() == '95127b901bbce2407daf43cce9f45d4c27ef635d'
assert sha1(ue).hexdigest() == 'f2f52230b536214ef7c9924f483392993e226cfb'
assert sha1(pc).hexdigest() == 'dd00b737fbd18d2e8ae064097a36e8fd4b16855d'
# Cumulative thresholds and slot indices, checked in all actual inputs.
probabilities=bytes.fromhex('1e003c0250045a065f08630a640c3c005a026404')
for rom in (jp,ue,pc):
    assert rom.count(probabilities)==1,'wild encounter slot weights differ'
chars = japanese_chars()
chars.update({0x50:'',0xeb:'ェ',0xf4:'ォ',0xef:'♂',0xf5:'♀'})

def decode(data, katakana=False):
    text = ''.join(chars.get(b, f'<{b:02x}>') for b in data.split(b'\x50')[0])
    if katakana:
        text = ''.join(chr(ord(c)+0x60) if 'ぁ' <= c <= 'ゖ' else c for c in text)
    return text

species = {i+1:decode(jp[0x5341a+i*5:0x5341a+(i+1)*5], True) for i in range(251)}
assert [species[i] for i in (1,2,3,151,251)] == ['フシギダネ','フシギソウ','フシギバナ','ミュウ','セレビィ']

def strings(offset, count):
    names={}
    for i in range(1,count+1):
        end=jp.index(0x50,offset)
        names[i]=decode(jp[offset:end])
        offset=end+1
    return names

items=strings(0x70fa,256)
moves=strings(0x4163b,251)
classes=strings(0x2d319,67)
for key,value in list(classes.items()):
    classes[key]=value.replace('ジムりーダー','ジムリーダー').replace('エりート','エリート').replace('ギタりスト','ギタリスト')
items[0]='なし'
moves[0]='なし'
for key,value in list(items.items()):
    items[key]=value.replace('りーフ','リーフ').replace('りカバー','リカバー').replace('ラブりー','ラブリー').replace('みずたまりボン','みずたまリボン')
tm_number=0
for line in (ROOT/'pokekuristaru/constants/item_constants.asm').read_text().splitlines():
    match=re.match(r'\s*add_tm\s+\w+\s*;\s*\$([0-9A-F]+)',line)
    if match:
        tm_number+=1
        items[int(match[1],16)]=f'わざマシン{tm_number:02d}'

locations=map_names(True)
wild=[]
for table,jstart,ustart,pstart,old_count,new_count,width in (
    ('ジョウト陸上',0x2a60c,0x2a5e9,0x2a5e9,61,61,47),
    ('ジョウト水上',0x2b140,0x2b11d,0x2b11d,38,38,9),
    ('カントー陸上',0x2b297,0x2b274,0x2b274,30,33,47),
    ('カントー水上',0x2b81a,0x2b7f7,0x2b884,24,26,9),
):
    assert jp[jstart:jstart+old_count*width]==ue[ustart:ustart+old_count*width]
    assert ue[ustart+old_count*width]==pc[pstart+new_count*width]==0xff
    before={tuple(ue[ustart+i*width:ustart+i*width+2]):ue[ustart+i*width:ustart+(i+1)*width] for i in range(old_count)}
    for i in range(new_count):
        row=pc[pstart+i*width:pstart+(i+1)*width]
        key=tuple(row[:2]); old=before.get(key)
        if old==row: continue
        modes=range(3) if width==47 else range(1)
        for mode in modes:
            count=7 if width==47 else 3
            header=5 if width==47 else 3
            index=header+mode*count*2
            rates=(30,30,20,10,5,4,1) if width==47 else (60,30,10)
            def group(record):
                if record is None:return []
                totals=Counter()
                for slot,chance in enumerate(rates):
                    level,mon=record[index+2*slot:index+2*slot+2]
                    totals[(mon,level)]+=chance
                return [dict(species=species[mon],level=level,percent=chance) for (mon,level),chance in totals.items()]
            oldslots=old[index:index+2*count] if old else None
            changed=oldslots!=row[index:index+2*count] or (old is not None and old[2+mode]!=row[2+mode])
            if changed:
                wild.append(dict(table=table,map=locations[key],mode=('朝','昼','夜')[mode] if width==47 else '全時間帯',
                                 old_rate=old[2+mode] if old else None,new_rate=row[2+mode],old=group(old),new=group(row)))

prices=[]
for item in range(1,256):
    old=ue[0x67c1+(item-1)*7:0x67c1+item*7]
    new=pc[0x67a7+(item-1)*7:0x67a7+item*7]
    if old[:2]!=new[:2]:prices.append(dict(id=item,name=items[item],old=int.from_bytes(old[:2],'little'),new=int.from_bytes(new[:2],'little')))
assert len(prices)==11

marts=[]
for number in range(34):
    def mart(rom,table):
        off=int.from_bytes(rom[table+number*2:table+number*2+2],'little')+0x10000
        return list(rom[off+1:off+1+rom[off]])
    old,new=mart(jp,0x164c3),mart(pc,0x160a9)
    if old!=new:marts.append(dict(id=number,old=[items[i] for i in old],new=[items[i] for i in new],added=[items[i] for i in new if i not in old],removed=[items[i] for i in old if i not in new]))
assert [m['id'] for m in marts]==[5,23,25,26]

jgroups=trainer_groups(jp,0x399ba,0x3b700)
ugroups=trainer_groups(ue,0x39999,0x3ba67)
pgroups=trainer_groups(pc,0x3999e,0x3bae1)
trainers=[]
def party(rom,record):
    _,_,kind,width,members=record
    result=[]
    for off in members:
        level,mon=rom[off:off+2];pos=off+2
        item=rom[pos] if kind&2 else 0
        if kind&2:pos+=1
        moveset=list(rom[pos:pos+4]) if kind&1 else None
        result.append(dict(species=species[mon],level=level,item=items[item],moves=[moves[i] for i in moveset] if moveset is not None else None))
    return result

for g,(jg,ug,pg) in enumerate(zip(jgroups,ugroups,pgroups),1):
    for t,(jr,ur,pr) in enumerate(zip(jg,ug,pg),1):
        old,new=party(ue,ur),party(pc,pr)
        if old==new and ur[2]==pr[2]:continue
        assert party(jp,jr)==old and jr[2]==ur[2],('Japanese baseline differs',g,t)
        name=decode(jp[jr[0]:jr[1]],True)
        trainers.append(dict(group=g,trainer_class=classes[g],index=t,name=name,old=old,new=new,old_type=ur[2],new_type=pr[2]))
assert len(trainers)==212
leaders=[]
for g in (1,3,2,4,7,6,5,8,17,18,19,21,26,35,46,64):
    record=jgroups[g-1][0]
    leaders.append(dict(name=decode(jp[record[0]:record[1]],True),party=party(pc,pgroups[g-1][0])))
result=dict(wild=wild,prices=prices,marts=marts,trainers=trainers,leaders=leaders,species=species,items=items,moves=moves)
(WORK/'perfect_2020_documentation_data.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

MAP_JA={
    'BurnedTowerB1F':'やけたとう B1F',
    'CeruleanCave1F':'ハナダのどうくつ 1F',
    'CeruleanCave2F':'ハナダのどうくつ 2F',
    'CeruleanCaveB1':'ハナダのどうくつ B1F',
    'DarkCaveVioletEntrance':'くらやみのほらあな（キキョウ側）',
    'IcePathB3F':'こおりのぬけみち B3F',
    'IlexForest':'ウバメのもり',
    'Route10North':'10番道路（北側・発電所付近）',
    'SilverCaveItemRooms':'シロガネやま（道具のある小部屋）',
    'SilverCaveOutside':'シロガネやま入口の屋外',
    'SilverCaveRoom1':'シロガネやま（第1の洞窟）',
    'SilverCaveRoom2':'シロガネやま（第2の洞窟）',
    'SilverCaveRoom3':'シロガネやま頂上（レッドの部屋）',
    'TinTower2F':'スズのとう 2F',
    'UnionCaveB1F':'つながりのどうくつ B1F',
    'WhirlIslandB2F':'うずまきじま B2F',
    'WhirlIslandLugiaChamber':'うずまきじま（ルギアの部屋）',
}
for row in wild:
    if re.fullmatch(r'Route\d+',row['map']):
        MAP_JA[row['map']]=row['map'][5:]+'番道路'
assert all(row['map'] in MAP_JA for row in wild)
assert len(wild)==66 and len(set(row['map'] for row in wild))==27

lines=['## データ変更の全一覧','',
       '以下の表は、ローカルの日本語原版・英語原版・2020配布版から抽出した値です。',
       '種族・道具・技・トレーナー名も日本語原版から復号しています。','',
       '### 店の全商品（変更された4売場）','',
       '| 売場 | 原版の商品 | 2020版で追加する商品 |',
       '|---|---|---|']
shops={5:'コガネデパート2F・薬売場',23:'タマムシデパート2F・薬売場',25:'タマムシデパート3F',26:'タマムシデパート4F'}
for row in marts:
    assert not row['removed']
    lines.append(f"| {shops[row['id']]} | {'、'.join(row['old'])} | {'、'.join(row['added'])} |")
lines+=['','原版の商品と追加商品を合わせたものが2020版の全在庫です。わざマシン09は「じこあんじ」、10は「めざめるパワー」、11は「にほんばれ」、17は「まもる」、18は「あまごい」、37は「すなあらし」。','',
        '### 基本価格の全変更11件','',
        '| 道具 | 原版 | 2020版 |','|---|---:|---:|']
for row in prices:lines.append(f"| {row['name']} | {row['old']:,}円 | {row['new']:,}円 |")
lines+=['','原版の0円や10円は、売場での販売実績ではなく道具データに保存されていた基本価格です。','',
        '### ジムリーダー16人の初戦・再戦パーティ','',
        '再戦も初戦と同じ編成です。持ち物の記載がない個体は持ち物なし。','',
        '| リーダー | 2020版のパーティ（登場順） |','|---|---|']
def describe(mon):
    text=f"{mon['species']} Lv{mon['level']}"
    if mon['item']!='なし':text+=f"（{mon['item']}）"
    return text
for row in leaders:lines.append(f"| {row['name']} | {'、'.join(describe(m) for m in row['party'])} |")

lines+=['','### 野生出現の全変更表（27マップ・66行）','',
        '確率は**野生ポケモンに遭遇したときの種族・レベルの選択割合**で、1歩ごとの遭遇率ではありません。',
        '陸上は草むら・洞窟床など、水上はなみのり中の遭遇です。水上表には朝昼夜の区別がありません。',
        '同じ種族・レベルの複数枠は合算。変化した時間帯／方法だけを掲載し、行内では変更前後の全出現枠を示します。',
        '原版に存在しないハナダのどうくつの行は「新規追加」と表記。固定Lv70ミュウツーはこの野生抽選表とは別です。','',
        '<details>','<summary>全66行を開く</summary>','',
        '| 場所 | 方法・時間 | 原版 | 2020版 |','|---|---|---|---|']
def encounters(entries):
    return '、'.join(f"{e['species']} Lv{e['level']}：{e['percent']}%" for e in entries) if entries else '新規追加'
for row in wild:
    assert sum(e['percent'] for e in row['new'])==100
    assert not row['old'] or sum(e['percent'] for e in row['old'])==100
    method='陸上' if '陸上' in row['table'] else '水上'
    oldtext=encounters(row['old']);newtext=encounters(row['new'])
    if row['old_rate'] is not None and row['old_rate']!=row['new_rate']:
        oldtext+=f"（遭遇率データ {row['old_rate']}）"
        newtext+=f"（遭遇率データ {row['new_rate']}）"
    lines.append(f"| {MAP_JA[row['map']]} | {method}・{row['mode']} | {oldtext} | {newtext} |")
lines+=['','</details>','',
        '### トレーナーの全変更表（212レコード）','',
        '各行は1つの編成データです。同じ人物の電話再戦・御三家による分岐なども別レコードとして数えます。',
        '「編成」はクラス番号-クラス内編成番号、「n匹目」は手持ちの登場順です。記載のない項目は原版と同じです。',
        'ライバルの「?」はデータ内の仮名で、ゲーム画面ではプレイヤーが付けた名前になります。',
        '技の「自動設定」は種族・レベルから技を決める形式。通常トレーナーのレベル上昇に伴う自動技の変化もこの形式に従います。',
        '個別の持ち物指定と、戦闘中にトレーナーが使う回復道具は別の仕組みです。',
        'レッドの個体値変更やジムの再戦会話は上記の機能説明を参照してください。','',
        '<details>','<summary>全212レコードを開く</summary>','',
        '| トレーナー | 編成 | パーティデータの変更 |','|---|---:|---|']
from itertools import zip_longest
for row in trainers:
    changes=[]
    for slot,(old,new) in enumerate(zip_longest(row['old'],row['new']),1):
        prefix=f'{slot}匹目：'
        if old is None:
            changes.append(prefix+'追加 '+describe(new)+'、技 '+('／'.join(new['moves']) if new['moves'] is not None else '自動設定'));continue
        if new is None:
            changes.append(prefix+'削除 '+describe(old)+'、技 '+('／'.join(old['moves']) if old['moves'] is not None else '自動設定'));continue
        delta=[]
        if old['species']!=new['species']:delta.append(f"{old['species']} → {new['species']}")
        if old['level']!=new['level']:delta.append(f"Lv{old['level']} → Lv{new['level']}")
        if old['item']!=new['item']:delta.append(f"持ち物 {old['item']} → {new['item']}")
        if old['moves']!=new['moves']:
            a='／'.join(old['moves']) if old['moves'] is not None else '自動設定'
            b='／'.join(new['moves']) if new['moves'] is not None else '自動設定'
            delta.append(f'技 {a} → {b}')
        if delta:
            species_prefix=(old['species']+' ') if old['species']==new['species'] else ''
            changes.append(prefix+species_prefix+'、'.join(delta))
    if not changes:
        assert row['old_type']!=row['new_type']
        changes.append('技・持ち物の指定形式を変更（具体値は同じ）')
    lines.append(f"| {row['trainer_class']}／{row['name']} | {row['group']}-{row['index']} | {'<br>'.join(changes)} |")
lines+=['','</details>','']
table='\n'.join(lines)
assert not re.search(r'<[0-9a-f]{2}>',table),'undecoded name byte'
start='<!-- perfect-2020-data:start -->'
end='<!-- perfect-2020-data:end -->'
status_path=WORK/'PORTING_STATUS.md'
status=status_path.read_text()
assert status.count(start)==status.count(end)==1
status=status.split(start)[0]+start+'\n\n'+table+'\n'+end+status.split(end)[1]
status_path.write_text(status)
(WORK/'release/PORTING_STATUS.md').write_text(status)
print(json.dumps(dict(wild_changed_rows=len(wild),wild_maps=len(set(r['map'] for r in wild)),prices=len(prices),marts=len(marts),trainers=len(trainers),leaders=len(leaders),document_lines=len(status.splitlines())),ensure_ascii=False))
