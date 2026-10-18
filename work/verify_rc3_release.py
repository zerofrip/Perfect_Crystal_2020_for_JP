"""Check the local RC3 package and preserve both earlier release candidates."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from pc_env import workspace

WORK=workspace()/'work'
ROOT=workspace()
release=WORK/'release'
manifest=json.loads((release/'manifest.json').read_text())
assert manifest['revision']=='RC3'
for path in (ROOT/'Pokemon Perfect Crystal 2020 Japanese RC3.gbc',WORK/'development_only_jp_partial.gbc'):
    assert sha256(path.read_bytes()).hexdigest()==manifest['output_sha256']
assert sha256((release/manifest['ips_file']).read_bytes()).hexdigest()==manifest['ips_sha256']
cpu=json.loads((release/manifest['cpu_verification_file']).read_text())
assert cpu['passed'] and cpu['rom_sha256']==manifest['output_sha256']
for revision,filename in (('RC1','Pokemon Perfect Crystal 2020 Japanese.gbc'),
                          ('RC2','Pokemon Perfect Crystal 2020 Japanese RC2.gbc')):
    previous=json.loads((release/(revision+'_metadata')/'manifest.json').read_text())
    assert sha256((ROOT/filename).read_bytes()).hexdigest()==previous['output_sha256']
    assert sha256((release/previous['ips_file']).read_bytes()).hexdigest()==previous['ips_sha256']
for name in ('README_JP.md','PORTING_STATUS.md'):
    assert (WORK/name).read_bytes()==(release/name).read_bytes(),name
status=(release/'PORTING_STATUS.md').read_text()
def tables(text):
    return text.split('<!-- perfect-2020-data:start -->',1)[1].split('<!-- perfect-2020-data:end -->',1)[0]
assert tables(status)==tables((release/'RC2_metadata/PORTING_STATUS.md').read_text())
assert manifest['output_sha256'] in status and manifest['ips_sha256'] in status
assert not list(release.rglob('*.gbc')) and not list(release.rglob('*.sav'))
result=subprocess.run([str(ROOT/'gb-asm-tools/tools/gbdiff.sh'),
                       str(WORK/'rc2_reference.gbc'),str(WORK/'development_only_jp_partial.gbc')],
                      check=True,capture_output=True,text=True)
(WORK/'rc2_to_rc3_gbdiff.txt').write_text(result.stdout)
assert '0d:7f70' in result.stdout and '0d:52c0' in result.stdout
print('RC3 ROM/IPS/CPU hashes match; RC1 and RC2 retained; docs and historical tables match; bank-aware diff saved')
