"""Password-free title clock reset for the original Japanese Crystal ROM.

The original Japanese Continue path already has a localized RTC repair screen.
This port sets the same SRAM request flag as released Perfect Crystal 2020,
then lets that original path load the save and update the clock normally.
No save payload, checksums, or hardware RTC registers are changed by this menu.
"""
from japanese_text import encode

CAVE = 0x7e82


class _Code:
    def __init__(self):
        self.data = bytearray()
        self.labels = {}
        self.fixups = []

    def label(self, name):
        self.labels[name] = CAVE + len(self.data)

    def emit(self, text):
        self.data.extend(bytes.fromhex(text))

    def addr(self, instruction, label):
        self.emit(instruction)
        self.fixups.append((len(self.data), label))
        self.data.extend(b'\0\0')

    def finish(self):
        for offset, label in self.fixups:
            self.data[offset:offset+2] = self.labels[label].to_bytes(2, 'little')
        return bytes(self.data)


def clock_reset_payload():
    c = _Code()
    c.label('table')
    c.emit('e8 5a d4 64 85 63 85 63')  # all four original title destinations
    c.addr('', 'wrapper')
    c.label('input')
    c.emit('21 a8 ff 7e e6 46 fe 46 c2')
    c.fixups.append((len(c.data), 'check_reset'))
    c.emit('00 00 c3 8f 64')  # Up+B+Select keeps delete-save priority
    c.label('check_reset')
    c.emit('7e e6 86 fe 86 c2 8f 64 3e 04 c3 a2 64')
    c.label('wrapper')
    c.addr('cd', 'menu')
    c.emit('c3 7d 01')  # original title/delete wrapper's reset destination
    c.label('menu')
    # Actual JP _DeleteSaveData setup, with addresses verified in the ROM.
    c.emit('3e 02 21 00 40 cf 06 08 cd 0c 33 cd 3b 0e cd 49 0e')
    c.emit('11 54 00 cd 24 3b')
    c.addr('21', 'question')
    c.emit('cd 41 10')
    c.addr('21', 'menu_header')
    c.emit('cd 07 1d cd 4c 1d')
    c.label('decision')
    c.emit('d8 fa 9d cf fe 01 c8')
    c.label('request')
    # This is outside both saved player-data checksums. Match released 2020:
    # write exactly $80, do not change save existence or the saved time offset.
    c.emit('3e 00 cd 9d 2f 3e 80 ea 80 ac cd ad 2f')
    c.addr('21', 'success')
    c.emit('cd 41 10 c9')
    c.label('question')
    c.data.extend(b'\x00' + encode('とけいを') + b'\x4f' + encode('せっていしなおしますか?') + b'\x57')
    c.label('success')
    c.data.extend(b'\x00' + encode('つづきから はじめる を') + b'\x4f' + encode('えらんで せっていしなおしてね') + b'\x58')
    c.label('menu_header')
    c.emit('00 07 0e 0b 13')
    c.addr('', 'menu_items')
    c.emit('01')
    c.label('menu_items')
    c.emit('c0 02 b2 b2 b4 50 ca b2 50')  # original いいえ / はい
    payload = c.finish()
    assert CAVE + len(payload) <= 0x8000
    return payload, c.labels


def apply_clock_reset(original, english_stock, perfect, output):
    """Apply only to verified original JP code; return all modified ranges."""
    # Exact actual-ROM control flow and SRAM layout evidence.
    anchors = {
        0x63d8: '5f160021e46319192a666fe9',
        0x63e4: 'e85ad46485638563',
        0x648c: '21a8ff7ee646fe46280a7ee6092001c93e0018023e01ea58cf2157cfcbfec9',
        0x64d4: '3e1321a553cfc37d01',
        0x6e3: '3e00cd9d2ffa80accdad2fc9',
        0x5e31: 'cde306e680280c3e08212140cf79a7280237c9afc9',
        0x4d3a5: '3e02210040cf0608cd0c33cd3b0ecd490e115400cd243b',
        0x4d3f4: '00070e0b13fc5301c002b2b2b450cab250',
    }
    for offset, value in anchors.items():
        expected = bytes.fromhex(value)
        assert original[offset:offset+len(expected)] == expected, f'clock anchor {offset:x}'
    # Released 2020 title combination, and its password-free flag write
    # (historical reference cross-checks).
    if perfect is not None and english_stock is not None:
        assert perfect[0x631f:0x6325] == bytes.fromhex('7ee686fe8628')
        assert bytes.fromhex('3e00cdcb2f3e80ea60accde12f') in perfect[0x4d3b1:0x4d40d]
        assert bytes.fromhex('3e80ea60ac') in english_stock[0x4d3b1:0x4d41e]
    payload, labels = clock_reset_payload()
    assert original[CAVE:0x8000] == bytes(0x8000-CAVE)
    assert output[CAVE:0x8000] == original[CAVE:0x8000], 'clock cave already used'
    for offset, size in ((0x63dc, 2), (0x648c, 3)):
        assert output[offset:offset+size] == original[offset:offset+size], 'clock hook already changed'
    ranges = []
    def put(offset, data, label):
        output[offset:offset+len(data)] = data
        ranges.append((offset, len(data), label))
    put(CAVE, payload, 'clock_reset_japanese_menu_and_title_table')
    put(0x63dc, labels['table'].to_bytes(2, 'little'), 'clock_reset_title_dispatch_table')
    put(0x648c, b'\xc3'+labels['input'].to_bytes(2, 'little'), 'clock_reset_title_buttons')
    return ranges
