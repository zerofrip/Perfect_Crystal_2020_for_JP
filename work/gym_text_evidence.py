"""Show human-readable rematch text from the actual released ROM locally."""
import re
from map_layout import ROOT,maps,file_offset,word
from port_gym_rematches import GYMS,leader_info

def english_chars():
    result={0:'',0x4f:' / ',0x51:' | ',0x55:' / ',0x57:'',0x54:'#',0x7f:' '}
    for line in (ROOT/'perfect_crystal_source/macros/charmap.asm').read_text().splitlines():
        match=re.match(r'\s*charmap "([^"]+)",\s*\$([a-fA-F0-9]+)',line)
        if match and ((len(match[1])==1 and ord(match[1])<128) or match[1] in ('<PLAYER>','…')):
            result[int(match[2],16)]=match[1]
    return result

def read_text(rom,offset):
    end=rom.index(0x57,offset)
    return rom[offset:end+1]

if __name__=='__main__':
    old=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
    new=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
    a,b=maps(old),maps(new,True)
    charmap=english_chars()
    decode=lambda data: ''.join(charmap.get(c,f'<{c:02x}>') for c in data)
    for config in GYMS:
        x,y=leader_info(old,a,config),leader_info(new,b,config,perfect=True)
        before,after=read_text(old,x['text']),read_text(new,y['text'])
        i=0
        while i<min(len(before),len(after)) and before[i]==after[i]: i+=1
        defeat=file_offset(y['bank'],word(new,y['rematch']+1))
        print(config[0],hex(y['tail']),hex(y['rematch']))
        print('  added/changed:',decode(after[i:]))
        print('  defeat:',decode(read_text(new,defeat)))
