import asyncio
import sys

from machine import Pin

_led = None
_led_task = None


def _led_get():
    global _led
    if not _led:
        _led = Pin('LED', Pin.OUT)
    return _led


async def _led_create_task(led: Pin, on=False, flash=0):
    led.value(1 if on else 0)
    if flash:
        for _ in range(sys.maxsize if flash < 0 else flash):
            await asyncio.sleep_ms(200)
            led.toggle()
            await asyncio.sleep_ms(200)
            led.toggle()
    while True:
        await asyncio.sleep_ms(5000)
        led.toggle()
        await asyncio.sleep_ms(50)
        led.toggle()


def led_state(*, on=False, flash=0):
    global _led_task
    if _led_task:
        _led_task.cancel()
    _led_task = asyncio.create_task(_led_create_task(_led_get(), on, flash))


def led_force(on=True):
    _led_get().value(1 if on else 0)


def led_force_toggle():
    _led_get().toggle()
