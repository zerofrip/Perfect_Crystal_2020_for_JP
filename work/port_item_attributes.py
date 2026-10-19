"""Port released prices and held effects, preserving regional item records.

The 13 changed ItemAttributes records are authored in rc5_defs.items; every
unlisted item stays Japanese-original.  english_stock/perfect are optional
historical references used only to cross-check the authored definitions.
"""

JP_TABLE = 0x69FA
UE_TABLE = 0x67C1
PC_TABLE = 0x67A7
COUNT = 255


def apply_item_attributes(original, english_stock, perfect, output):
    ranges = []
    # The actual ItemAttributes callers and the first two records identify
    # the tables independently of public source layout and price constants.
    first = bytes.fromhex('00000000400306b0040000400306')
    assert original[JP_TABLE:JP_TABLE+14] == first, original[JP_TABLE:JP_TABLE+14].hex()
    assert original.count(first) == 1
    if english_stock is not None and perfect is not None:
        assert english_stock[UE_TABLE:UE_TABLE+14] == first
        assert perfect[PC_TABLE:PC_TABLE+14] == first
    from rc5_defs.items import CHANGED_ITEMS
    changed = set()
    for item_id, semantic in CHANGED_ITEMS:
        price, effect, param, permissions, pocket, fieldmoves = semantic
        record = price.to_bytes(2, 'little') + bytes((effect, param, permissions, pocket, fieldmoves))
        assert len(record) == 7
        target = JP_TABLE + 7 * (item_id - 1)
        if english_stock is not None and perfect is not None:
            before = english_stock[UE_TABLE+7*(item_id-1):UE_TABLE+7*item_id]
            after = perfect[PC_TABLE+7*(item_id-1):PC_TABLE+7*item_id]
            assert before != after, ('reference records identical', item_id)
            assert original[target:target+7] == before, ('regional preimage', item_id)
            assert after == record, ('authored record drifts from released', item_id)
        assert output[target:target+7] == original[target:target+7], ('overlap', item_id)
        output[target:target+7] = record
        changed.add(item_id)
        ranges.append((target, 7, 'released_item_attributes_'+str(item_id)))
    if english_stock is not None and perfect is not None:
        reference_changed = {index + 1 for index in range(COUNT)
                             if english_stock[UE_TABLE+7*index:UE_TABLE+7*(index+1)] !=
                             perfect[PC_TABLE+7*index:PC_TABLE+7*(index+1)]}
        assert reference_changed == changed, (sorted(reference_changed), sorted(changed))
    return ranges

if __name__=='__main__':
    from map_layout import ROOT
    j=(ROOT/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()
    u=(ROOT/'Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc').read_bytes()
    p=(ROOT/'work/perfect_crystal_ue_patched.gbc').read_bytes()
    output=bytearray(j)
    print(apply_item_attributes(j,u,p,output))
