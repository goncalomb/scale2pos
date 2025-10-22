from microdot import Microdot
from mpy_ctrl import ARGS, GIT_COMMIT, GIT_VERSION

from utils.keyboard import keyboard_get
from utils.led import led_state
from utils.net import start_ap


async def start(server=False):
    app = Microdot()

    print('GIT_COMMIT =', GIT_COMMIT)
    print('GIT_VERSION =', GIT_VERSION)
    print('ARGS =', ARGS)
    print('server =', server)

    led_state(on=True)
    print('start test ap')
    start_ap('TEST_AP')
    led_state()

    @app.route('/')
    async def _(req):
        return 'hi'

    @app.route('/kb')
    async def _(req):
        if 'code' not in req.args:
            return 'bad code', 400
        await keyboard_get().async_send_codes(req.args['code'])
        return 'ok'

    print('start server')
    await app.start_server(port=80)
