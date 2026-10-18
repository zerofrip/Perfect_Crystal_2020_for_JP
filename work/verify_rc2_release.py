"""Check local RC2 deliverables, preserve RC1, and record gb-asm-tools diff."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from pc_env import workspace

WORK = workspace() / 'work'
ROOT = workspace()
release = WORK / 'release'
manifest = json.loads((release / 'manifest.json').read_text())
assert manifest['revision'] == 'RC2'
assert sha256((ROOT / 'Pokemon Perfect Crystal 2020 Japanese RC2.gbc').read_bytes()).hexdigest() == manifest['output_sha256']
assert sha256((WORK / 'development_only_jp_partial.gbc').read_bytes()).hexdigest() == manifest['output_sha256']
assert sha256((release / manifest['ips_file']).read_bytes()).hexdigest() == manifest['ips_sha256']
cpu = json.loads((release / manifest['cpu_verification_file']).read_text())
assert cpu['passed'] and cpu['rom_sha256'] == manifest['output_sha256']
assert cpu['total_corrected_cpu_cases'] == 1357
assert sha256((ROOT / 'Pokemon Perfect Crystal 2020 Japanese.gbc').read_bytes()).hexdigest() == manifest['base_rc1_sha256']
rc1 = json.loads((release / 'RC1_metadata/manifest.json').read_text())
assert sha256((release / rc1['ips_file']).read_bytes()).hexdigest() == rc1['ips_sha256']
for name in ('README_JP.md', 'PORTING_STATUS.md'):
    assert (WORK / name).read_bytes() == (release / name).read_bytes(), name
status = (release / 'PORTING_STATUS.md').read_text()
previous_status = (release / 'RC1_metadata/PORTING_STATUS.md').read_text()
def data_tables(text):
    return text.split('<!-- perfect-2020-data:start -->', 1)[1].split('<!-- perfect-2020-data:end -->', 1)[0]
assert data_tables(status) == data_tables(previous_status), 'historical 2020 data tables changed'
assert manifest['output_sha256'] in status and manifest['ips_sha256'] in status
assert not list(release.rglob('*.gbc'))
assert not list(release.rglob('*.sav'))
# Run the user's requested bank-aware diff tool on local files only.
result = subprocess.run(
    [str(ROOT / 'gb-asm-tools/tools/gbdiff.sh'),
     str(WORK / 'rc1_reference.gbc'), str(WORK / 'development_only_jp_partial.gbc')],
     check=True, capture_output=True, text=True)
(WORK / 'rc1_to_rc2_gbdiff.txt').write_text(result.stdout)
for bank_address in ('00:0140', '01:6de0', '03:6f50', '03:7f80', '0d:6300', '0d:6340', '0d:7fa0', '3e:7df0'):
    assert bank_address in result.stdout, bank_address
print('RC2 ROM/IPS/manifest hashes match; RC1 retained; docs match; bank-aware diff recorded')
