"""Correct sharp drops and preserve stages when the original stat check fails.

Apply after the released-2020 behavior has already been ported. Restore the
original JP JR NZ: after the second decrement, skip INC B unless B is zero.
The command's earlier stage-one failure and all immunity/miss checks remain.
The original TryLowerStat check is retained; its failure restores the exact
previous stage instead of unconditionally adding one to the proposed stage.
"""

OFFSET=0x3630d
HOOK_OFFSET=0x3634e
CAVE_OFFSET=0x37fa0
STAT_BLOCK=bytes.fromhex(
    '7079fe053018e5214cd211b5c6f0e4a728062137c611aac6cd3264e12805')
HOOK=bytes.fromhex('c3a07f000000')
# Save the original stage on the stack, then execute the original write,
# accuracy/evasion branch, stat selection and TryLowerStat call. Its old
# Hit branch now lands at POP AF; the existing Hit resets flags afterwards.
# On failure set [HL] to the saved stage minus one and enter the original
# INC [HL]/CantLower path, restoring both the stage and original CPU flags.
CAVE=bytes.fromhex('7ef5')+STAT_BLOCK[:-2]+bytes.fromhex(
    '2804f1c36c63f13d77c37163')
assert len(CAVE)==42


def apply_sharp_stat_drop_fix(original,english_stock,perfect,output):
    before=bytes.fromhex('fa00c7e6f0280405200104f0e4a72823')
    rc1=bytes.fromhex('fa00c7e6f0280405280104f0e4a72823')
    released=bytes.fromhex('fa0cc7e6f0280405280104cd2773')
    stock=bytes.fromhex('fa0cc7e6f0280405200104f0e4a72823')
    assert len(output)==len(original)==len(english_stock)==len(perfect)==0x200000
    assert original.count(before)==1 and original.find(before)==0x36305
    assert english_stock.count(stock)==1 and english_stock.find(stock)==0x36305
    assert perfect.count(released)==1 and perfect.find(released)==0x362e9
    assert original[OFFSET]==0x20
    assert output[0x36305:0x36305+len(rc1)]==rc1, 'expected released-2020/RC1 stat-drop preimage'
    assert original[HOOK_OFFSET:HOOK_OFFSET+len(STAT_BLOCK)]==STAT_BLOCK
    assert output[HOOK_OFFSET:HOOK_OFFSET+len(STAT_BLOCK)]==STAT_BLOCK, 'stat-drop body overlap'
    assert original[CAVE_OFFSET:CAVE_OFFSET+len(CAVE)]==bytes(len(CAVE))
    assert output[CAVE_OFFSET:CAVE_OFFSET+len(CAVE)]==bytes(len(CAVE)), 'stat-drop cave overlap'
    # Validate every region before the first write, including the cave.
    output[OFFSET]=0x20
    output[HOOK_OFFSET:HOOK_OFFSET+len(HOOK)]=HOOK
    output[CAVE_OFFSET:CAVE_OFFSET+len(CAVE)]=CAVE
    return [(OFFSET,1,'sharp_stat_drop_two_stages_floor_one'),
            (HOOK_OFFSET,len(HOOK),'sharp_stat_drop_preserve_stage_hook'),
            (CAVE_OFFSET,len(CAVE),'sharp_stat_drop_preserve_stage_routine')]
