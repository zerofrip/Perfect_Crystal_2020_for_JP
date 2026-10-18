; Japanese Crystal bank $25.  The 2020 English Hall of Fame script sets these
; decoration flags immediately after EVENT_BEAT_ELITE_FOUR ($0044).  The stock
; Japanese decoration attribute table uses the same event IDs byte for byte.
;
; Script_setevent calls this at $25:796f instead of its original call $2e41.
; Only the Elite Four flag takes the extended path.  Preserve the result
; registers and flags of the original event action for the script engine.
SECTION "Hall Decoration Hook", ROMX[$7f92], BANK[$25]

HallDecorationHook:
    ld a, d
    and a
    jr nz, .normal
    ld a, e
    cp $44
    jr nz, .normal

    call $2e41
    push af
    push bc
    push de
    push hl

    ld de, $02a4
.loop
    ld a, e
    cp $b7
    jr z, .next
    cp $b9
    jr z, .next
    cp $bc
    jr z, .next
    cp $cd
    jr z, .next
    cp $cf
    jr z, .next

    push de
    ld b, 1
    call $2e41
    pop de
.next
    inc de
    ld a, e
    cp $d2
    jr nz, .loop

    pop hl
    pop de
    pop bc
    pop af
    ret

.normal
    jp $2e41
