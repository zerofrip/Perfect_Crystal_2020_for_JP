"""Generate candidates only: reference-source differences need ROM validation."""
from pc_env import workspace
from pathlib import Path
import difflib
ROOT=workspace()
left=ROOT/'pokekuristaru';right=ROOT/'perfect_crystal_source'
def normalized(path,perfect=False):
    result=[]
    for line in path.read_text().splitlines():
        line=line.split(';')[0].strip()
        if not line:continue
        line=line.replace('jp [hl]','jp hl')
        if perfect:
            # These two source labels were exchanged, but occupy the same
            # physical WRAM slots; inspect actual bytes for any true changes.
            line=line.replace('LastEnemyCounterMove','__firstcounter__').replace('LastPlayerCounterMove','LastEnemyCounterMove').replace('__firstcounter__','LastPlayerCounterMove')
        line=' '.join(line.split())
        result.append(line)
    return result
report=[]
for group in ('battle','items'):
    for path in sorted((left/group).rglob('*.asm')):
        rel=path.relative_to(left);other=right/rel
        if not other.exists():continue
        a,b=normalized(path),normalized(other,True)
        if a==b:continue
        diff=list(difflib.unified_diff(a,b,fromfile=str(rel)+' JP reference',tofile=str(rel)+' Perfect reference',n=3))
        report.extend(diff)
        print(str(rel), 'changed lines',sum(x.startswith(('+','-')) and not x.startswith(('+++','---')) for x in diff))
(ROOT/'work/battle_coverage_source_diff.txt').write_text('\n'.join(report)+'\n')
