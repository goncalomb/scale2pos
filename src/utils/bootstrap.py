def run(main):
    from utils.led import led_force, led_state
    led_force()

    # allow us to capture all print messages
    import time
    time.sleep(1)

    async def boot():
        led_state()
        print('boot')
        await main

    try:
        import asyncio
        asyncio.run(boot())
    finally:
        led_force(False)
        print('end')
