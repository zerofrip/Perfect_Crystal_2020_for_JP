"""Score historic upstream trees against Perfect's import without Git writes."""
from pc_env import workspace
from collections import Counter
import difflib
import json
from pathlib import Path
import subprocess

ROOT=workspace()
PERF=ROOT/'perfect_crystal_source'
UP=ROOT/'pokecrystal'
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])
def tree(repo,ref):
    result={}
    for line in git(repo,'ls-tree','-r',ref).decode().splitlines():
        desc,path=line.split('\t',1)
        mode,kind,obj=desc.split()
        if kind=='blob':result[path]=obj
    return result
target=tree(PERF,'ee6828e')
log=git(UP,'log','--first-parent','--reverse','--raw','--no-abbrev','--no-renames',
        '--diff-merges=first-parent','--format=COMMIT %H %ad %s','--date=short',
        '--since=2015-01-01','--until=2019-02-07','HEAD').decode()
first=next(line.split()[1] for line in log.splitlines() if line.startswith('COMMIT '))
current=tree(UP,first+'^')
score=sum(target.get(path)==blob for path,blob in current.items())
scores=[]
record=None
for line in log.splitlines():
    if line.startswith('COMMIT '):
        if record:scores.append(dict(record,score=score))
        _,commit,date,subject=line.split(' ',3)
        record=dict(commit=commit,date=date,subject=subject)
    elif line.startswith(':'):
        desc,path=line.split('\t',1)
        _,_,old,new,status=desc.split()
        before=current.get(path)
        if before is not None and target.get(path)==before:score-=1
        if status=='D':current.pop(path,None)
        else:current[path]=new
        if status!='D' and target.get(path)==new:score+=1
if record:scores.append(dict(record,score=score))
scores.sort(key=lambda item:(item['score'],item['date']),reverse=True)
print('scored_commits',len(scores),'target_files',len(target))
for result in scores[:12]:print(result)
best=scores[0]
base=tree(UP,best['commit'])
assert sum(target.get(path)==blob for path,blob in base.items())==best['score']
changes=[]
diff=[]
for path in sorted(set(base)|set(target)):
    if base.get(path)==target.get(path):continue
    status='added' if path not in base else 'removed' if path not in target else 'modified'
    changes.append(dict(path=path,status=status,base_blob=base.get(path),import_blob=target.get(path)))
    if path.endswith(('.asm','.py','.md','.txt')) and not path.startswith(('battle/','engine/battle','items/')):
        before=git(UP,'show',best['commit']+':'+path).decode(errors='replace') if path in base else ''
        after=git(PERF,'show','ee6828e:'+path).decode(errors='replace') if path in target else ''
        diff.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
                                       fromfile='upstream/'+path,tofile='PerfectImport/'+path))
(ROOT/'work/audit_baseline_scores.json').write_text(json.dumps(scores,indent=2))
(ROOT/'work/audit_initial_changes.json').write_text(json.dumps({'best':best,'changes':changes},indent=2))
(ROOT/'work/audit_perfect_initial_vs_upstream.patch').write_text(''.join(diff))
print('best_changes',len(changes),dict(Counter(x['status'] for x in changes)))
print('\n'.join(x['status']+' '+x['path'] for x in changes))
