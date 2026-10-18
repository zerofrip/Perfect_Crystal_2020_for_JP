"""Compare instruction shapes across all actual battle-command pointer blocks.

This is a coverage aid, not a proof: relocated code pointers and relative
branch operands are normalized, so semantic pointer-only changes need source
or control-flow review. The inputs remain local.
"""
from pc_env import workspace
from pathlib import Path
import difflib
import json
import re
import sys
ROOT=workspace()
sys.path.insert(0,str(ROOT/'work/pokemon-reverse-engineering-tools'))
from pokemontools.gbz80disasm import z80_table
ROMS={'ue':(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes(),
      'pc':(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()}
names=re.findall(r'^\s*dw (BattleCommand\S+)',(ROOT/'perfect_crystal_source/battle/effect_command_pointers.asm').read_text(),re.M)
tables={};commands={}
for name,d in ROMS.items():
    pattern=rb'\xc5\x3d\x4f\x06\x00\x21(..)\x09\x09\xc1\x3e\x0f'
    matches=list(re.finditer(pattern,d[0x34000:0x34100],re.DOTALL))
    assert len(matches)==1
    table=0x3c000+int.from_bytes(matches[0][1],'little')-0x4000
    tables[name]=table
    commands[name]=[0x34000+int.from_bytes(d[table+2*i:table+2*i+2],'little')-0x4000 for i in range(len(names))]
    assert all(0x34000<=a<0x38000 for a in commands[name])
    print(name,'command_table',hex(table),'entries',len(names))

def instructions(d,a,b):
    result=[]
    while a<b:
        op=d[a];mnemonic,length=z80_table[op]
        args=d[a+1:a+1+length]
        if op in (0x18,0x20,0x28,0x30,0x38,0xc2,0xc3,0xc4,0xca,0xcc,0xcd,0xd2,0xd4,0xda,0xdc):
            token=mnemonic.replace('{}','target')
        elif op in (1,0x11,0x21) and 0x4000<=int.from_bytes(args,'little')<0x8000:
            token=mnemonic.replace('{}','ROM-pointer')
        else:
            token=mnemonic+' '+args.hex()
        result.append((a,token))
        a+=1+length
    return result

changed=[];seen=set()
for i,label in enumerate(names):
    pair=tuple(commands[n][i] for n in ('ue','pc'))
    if pair in seen:continue
    seen.add(pair)
    inst=[]
    for n,start in zip(('ue','pc'),pair):
        end=min((v for v in commands[n] if v>start),default=0x38000)
        if end==0x38000:
            while end>start and ROMS[n][end-1]==0:end-=1
        inst.append(instructions(ROMS[n],start,end))
    a,b=[[token for _,token in rows] for rows in inst]
    if a==b:continue
    blocks=[]
    for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():
        if tag!='equal':blocks.append({'type':tag,'ue':inst[0][i1:i2],'pc':inst[1][j1:j2]})
    changed.append({'command':label,'ue':pair[0],'pc':pair[1],'blocks':blocks})
    print(label,hex(pair[0]),hex(pair[1]),'changed instruction blocks',len(blocks))
(ROOT/'work/battle_coverage_commands.json').write_text(json.dumps({'tables':tables,'commands':len(names),'changed':changed},indent=2)+'\n')
