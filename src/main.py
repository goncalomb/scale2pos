from server import start
from utils.bootstrap import run
from utils.keyboard import keyboard_setup

# do keyboard setup as early as possible
keyboard_setup()

run(start())
