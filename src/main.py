from mpy_ctrl import args

from utils.bootstrap import panic, run
from utils.keyboard import keyboard_setup

variant = args[0] if args and args[0] in [
    'client', 'server', 'serial-debug',
] else None
if not variant:
    panic('invalid variant')

if variant == 'server':
    # do keyboard setup as early as possible
    keyboard_setup()

if variant == 'client':
    from utils.led import led_setup
    from config import scale_gpio_led
    led_setup(scale_gpio_led)


async def main():
    # defer app import
    if variant == 'serial-debug':
        from utils.serial import serial_debug_start
        await serial_debug_start()
    else:
        from app import start
        await start(variant == 'server')

run(main())
