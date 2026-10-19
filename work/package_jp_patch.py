"""Package a locally verified candidate; never include or upload a ROM.

This script lives in the source tree, but it operates on private workspace data
under PC_WORKSPACE.  The verification scripts it spawns are resolved from the
source directory, while ROMs, IPS files and CPU reports are resolved from the
private workspace's work/ directory.
"""
from hashlib import sha1, sha256
import json
from pathlib import Path
import subprocess, sys

from pc_env import workspace

SOURCE_DIR = Path(__file__).resolve().parent
ROOT = workspace()
WORK = ROOT / 'work'

original = (ROOT / 'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
output = (WORK / 'development_only_jp_partial.gbc').read_bytes()
assert sha256(original).hexdigest() == '136ada06cb68656b7de475fa4b278d37dbeff8f5257e7dfdf7f4a4aec19a90f3'

# Retain RC2 evidence against its immutable baseline.
for script in ('verify_requested_fixes.py', 'verify_rc2_cpu_reports.py'):
    subprocess.run([sys.executable, str(SOURCE_DIR / script), str(WORK / 'rc2_reference.gbc')], check=True)

# RC3 evidence is historical; verify the stored RC3 snapshot before the RC4 gate.
subprocess.run([sys.executable, str(SOURCE_DIR / 'verify_rc3_delta.py'), str(WORK / 'rc3_reference.gbc')], check=True)
subprocess.run([sys.executable, str(SOURCE_DIR / 'verify_rc3_cpu_reports.py'), str(WORK / 'rc3_reference.gbc')], check=True)

# Historical RC4 gate: the stored RC4 snapshot must still satisfy the RC4 delta.
subprocess.run([sys.executable, str(SOURCE_DIR / 'verify_rc4_delta.py'), str(WORK / 'rc4_reference.gbc')], check=True)

# Current RC5 integrated checks.
for script in ('verify_partial_jp_patch.py', 'verify_rc5_delta.py',
               'verify_cerulean_cave.py', 'verify_gs_ball_binary.py',
               'verify_red_rewards_binary.py', 'verify_trainer_binary.py',
               'compare_red.py', 'audit_base_stats.py',
               'audit_species_records.py', 'audit_map_and_move_data.py',
               'audit_item_attributes.py', 'audit_encounter_tables.py',
               'compare_marts.py', 'nonbattle_event_fields_audit.py'):
    subprocess.run([sys.executable, str(SOURCE_DIR / script)], check=True)
for script in ('verify_gym_rematches.py', 'verify_dialogue_updates.py', 'verify_remaining_features.py'):
    subprocess.run([sys.executable, str(SOURCE_DIR / script), str(WORK / 'development_only_jp_partial.gbc')], check=True)

# Fresh Hall-hook CPU checks run against the current RC5 development ROM.
subprocess.run([sys.executable, str(SOURCE_DIR / 'verify_rc4_cpu_reports.py'), '--revision', 'RC5'], check=True)

patch = (WORK / 'development_only_jp_partial.ips').read_bytes()
assert len(original) == len(output) == 2 * 1024 * 1024
# Packaging can run separately from the builder: reject a stale IPS here too.
from io import BytesIO
sys.path.insert(0, str(ROOT / 'lazy_ips'))
from lazy_ips.patch import ips
roundtrip = bytearray(original)
for record in ips.read_patch(BytesIO(patch)):
    end = record.offset + len(record.data)
    assert end <= len(roundtrip), 'IPS write exceeds input ROM'
    roundtrip[record.offset:end] = record.data
assert bytes(roundtrip) == output, 'IPS does not reproduce the verified ROM'
release = WORK / 'release'
release.mkdir(exist_ok=True)
filename = 'Perfect_Crystal_2020_Japanese_RC5.ips'
(release / filename).write_bytes(patch)
manifest = {
    'name': 'Perfect Crystal (2020 Update) Japanese port',
    'status': 'release_candidate',
    'revision': 'RC5',
    'base_rc1_sha256': 'bdb8b08177dc6e5a549c5d3ed2499a9835ae7c7c01ad0acafda659072335805e',
    'base_rc2_sha256': '96b08ba49bc42096b2156a6795c86f1b47f40afe8786a6569da764d8c493163c',
    'base_rc3_sha256': 'b6f6b73dc7e6d8f4d3223b398fb1202519efae0c0e36959ab7ac43cb8e5a4c21',
    'base_rc4_sha256': 'f7a0da3b9df33d4d010b05d82c8e6644d09ebd9c42320cc1ee89d4e2fd20ddd6',
    'requested_corrections': [
        'Moon Ball: scan all evolution records; 4x catch rate capped at 255 for Moon Stone species.',
        'Dragon Fang: held effect amount 10 for Dragon moves.',
        'Magikarp length: unsigned 16-bit comparison.',
        'Sharp stat drops: decrease two stages, clamped at stage minimum.',
        'Held-item stat caps: exact minimum with 999; Metal Powder boosts 16-bit defense before damage-stat truncation.',
        'Starter encounter rates: Chikorita Route 31 morning 10%; Cyndaquil Dark Cave Violet entrance night 40%; Totodile Route 32 day 20%; Squirtle Union Cave B1F land morning/day 10%; Kabuto Whirl Island Lugia chamber night 10%.',
        "Red's party: all six Pokemon at level 100, preserving species/items/moves/DVs/Japanese name.",
        'Hall of Fame decoration flags: 42 flags (41 actual item flags plus separate poster-display flag), adding Pikachu doll (0x2B7) to the existing 41.',
        'RC5: graphics verified against the Japanese originals for all five target trainer pictures, Jynx front/back, its base plus three rendered animation frames, palettes and animation commands. The actual RC5 changes revert only swimmer_f and the Jynx front picture with its third animation frame, plus the associated storage, pointers and bank-64 assets; every other RC4 byte is preserved except the checksums.',
    ],
    'input_sha1': sha1(original).hexdigest(),
    'input_sha256': sha256(original).hexdigest(),
    'ips_file': filename,
    'ips_sha256': sha256(patch).hexdigest(),
    'output_sha256': sha256(output).hexdigest(),
    'rom_size': len(output),
    'changed_bytes': sum(a != b for a, b in zip(original, output)),
    'cpu_verification_file': 'rc5_cpu_verification.json',
    'baseline_rc2_cpu_verification_file': 'rc2_cpu_verification.json',
    'baseline_rc3_cpu_verification_file': 'rc3_cpu_verification.json',
    'source_2020_sha1': 'dd00b737fbd18d2e8ae064097a36e8fd4b16855d',
    'limitations': ['Not tested on physical hardware.', 'Not a complete start-to-credits playthrough.'],
}
(release / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
for name in ('README_JP.md', 'PORTING_STATUS.md'):
    (release / name).write_bytes((WORK / name).read_bytes())
for name in ('rc2_cpu_verification.json', 'rc3_cpu_verification.json', 'rc5_cpu_verification.json'):
    (release / name).write_bytes((WORK / name).read_bytes())
print(json.dumps(manifest, indent=2))
