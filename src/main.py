from machine import Pin
import asyncio
from keyboard import keyboard_setup

kb = keyboard_setup()
led = Pin('LED', Pin.OUT)


async def main():
    await asyncio.sleep(1)
    print('hi')
    # await kb.async_send_codes('9.99>')
    while True:
        await asyncio.sleep_ms(200)
        led.toggle()
        print(led.value())

asyncio.run(main())
