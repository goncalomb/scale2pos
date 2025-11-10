import asyncio
import gc

import machine
import mpy_ctrl
import requests

import config
from utils.gpio import PinEx, gpio_start_poll_btns
from utils.keyboard import keyboard_get
from utils.led import led_force, led_state
from utils.microdot import Args, MicrodotEx, Request
from utils.net import net_wlan_start
from utils.retail import ScaleSerialToledo, gs1_retail_weight_code_gen


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
        # setup scale serial
        scale = ScaleSerialToledo(
            config.scale_serial_phys,
            config.scale_serial_proto,
        )
        # setup unused serial (dual transceiver)
        machine.Pin(
            config.scale_serial_extra_tx,
            mode=machine.Pin.IN, pull=machine.Pin.PULL_UP,
        )

        pcodes = config.scale_gpio_product_codes
        lock = asyncio.Lock()

        async def send_product_weight(pcode: str):
            if lock.locked():
                print('button:', pcode, 'locked')
                return
            async with lock:
                if not wlan_gateway:
                    print('button:', pcode, 'no wlan')
                    buzzer_pin.async_flash(count=3)
                    return

                weight = await scale.get_weight()
                print('button:', pcode, 'weight', weight)
                if not weight.w:  # bad weight
                    buzzer_pin.async_flash(count=3)
                    return

                try:
                    bcode = gs1_retail_weight_code_gen(pcode, weight.w)
                except ValueError:
                    print('button:', pcode, weight.w, 'bad code')
                    buzzer_pin.async_flash(count=3)
                    return

                print('button:', pcode, weight.w, 'sending', bcode)
                buzzer_pin.flash(count=1)  # the request is sync
                ok = _send_keyboard_code(wlan_gateway, bcode)
                buzzer_pin.async_flash(count=2 if ok else 3)

        def btn_long(id):
            if id == config.scale_gpio_reset:
                print('button: reset')
                app.shutdown()

        def btn_short(id):
            asyncio.create_task(send_product_weight(pcodes[id]))

        gpio_start_poll_btns(
            pcodes.keys(),
            callback_short=btn_short, callback_long=btn_long,
        )

    await app.start_server()
    buzzer_pin.flash(count=2)
