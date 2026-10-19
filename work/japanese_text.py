"""Encode explicit Japanese port text using the authored character map."""
import re
from map_layout import ROOT

# The default build is deterministic from checked-in definitions and the JP
# ROM: CHARMAP is the authored subset covering every character the build's
# text uses, and encode() fails fast on anything outside it.  Historical
# audit tools that want the full public disassembly charmap must opt in
# explicitly via reference_charmap(); no source tree is read implicitly.
from rc5_defs.charmap import CHARMAP


def reference_charmap():
    """Opt-in: overlay the pokekuristaru charmap for historical audits."""
    overlay = dict(CHARMAP)
    for line in (ROOT / 'pokekuristaru/macros/charmap.asm').read_text().splitlines():
        match = re.match(r'\s*charmap "([^"]+)",\s*\$([0-9a-fA-F]+)', line)
        if match:
            overlay[match[1]] = int(match[2], 16)
    return overlay


def encode(text):
    tokens = re.findall(r'<[^>]+>|.', text)
    return bytes(CHARMAP[token] for token in tokens)


def dialogue(paragraphs):
    result = bytearray((0,))
    for p, lines in enumerate(paragraphs):
        if p:
            result.append(0x51)
        for index, line in enumerate(lines):
            assert len(re.findall(r'<[^>]+>|.', line)) <= 18, line
            if index:
                result.append(0x4f if index == 1 else 0x55)
            result.extend(encode(line))
    result.append(0x57)
    return bytes(result)
