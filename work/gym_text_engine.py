"""Derive text-far dispatcher/entry addresses from the original Japanese ROM."""
import re
from map_layout import ROOT,word


def text_engine(rom):
    # Locate the command loop and derive all handler addresses from its own
    # table. The JP FAR handler differs from the reference disassembly.
    pattern=bytes.fromhex('2afe50c8cd')
    matches=[m.start() for m in re.finditer(re.escape(pattern),rom[:0x4000])]
    assert len(matches)==1,matches
    loop=matches[0]
    dispatcher=word(rom,loop+5)
    assert rom[dispatcher:dispatcher+6]==bytes.fromhex('e5c54f060021')
    table=word(rom,dispatcher+6)
    start=word(rom,table)
    # JP lacks the English TX_FAR ($16); its last entry is current_day ($15).
    assert start-table==22*2
    asm=word(rom,table+8*2)
    assert rom[asm:asm+6]==bytes.fromhex('cb7c2001e93e')
    win_pattern=bytes.fromhex('213dd0e60f2803213fd02a666fcd')
    matches=[m.start() for m in re.finditer(re.escape(win_pattern),rom[:0x4000])]
    assert len(matches)==1
    farprint=word(rom,matches[0]+17)
    assert farprint==0x317c
    return dict(loop=loop,dispatcher=dispatcher,table=table,start=start,
                asm=asm,farprint=farprint)


if __name__=='__main__':
    r=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
    print({k:hex(v) for k,v in text_engine(r).items()})
