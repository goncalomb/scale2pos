# Scale 2 POS (scale2pos)

The goal of this project is to connect a retail scale to a POS (point of sale) system using 2 Raspberry Pi Pico W.

The scale has an RS-232 port that is normally connected directly to the POS, but in this case it is connected an RPi that reads the weight from the scale and transmits it to the other RPi (over Wi-Fi), the second RPi inputs the weight (and product code) on the POS. This removes the need for the scale and POS to be physically connected.

## Requirements / Setup

"Client" RPi (scale):

- Connects to the scale using RS-232;
- Connects to the "server" using Wi-Fi;
- Has a buzzer for audio feedback;
- Has a set of push buttons for different product codes;
- Reads the weight from the scale and transmits it to the "server" (Web API), together with the product code as a barcode with embedded weight;

"Server" RPi (POS):

- Connects to the POS using USB;
- Acts as a USB keyboard;
- Acts as a Wi-Fi access point and web server (HTTP);
- Receives and emulates keyboard codes, the POS interprets these inputs as barcodes and registers the product;

## MicroPython Code

```bash
# setup environment and download dependencies
./mpy-ctrl.sh setup

# install the "client" code (scale) on a Raspberry Pi Pico W
./mpy-ctrl.sh push client

# install the "client" code (POS) on a Raspberry Pi Pico W
./mpy-ctrl.sh push server
```
