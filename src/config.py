import config_gen

wlan_ssid = 'SCALE2POS_' + config_gen.wlan_ssid_suffix
wlan_key = config_gen.wlan_key

gpio_buzzer = 15

pos_keyboard_code_max = 20
pos_keyboard_delay = 20
pos_keyboard_delay_max = 500
pos_keyboard_delay_long = 1500
pos_keyboard_delay_long_max = 5000

scale_gpio_reset = 10
scale_gpio_product_codes = {
    10: '10010',
    11: '10011',
    12: '10012',
    13: '10013',
}
