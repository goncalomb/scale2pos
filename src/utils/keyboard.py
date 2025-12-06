import asyncio
import time

import usb.device
from usb.device.keyboard import KeyboardInterface, KeyCode


def _gen_char_codes(spec):
    def gen(chr_start, code, chr_end):
        start = ord(chr_start)
        return [(chr(start + i), code + i) for i in range(0, ord(chr_end) - start + 1)]
    for args in spec:
        if len(args) < 3:
            yield tuple(args)
        else:
            for v in gen(*args):
                yield v


class KeyboardInterfaceEx(KeyboardInterface):
    CHAR_CODES = dict(_gen_char_codes([
        ('>', KeyCode.ENTER),
        ('E', KeyCode.ESCAPE),
        ('<', KeyCode.BACKSPACE),
        ('T', KeyCode.TAB),
        (' ', KeyCode.SPACE),
        ('.', KeyCode.DOT),
        (',', KeyCode.COMMA),
        ('a', KeyCode.A, 'z'),
        ('0', KeyCode.N0),
        ('1', KeyCode.N1, '9'),
    ]))

    def send_codes(self, codes, delay=20, delay_long=200):
        for c in codes:
            if c == '_':
                time.sleep_ms(delay_long)
            elif c in self.CHAR_CODES:
                self.send_keys([self.CHAR_CODES[c]])
                self.send_keys([])
                time.sleep_ms(delay)

    async def async_send_codes(self, codes, delay=20, delay_long=200):
        for c in codes:
            if c == '_':
                await asyncio.sleep_ms(delay_long)
            elif c in self.CHAR_CODES:
                self.send_keys([self.CHAR_CODES[c]])
                await asyncio.sleep_ms(5)
                self.send_keys([])
                await asyncio.sleep_ms(delay)


_kb = None


def keyboard_get():
    global _kb
    if not _kb:
        _kb = KeyboardInterfaceEx()
        usb.device.get().init(_kb, builtin_driver=True)
    return _kb


def keyboard_setup():
    keyboard_get()
