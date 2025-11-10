import asyncio
import typing

import machine


class ScaleSerial():
    def __init__(
        self,
        phys: typing.Tuple[int, int, int],
        proto: typing.Tuple[int, int, None | int, int],
    ):
        uart = machine.UART(
            phys[0], tx=phys[1], rx=phys[2],
            baudrate=proto[0], bits=proto[1], parity=proto[2], stop=proto[3],
        )
        self._lock = asyncio.Lock()
        self._sr = asyncio.StreamReader(uart, {})
        self._sw = asyncio.StreamWriter(uart, {})

    async def _send_request(self, data: bytes, *, sep=b'\r', max=128):
        async with self._lock:
            # drain any data on the receive buffer
            # XXX: should have some kind of limit
            try:
                while await asyncio.wait_for(self._sr.read(128), .1):
                    await asyncio.sleep_ms(10)
            except asyncio.TimeoutError:
                pass
            # write request
            self._sw.write(data)
            await self._sw.drain()
            # read response
            # XXX: should read up to separator (but no readuntil on StreamReader)
            try:
                return await asyncio.wait_for(self._sr.read(max), .2)
            except asyncio.TimeoutError:
                return None


class ScaleSerialToledo(ScaleSerial):
    class WeightResult():
        def __init__(self, data: bytes | None):
            self.data = data
            self.w = ''  # weight
            self.u = False  # unstable
            self.o = False  # overload
            self.n = False  # negative
            self.z = False  # zero
            if data and data[0] == 0x02 and data[-1] == 0x0d:  # STX...CR
                l = len(data)
                if l == 4 and data[1] == 0x3f and data[2] & 0xf0 == 0x60:  # '?' and flags
                    self.u = bool(data[2] & 0b0001)
                    self.o = bool(data[2] & 0b0010)
                    self.n = bool(data[2] & 0b0100)
                    self.z = bool(data[2] & 0b1000)
                elif l == 7:
                    self.w = data[1:6].decode('ascii')  # TODO: check digits

        def valid(self):
            return bool(self.w or self.u or self.o or self.n or self.z)

        def __str__(self):
            return ', '.join([
                (self.w + ' grams') if self.w else 'error' if self.valid() else 'invalid',
                ', '.join((x + '=' + ('1' if getattr(self, x) else '0')) for x in [
                    'u', 'o', 'n', 'z',
                ]),
                str(self.data),
            ])

    async def get_weight(self):
        data = await self._send_request(b'w\r', max=7)
        return self.__class__.WeightResult(data)
