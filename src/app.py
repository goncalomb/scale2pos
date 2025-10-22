from microdot import Microdot
from mpy_ctrl import ARGS, GIT_COMMIT, GIT_VERSION

import config
from utils.keyboard import keyboard_get
from utils.led import led_state
from utils.net import net_wlan_get, net_wlan_start


async def start(server=False):
    print('GIT_COMMIT =', GIT_COMMIT)
    print('GIT_VERSION =', GIT_VERSION)
    print('ARGS =', ARGS)
    print('app: start')

    net_wlan_start(
        config.wlan_ssid,
        ap=server,
        key=config.wlan_key,
        on_connected_change=lambda ok, ips: led_state(flash=0 if ok else -1),
    )

    app = Microdot()

    @app.route('/')
    async def _(req):
        return '\n'.join([
            'hi',
            f'GIT_COMMIT = {GIT_COMMIT}',
            f'GIT_VERSION = {GIT_VERSION}',
            f'ARGS = {ARGS}',
            f'ifconfig = {net_wlan_get().ifconfig()}',
            ''
        ])

    if server:
        @app.route('/kb')
        async def _(req):
            if 'code' not in req.args:
                return 'bad code', 400
            await keyboard_get().async_send_codes(req.args['code'])
            return 'ok'

    print('app: start web server')
    await app.start_server(port=80)
