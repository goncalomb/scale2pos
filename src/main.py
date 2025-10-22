from mpy_ctrl import ARGS

from utils.bootstrap import panic, run
from utils.keyboard import keyboard_setup

variant = ARGS[0] if ARGS and ARGS[0] in ['client', 'server'] else None
if not variant:
    panic('invalid variant')

if variant == 'server':
    # do keyboard setup as early as possible
    keyboard_setup()


async def main():
    # defer app import
    from app import start
    await start(variant == 'server')

run(main())
