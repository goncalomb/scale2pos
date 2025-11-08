import asyncio
import binascii
import sys

from machine import UART, Pin


class SerialDebug():
    @staticmethod
    def setup_echo(id, *, tx, rx):
        uart = UART(id, baudrate=9600, tx=Pin(tx), rx=Pin(rx))

        async def echo_task():
            sr = asyncio.StreamReader(uart)
            sw = asyncio.StreamWriter(uart, {})
            while buf := await sr.read(128):
                print('echo', len(buf), buf.hex(), buf)
                sw.write(buf)
                await sw.drain()
        asyncio.create_task(echo_task())

    def __init__(self, id, *, tx, rx):
        self._uart = UART(id, baudrate=9600, tx=Pin(tx), rx=Pin(rx))
        self._sw = asyncio.StreamWriter(self._uart, {})

        async def read_task(uart: UART):
            sr = asyncio.StreamReader(uart)
            while buf := await sr.read(128):
                print('>', len(buf), buf.hex(), buf)
        asyncio.create_task(read_task(self._uart))

    async def write(self, buf):
        print('<', len(buf), buf.hex(), buf)
        self._sw.write(buf)
        await self._sw.drain()

    def write_task(self, buf):
        return asyncio.create_task(self.write(buf))


async def serial_debug_start():
    await asyncio.sleep(1)
    sd = SerialDebug(0, tx=0, rx=1)
    SerialDebug.setup_echo(1, tx=4, rx=5)

    for s in [
        'connected to UART0',
        'echo on UART1',
        'commands:',
        '  -... = send to UART0',
        '  p... = set prefix',
        '  s... = set suffix',
        '  r = set raw',
        '  h = set hex',
        '  e = exit',
    ]:
        print('serial:', s)

    p = b''
    s = b'\r\n'
    h = False
    sr = asyncio.StreamReader(sys.stdin)
    while buf := await sr.readline():
        buf = buf.strip()
        if not buf:
            continue

        cmd = buf[0:1]
        if cmd not in b'-psrhe':
            print('serial: bad command')
            continue
        elif cmd == b'e':
            break
        elif cmd in b'rh':
            h = cmd == b'h'
            print('serial:', 'hex' if h else 'raw', 'mode')
            continue

        dat = buf[1:]
        if h:
            try:
                dat = binascii.unhexlify(dat)
            except ValueError:
                print('serial: bad hex')
                continue

        if cmd == b'-':
            await sd.write(p + dat + s)
        elif cmd == b'p':
            p = dat
            print('serial: prefix =', p)
        elif cmd == b's':
            s = dat
            print('serial: suffix =', s)
