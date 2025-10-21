import asyncio

from utils.keyboard import keyboard_setup
from utils.led import led_state

kb = keyboard_setup()


async def main():
    await asyncio.sleep(1)
    print('hi')
    # await kb.async_send_codes('9.99>')
    led_state(on=True)
    await asyncio.sleep(7)
    led_state(flash=-1)
    await asyncio.sleep(2)
    led_state()
    while True:
        await asyncio.sleep(1)


asyncio.run(main())
