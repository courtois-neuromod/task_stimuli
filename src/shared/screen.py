from . import config
from subprocess import Popen
import os


def init_exp_screen():
    if os.name != 'nt':
        xrandr = Popen(
            [
                "xrandr",
                "--output",
                config.EXP_SCREEN_XRANDR_NAME,
                "--mode",
                "%dx%d" % config.EXP_WINDOW["size"],
                "--rate",
                str(config.FRAME_RATE),
            ]
        )


def reset_exp_screen():
    if os.name != 'nt':
        xrandr = Popen(
            [
                "xrandr",
                "--output",
                config.EXP_SCREEN_XRANDR_NAME,
                "--preferred",
            ]
        )
