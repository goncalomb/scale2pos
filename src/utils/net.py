import network
import uasyncio as asyncio

_stat_map = {
    getattr(network, key): key for key in dir(network) if key.startswith('STAT_')
}
_stat_bad = [
    network.STAT_IDLE,
    network.STAT_CONNECT_FAIL,
    network.STAT_NO_AP_FOUND,
    network.STAT_WRONG_PASSWORD,
]
_stat_initial = -999999  # placeholder
_stat_poll_interval = 1  # seconds
_stat_connecting_reset_count = 30  # X * _stat_poll_interval = seconds
_stat_backoff = 9, 1.5, 60  # min, base, max

_wlan = None
_wlan_task = None


def _get_stat_name(stat):
    return _stat_map[stat] if stat in _stat_map else f'STAT_UNKNOWN ({stat})'


async def _wlan_create_task(wlan: network.WLAN, on_connected_change, on_bad_status):
    # activate interface
    wlan.active(True)

    # start monitoring status
    s_last = _stat_initial
    s_conn_count = 0
    s_bad_count = 0
    while True:
        s = wlan.status()

        if s == s_last and s == network.STAT_CONNECTING:
            s_conn_count += 1
            if s_conn_count > _stat_connecting_reset_count:
                # sometimes the interface can be stuck on STAT_CONNECTING
                # while reconnecting with the AP (lost connection)
                # XXX: is this s bug? reset the interface
                print('wlan: taking too long, reset')
                wlan.disconnect()
                wlan.active(False)
                wlan.active(True)
                s_conn_count = 0
                s_bad_count = 0
        else:
            s_conn_count = 0

        if s == s_last:
            # same status, sleep
            await asyncio.sleep(_stat_poll_interval)
            continue

        print('wlan: status =', _get_stat_name(s))

        now_connected = s == network.STAT_GOT_IP
        was_connected = s_last == network.STAT_GOT_IP
        if now_connected or was_connected or s_last == _stat_initial:
            ips = wlan.ifconfig()
            if now_connected:
                print('wlan: ifconfig =', ips)
                s_bad_count = 0
            if on_connected_change:
                on_connected_change(now_connected, ips)

        if s in _stat_bad:
            if s_bad_count:
                # exponential backoff
                t = int(min(
                    _stat_backoff[0] + _stat_backoff[1]**s_bad_count,
                    _stat_backoff[2],
                ))
                print(f'wlan: backoff {t} seconds')
                await asyncio.sleep(t)
            on_bad_status(wlan, s)
            s_bad_count += 1

        s_last = s


def net_wlan_start(ssid, *, ap=False, key=None, on_connected_change=None):
    global _wlan, _wlan_task
    if _wlan and _wlan_task:
        raise RuntimeError('wlan already configured')

    print(
        'wlan:', 'AP_IF' if ap else 'STA_IF',
        '/', ssid,
        '/', 'secure' if key else 'not secure',
    )

    _wlan = network.WLAN(network.AP_IF if ap else network.STA_IF)
    if ap:
        if key:
            _wlan.config(ssid=ssid, key=key)
        else:
            _wlan.config(ssid=ssid, security=0)

    def on_bad_status(wlan, status):
        if not ap:
            wlan.connect(ssid, key)
        elif status != network.STAT_IDLE:
            print('wlan: error')

    _wlan_task = asyncio.create_task(_wlan_create_task(
        _wlan, on_connected_change,
        on_bad_status=on_bad_status,
    ))


def net_wlan_get():
    if not _wlan:
        raise RuntimeError('wlan not configured')
    return _wlan
