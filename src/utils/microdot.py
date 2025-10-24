import asyncio
import gc
import sys
import time

import machine
import mpy_ctrl
from microdot import *

from utils.net import net_wlan_get


class MicrodotEx(Microdot):
    def _system(self):
        wlan = net_wlan_get()
        yield f'machine.unique_id = {machine.unique_id().hex()}\n'
        yield f'machine.freq = {machine.freq()}\n'
        yield '\n'
        yield f'sys.platform = {sys.platform}\n'
        yield f'sys.version_info = {sys.version_info}\n'
        yield f'sys.path = {sys.path}\n'
        yield f'sys.version = {sys.version}\n'
        yield f'sys.ps1 = {sys.ps1}\n'
        yield f'sys.ps2 = {sys.ps2}\n'
        yield f'sys.byteorder = {sys.byteorder}\n'
        yield f'sys.modules = {list(sys.modules.keys())}\n'
        yield f'sys.argv = {sys.argv}\n'
        yield f'sys.implementation = {sys.implementation}\n'
        yield f'sys.maxsize = {sys.maxsize}\n'
        yield '\n'
        yield f'gc.mem_alloc = {gc.mem_alloc()}\n'
        yield f'gc.mem_free = {gc.mem_free()}\n'
        yield '\n'
        yield f'time.time = {time.time()}\n'
        yield f'time.time_ns = {time.time_ns()}\n'
        yield f'time.ticks_ms = {time.ticks_ms()}\n'
        yield f'time.ticks_us = {time.ticks_us()}\n'
        yield '\n'
        yield f'ctrl: GIT_COMMIT = {mpy_ctrl.GIT_COMMIT}\n'
        yield f'ctrl: GIT_VERSION = {mpy_ctrl.GIT_VERSION}\n'
        yield f'ctrl: ARGS = {mpy_ctrl.ARGS}\n'
        yield '\n'
        yield f'wlan: mac = {wlan.config("mac").hex()}\n'
        yield f'wlan: ssid = {wlan.config("ssid")}\n'
        yield f'wlan: secure = {bool(wlan.config("security"))}\n'
        yield f'wlan: ifconfig = {wlan.ifconfig()}\n'
        yield '\n'
        for methods, url, *_ in self.url_map:
            yield 'route: '
            yield ','.join(methods)
            yield ' '
            yield url.url_pattern
            yield '\n'

    def _enable_request_log(self):
        @self.after_request
        @self.after_error_request
        def _(req: Request, res: Response):
            print(
                f'http:', time.time(),
                req.client_addr[0], req.client_addr[1],
                req.method, req.url, '->', res.status_code,
            )

    def _enable_system_routes(self):
        @self.route('/')
        async def _(req: Request):
            return redirect('/system')

        @self.route('/system')
        async def _(req: Request):
            return self._system()

        @self.route('/system/id')
        async def _(req: Request):
            return f'{machine.unique_id().hex()}\n'

        @self.route('/system/reset/hard')
        @self.route('/system/reset')
        def _(req: Request):
            async def reset(hard=False):
                await asyncio.sleep(1)
                if hard:
                    print('http: hard reset')
                    machine.reset()
                else:
                    print('http: soft reset')
                    machine.soft_reset()
            asyncio.create_task(reset(req.path.endswith('/hard')))
            return redirect('/system')

    def start_server(self, *, host='0.0.0.0', port=80, request_log=True, system_routes=True):
        print('http: start server', host, port)
        if request_log:
            self._enable_request_log()
        if system_routes:
            self._enable_system_routes()
        return super().start_server(host, port)


class Args():
    class ArgError(ValueError):
        pass

    @staticmethod
    def inject(*, info=None, auto_validate=False):
        def decorator(f):
            async def handler(req: Request):
                args = Args(req.args, auto_validate)
                res, err, status = None, None, 200
                try:
                    res = await f(req, args)
                except Args.ArgError as e:
                    err, status = e.args[0], 400
                return {'info': info, 'time': time.time(), 'res': res, 'err': err, 'args': args.parsed}, status
            return handler
        return decorator

    def __init__(self, args, auto_validate=False):
        self._av = auto_validate
        self.args = args
        self.parsed = {}
        self.errors = []

    def _err(self, msg: str):
        self.errors.append(msg)
        if self._av:
            raise Args.ArgError(msg)

    def _get(self, key, default, typ, err):
        self.parsed[key] = None
        # XXX: microdot quirk, request args is a dict() when empty
        # args: MultiDict | dict[Unknown, Unknown]
        # handle empty case separately because of different get functions
        if not self.args:  # if not isinstance(self.args, MultiDict):
            if default is None:
                self._err(f'arg {key} missing')
                return err
            self.parsed[key] = default
            return default
        try:
            val = self.args.get(key, default, typ)
            if val is None:
                self._err(f'arg {key} missing')
                return err
            self.parsed[key] = val
            return val
        except ValueError:
            self._err(f'arg {key} invalid')
            return err

    def str(self, key, default=None, *, min: int | None = 1, max: int | None = None) -> str:
        val = self._get(key, default, str, '')
        if min is not None and len(val) < min:
            self._err(f'arg {key} len < {min}' if val else f'arg {key} empty')
        if max is not None and len(val) > max:
            self._err(f'arg {key} len > {max}')
        return val

    def int(self, key, default=None, *, min: int | None = None, max: int | None = None) -> int:
        val = self._get(key, default, int, 0)
        if min is not None and val < min:
            self._err(f'arg {key} < {min}')
        if max is not None and val > max:
            self._err(f'arg {key} > {max}')
        return val

    def validate(self):
        if self.errors:
            raise Args.ArgError(self.errors)
