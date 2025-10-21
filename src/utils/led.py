import asyncio
import sys

from machine import Pin

_led = Pin('LED', Pin.OUT)
_led_task = None


async def _led_create_task(on=False, flash=0):
    _led.value(1 if on else 0)
    if flash:
        for _ in range(sys.maxsize if flash < 0 else flash):
            await asyncio.sleep_ms(200)
            _led.toggle()
            await asyncio.sleep_ms(200)
            _led.toggle()
    while True:
        await asyncio.sleep_ms(5000)
        _led.toggle()
        await asyncio.sleep_ms(50)
        _led.toggle()


def led_state(*, on=False, flash=0):
    global _led_task
    if _led_task:
        _led_task.cancel()
    _led_task = asyncio.create_task(_led_create_task(on, flash))
