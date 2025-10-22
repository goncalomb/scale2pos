import asyncio
import time

from utils.led import led_force, led_force_toggle, led_state

_t_load = time.ticks_ms()
_t_boot = 0
_t_main = 0

print('load')


def run(main, *, led=True):
    global _t_boot
    _t_boot = time.ticks_ms()

    print('boot')

    async def boot():
        async def print_timings():
            now = time.ticks_ms()
            print(
                'timings:',
                _t_boot - _t_load, _t_main - _t_boot, now - _t_main,
                '[load] [boot] [main]',
            )
        asyncio.create_task(print_timings())

        if led:
            led_state()
        global _t_main
        _t_main = time.ticks_ms()
        await main

    try:
        if led:
            led_force()
        asyncio.run(boot())
    finally:
        if led:
            led_force(False)
        print('end')


def panic(msg=None, *, led=True):
    msg = 'panic: ' + msg if msg else 'panic'
    while True:
        print(msg)
        if led:
            for _ in range(50):
                led_force_toggle()
                time.sleep_ms(100)
        else:
            time.sleep_ms(5000)
