"""Requested RC2 correction: Dragon Fang boosts Dragon damage by ten percent."""
from hashlib import sha1
from port_item_attributes import JP_TABLE, UE_TABLE, PC_TABLE

ITEM_ID=0x90
OFFSET=JP_TABLE+(ITEM_ID-1)*7

def apply_dragon_fang_fix(original,english_stock,perfect,output):
    assert sha1(original).hexdigest()=='95127b901bbce2407daf43cce9f45d4c27ef635d'
    assert sha1(english_stock).hexdigest()=='f2f52230b536214ef7c9924f483392993e226cfb'
    assert sha1(perfect).hexdigest()=='dd00b737fbd18d2e8ae064097a36e8fd4b16855d'
    stock=bytes.fromhex('64000000400100')
    released=bytes.fromhex('64004000400100')
    assert original[OFFSET:OFFSET+7]==stock
    ue=UE_TABLE+(ITEM_ID-1)*7;pc=PC_TABLE+(ITEM_ID-1)*7
    assert english_stock[ue:ue+7]==stock
    assert perfect[pc:pc+7]==released
    assert output[OFFSET:OFFSET+7]==released, 'apply after released item-attribute port'
    # Effect $40 is already corrected by the 2020 port; the amount is zero.
    # The actual damage path multiplies its intermediate result by (100+C)/100.
    output[OFFSET+3]=10
    return [(OFFSET+3,1,'dragon_fang_ten_percent_amount')]
