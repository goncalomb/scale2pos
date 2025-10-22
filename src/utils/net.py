import network


def start_ap(ssid, *, key=None):
    # TODO: better support and state management
    ap = network.WLAN(network.AP_IF)
    if key:
        ap.config(ssid=ssid, key=key)
    else:
        ap.config(ssid=ssid, security=0)
    ap.active(True)
