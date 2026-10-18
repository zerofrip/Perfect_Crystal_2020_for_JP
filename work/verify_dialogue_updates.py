"""Verify text edits preserve actual Japanese scripts and unchanged paragraphs."""
from pathlib import Path
import sys
from map_layout import ROOT,file_offset,word
from japanese_text import encode
from dialogue_mapping import ENTRIES,locate
from gym_text_evidence import read_text
from port_dialogue_updates import apply_dialogue_updates
from verify_gym_rematches import inputs

EXPECTED=[(0x558d8,79),(0x6a1f8,32),(0x6a218,84),
          (0x541b8,28),(0x5b34a,77),(0x9f0dd,66)]


def verify(original,patched):
    changed=[]
    for index,(config,(address,size)) in enumerate(zip(ENTRIES,EXPECTED)):
        old=locate(original,config,japanese=True)
        assert old['text']==address and len(old['content'])==size
        assert original[old['script']:old['write']+3]==patched[old['script']:old['write']+3],config
        if index==3:
            assert patched[address:address+4]==bytes.fromhex('083e6521')
            assert patched[address+6:address+10]==bytes.fromhex('cd7c3121')
            assert word(patched,address+10)==0x4000+address%0x4000+13
            assert patched[address+12:address+14]==bytes.fromhex('c950')
            target=file_offset(0x65,word(patched,address+4))
            new=read_text(patched,target)
        else:
            new=read_text(patched,address)
            assert len(new)<=size
        old_parts=old['content'][1:-1].split(b'\x51')
        new_parts=new[1:-1].split(b'\x51')
        if index==0:
            assert encode('いしを') in new and encode('つうしんケーブル') not in new
            assert old_parts[1:]==new_parts[1:]
        elif index==1:
            assert encode('どうぐ') in new and encode('アップグレード') not in new
            assert old['content'].replace(encode('アップグレード'),encode('どうぐ'))==new
        elif index==2:
            assert new_parts==old_parts[:2]
        elif index==3:
            assert encode('けいけん') in new and encode('あかし') in new
            assert encode('ゆうり') not in new
        elif index==4:
            assert new_parts[0]==old_parts[0] and new_parts[2]==old_parts[2]
            assert encode('ちいさくなった') in new_parts[1] and encode('ハナダ') not in new
        else:
            assert new_parts==old_parts[:1]
        changed.append(new)
    print('dialogue_updates_verified',len(changed),'texts; original script pointers and preserved paragraphs unchanged')


if __name__=='__main__':
    original,en,perfect=inputs()
    if len(sys.argv)>1:
        patched=Path(sys.argv[1]).read_bytes()
    else:
        patched=bytearray(original)
        allowed=set()
        for offset,length,label in apply_dialogue_updates(original,en,perfect,patched):
            allowed.update(range(offset,offset+length))
        assert all(i in allowed for i,(a,b) in enumerate(zip(original,patched)) if a!=b)
    verify(original,patched)
