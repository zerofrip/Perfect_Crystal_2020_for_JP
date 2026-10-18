"""Read-only local Git archaeology for the Perfect Crystal import baseline."""
from pc_env import workspace
import json
from pathlib import Path
import subprocess

ROOT=workspace()
PERF=ROOT/'perfect_crystal_source'
UP=ROOT/'pokecrystal'

def git(repo,*args,input=None):
    return subprocess.check_output(['git','-C',str(repo),*args],input=input)

tree={}
for row in git(PERF,'ls-tree','-r','ee6828e').decode().splitlines():
    mode,kind,rest=row.split(' ',2)
    obj,path=rest.split('\t',1)
    if kind=='blob':tree[path]=obj
up_objects={row.split(' ',1)[0] for row in git(UP,'rev-list','--all','--objects').decode().splitlines()}
common={name:obj for name,obj in tree.items() if obj in up_objects}
print('import_files',len(tree),'upstream_object_matches',len(common))
anchors=['Makefile','home/text.asm','macros/event.asm','wram.asm','constants/trainer_constants.asm',
         'maps/CherrygroveCity.asm','engine/overworld.asm','main.asm','audio/engine.asm']
report={}
for name in anchors:
    if name not in tree:continue
    obj=tree[name]
    raw=git(PERF,'show',f'ee6828e:{name}')
    clean=git(UP,'hash-object','--stdin',input=raw.replace(b'\r\n',b'\n')).decode().strip()
    match=obj if obj in up_objects else clean if clean in up_objects else None
    print(name,'bytes',len(raw),'CRLF',raw.count(b'\r\n'),'match',match)
    if match:
        history=git(UP,'log','--all',f'--find-object={match}','--date=short','--format=%H %ad %s','--',name).decode()
        print(history.strip())
        report[name]={'blob':match,'history':history.splitlines()}
(ROOT/'work/audit_source_base_anchors.json').write_text(json.dumps(report,indent=2))
