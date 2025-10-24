import machine
import mpy_ctrl

import config
from utils.keyboard import keyboard_get
from utils.led import led_state
from utils.microdot import Args, MicrodotEx, Request
from utils.net import net_wlan_start


async def start(server=False):
    print(
        'app: start', machine.unique_id().hex(),
        mpy_ctrl.git_version, mpy_ctrl.args,
    )

    net_wlan_start(
        config.wlan_ssid,
        ap=server,
        key=config.wlan_key,
        on_connected_change=lambda ok, ips: led_state(flash=0 if ok else -1),
    )

    app = MicrodotEx()

    if server:
        @app.route('/keyboard')
        @Args.inject(info='send keyboard codes')
        async def _(req: Request, args: Args):
            code = args.str('code', max=config.pos_keyboard_code_max)
            delay = args.int(
                'delay', config.pos_keyboard_delay,
                min=0, max=config.pos_keyboard_delay_max,
            )
            delay_long = args.int(
                'delay_long', config.pos_keyboard_delay_long,
                min=0, max=config.pos_keyboard_delay_long_max,
            )
            args.validate()
            await keyboard_get().async_send_codes(code, delay, delay_long)

    await app.start_server()
