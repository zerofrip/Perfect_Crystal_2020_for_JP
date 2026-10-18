"""Apply local compatibility fixes to pret's gbz80disasm.py for Python 3.

The upstream pokemon-reverse-engineering-tools disassembler uses Python 2
string formatting and integer division.  This script idempotently patches the
local checkout under PC_WORKSPACE/work/pokemon-reverse-engineering-tools so the
disassembly helpers in this repository can run on Python 3.

The main ROM builder only needs pokemontools for LZ decompression, which does
not require this patch.
"""
import hashlib
import sys
from pathlib import Path

from pc_env import workspace

TARGET = workspace() / 'work/pokemon-reverse-engineering-tools/pokemontools/gbz80disasm.py'

BEFORE_SHA256 = '8d6545d566f8b91f36387b4a05e8d6b0d9dfa8052b86cb7e489376900244c71a'
AFTER_SHA256 = '4a78a06f5bdfad63d8e6baa9f6047811657feb55bc6b528c919351b8b2a35947'

# Exact old/new full-line fragments, including comment alignment.
REPLACEMENTS = (
    ("('jp nc, ${:04x}', 2),         # d2",
     "('jp nc, {}', 2),              # d2"),
    ("('jp c, ${:04x}', 2),          # da",
     "('jp c, {}', 2),               # da"),
    ('bank = address / 0x4000',
     'bank = address // 0x4000'),
    ('comment_bank = offset / 0x4000',
     'comment_bank = offset // 0x4000'),
    ('bank_id = start_offset / 0x4000',
     'bank_id = start_offset // 0x4000'),
)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if not TARGET.exists():
        print('gbz80disasm.py not found:', TARGET, file=sys.stderr)
        sys.exit(1)

    original = TARGET.read_bytes()
    digest = sha256_bytes(original)
    if digest == AFTER_SHA256:
        print('gbz80disasm.py already patched:', digest)
        return
    if digest != BEFORE_SHA256:
        print(
            f'Unknown gbz80disasm.py source (expected {BEFORE_SHA256} or {AFTER_SHA256}, got {digest}). '
            'Refusing to modify.',
            file=sys.stderr,
        )
        sys.exit(1)

    text = original.decode('utf-8')
    for old, new in REPLACEMENTS:
        if text.count(old) != 1:
            print(
                f'Expected exactly one occurrence of {old!r} in gbz80disasm.py; found {text.count(old)}. '
                'Refusing to modify.',
                file=sys.stderr,
            )
            sys.exit(1)
        text = text.replace(old, new)

    if not text.endswith('\n'):
        text += '\n'

    candidate = text.encode('utf-8')
    new_digest = sha256_bytes(candidate)
    if new_digest != AFTER_SHA256:
        print(
            f'Patch produced unexpected hash {new_digest}; expected {AFTER_SHA256}. '
            'Refusing to write.',
            file=sys.stderr,
        )
        sys.exit(1)

    TARGET.write_bytes(candidate)
    print('Patched gbz80disasm.py:', new_digest)


if __name__ == '__main__':
    main()
