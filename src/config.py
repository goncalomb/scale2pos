import config_gen

wlan_ssid = 'SCALE2POS_' + config_gen.wlan_ssid_suffix
wlan_key = config_gen.wlan_key

gpio_buzzer = 9

pos_keyboard_code_max = 20
pos_keyboard_delay = 20
pos_keyboard_delay_max = 500
pos_keyboard_delay_long = 1500
pos_keyboard_delay_long_max = 5000

scale_serial_phys = (0, 0, 1)  # id, tx, rx,
scale_serial_proto = (9600, 8, None, 1)  # speed, bits, parity, stop
scale_serial_extra_tx = 4  # extra unused tx pin to pull up (dual transceiver)
scale_gpio_reset = 10  # must be one of the product buttons (long press)
scale_gpio_product_codes = {  # product buttons (short press)
    10: '10010',
    11: '10011',
    12: '10012',
    13: '10013',
}
