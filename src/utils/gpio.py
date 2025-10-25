import asyncio
import time
import typing

import machine


def gpio_start_poll_btns(
    pins: typing.Iterable[int | str], *,
    callback_short=None, callback_long=None, interval=200, long=2000,
):
    async def poll(pins: list[tuple[int | str, machine.Pin]]):
        state = [-1] * len(pins)
        while True:
            now = time.ticks_ms()
            for i, (p, pin) in enumerate(pins):
                t = state[i]
                if pin.value():
                    if t >= 0 and callback_short:
                        callback_short(p)
                    if t != -1:
                        state[i] = -1  # up
                elif t == -1:
                    state[i] = time.ticks_ms()  # down
                elif t >= 0 and time.ticks_diff(now, t) > long:
                    if callback_long:
                        callback_long(p)
                    state[i] = -2  # long
            await asyncio.sleep_ms(interval)
    return asyncio.create_task(poll([
        (p, machine.Pin(p, machine.Pin.IN, machine.Pin.PULL_UP)) for p in pins
    ]))
