"""Read-only comparison of UE IPS record preimages against the Japanese ROM."""
from pc_env import workspace
from collections import Counter
from pathlib import Path
import sys

root = workspace()
sys.path.insert(0, str(root / "lazy_ips"))
from lazy_ips.patch import ips

ue = (root / "Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc").read_bytes()
jp = (root / "Pocket Monsters - Crystal Version (Japan).gbc").read_bytes()
with (root / "Pokemon Perfect Crystal (2020 Update)/Pokemon Perfect Crystal (2020 Update).ips").open("rb") as file:
    records = list(ips.read_patch(file))

counts = Counter()
bytes_count = Counter()
for record in records:
    start = record.offset
    end = start + len(record.data)
    before = ue[start:end]
    if before == jp[start:end]:
        kind = "same_offset_exact_preimage"
    elif len(before) < 8 or len(set(before)) < 3:
        kind = "short_or_low_entropy"
    else:
        first = jp.find(before)
        second = jp.find(before, first + 1) if first >= 0 else -1
        kind = "unique_elsewhere" if first >= 0 and second < 0 else ("ambiguous" if first >= 0 else "missing")
    counts[kind] += 1
    bytes_count[kind] += len(record.data)

for kind in sorted(counts):
    print(kind, "records", counts[kind], "written_bytes", bytes_count[kind])
