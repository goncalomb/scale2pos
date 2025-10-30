import gc

import machine
import mpy_ctrl
import requests

import config
from barcode import gs1_retail_weight_code_gen
from utils.gpio import PinEx, gpio_start_poll_btns
from utils.keyboard import keyboard_get
from utils.led import led_force, led_state
from utils.microdot import Args, MicrodotEx, Request
from utils.net import net_wlan_start


def _request_get_json(url: str, *, led=True):
    # XXX: synchronous requests
    # the request library is synchronous, this is not ideal,
    # long requests can trigger the wdt, but one good thing
    # is that we don't need explicit concurrency checks
    # i.e. we don't need to ignore multiple button pushes
    # also, cannot use led_state (async)
    # led_state(on=True)
    if led:
        led_force()
    res = requests.get(url)
    if led:
        led_state(flash=1 if res.status_code == 200 else 2)
    return res, res.json() if res.status_code == 200 else None


def _send_keyboard_code(host: str, code: str):
    url = f'http://{host}/keyboard?code={code}'
    res, dat = _request_get_json(url)
    print(
        'response:', res.status_code,
        dat and (dat['err'] or dat['res']),
    )
    # XXX: OSError: [Errno 12] ENOMEM
    # when multiple (~5) error requests (!=200)?
    gc.collect()
    return res.status_code == 200


async def start(server=False):
    print(
        'app: start', machine.unique_id().hex(),
        mpy_ctrl.git_version, mpy_ctrl.args,
    )

    wlan_gateway = ''

    def on_connected_change(ok, ips):
        nonlocal wlan_gateway
        wlan_gateway = ips[2] if ok else ''
        led_state(flash=0 if ok else -1)

    net_wlan_start(
        config.wlan_ssid,
        ap=server,
        key=config.wlan_key,
        on_connected_change=on_connected_change,
    )

    buzzer_pin = PinEx(config.gpio_buzzer, PinEx.OUT, value=0)
    app = MicrodotEx()

    if server:  # server (POS)
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

    else:  # client (scale)
        pcodes = config.scale_gpio_product_codes

        def btn_long(id):
            if id == config.scale_gpio_reset:
                print('button: reset')
                app.shutdown()

        def btn_short(id):
            pcode = pcodes[id]
            if not wlan_gateway:
                print('button:', pcode, 'no wlan')
                buzzer_pin.async_flash(count=3)
                return

            # TODO: connect to actual weighing scale
            weight = '12345'

            try:
                bcode = gs1_retail_weight_code_gen(pcode, weight)
            except ValueError:
                print('button:', pcode, weight, 'bad code')
                buzzer_pin.async_flash(count=3)
                return

            print('button:', pcode, weight, 'sending', bcode)
            buzzer_pin.flash(count=1)  # the request is sync
            ok = _send_keyboard_code(wlan_gateway, bcode)
            buzzer_pin.async_flash(count=2 if ok else 3)

        gpio_start_poll_btns(
            pcodes.keys(),
            callback_short=btn_short, callback_long=btn_long,
        )

    await app.start_server()
    buzzer_pin.flash(count=2)
