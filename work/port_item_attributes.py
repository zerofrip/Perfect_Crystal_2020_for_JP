"""Port released prices and held effects, preserving regional item records."""

JP_TABLE=0x69fa
UE_TABLE=0x67c1
PC_TABLE=0x67a7
COUNT=255

def apply_item_attributes(original,english_stock,perfect,output):
    ranges=[];changed=[]
    # The actual ItemAttributes callers and the first two records identify
    # the tables independently of public source layout and price constants.
    first=bytes.fromhex('00000000400306b0040000400306')
    for rom,start in ((original,JP_TABLE),(english_stock,UE_TABLE),(perfect,PC_TABLE)):
        assert rom[start:start+14]==first, (hex(start),rom[start:start+14].hex())
        assert rom.count(first)==1
    for index in range(COUNT):
        before=english_stock[UE_TABLE+7*index:UE_TABLE+7*(index+1)]
        after=perfect[PC_TABLE+7*index:PC_TABLE+7*(index+1)]
        if before==after:continue
        changed.append(index+1)
        target=JP_TABLE+7*index
        assert original[target:target+7]==before,('regional preimage',index+1)
        assert output[target:target+7]==before,('overlap',index+1)
        output[target:target+7]=after
        ranges.append((target,7,'released_item_attributes_'+str(index+1)))
    assert len(changed)==13,changed
    return ranges

if __name__=='__main__':
    from map_layout import ROOT
    j=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
    u=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
    p=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
    output=bytearray(j)
    print(apply_item_attributes(j,u,p,output))
