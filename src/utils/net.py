import network


def start_ap(ssid):
    # TODO: better support and state management
    ap = network.WLAN(network.AP_IF)
    ap.config(ssid=ssid, security=0)
    ap.active(True)
