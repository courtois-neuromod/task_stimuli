import os
from dotenv import load_dotenv
load_dotenv()

from psychopy import prefs
from psychopy.monitors import Monitor

# avoids delay in movie3 audio seek
prefs.hardware["audioLib"] = ["sounddevice"]
# prefs.hardware['general'] = ['glfw']

TR = 1.49 #seconds

OUTPUT_DIR = "output"

EYETRACKING_ROI = (60, 30, 660, 450)

EXP_SCREEN_XRANDR_NAME = "eDP-1"

EXP_MONITOR = Monitor(
    name='__blank__',
    width=55,
    distance=180,
    )

EXP_WINDOW = dict(
    size=(1280, 1024),
    screen=1 if os.name != 'nt' else 0, # don't ask why I reversed on windows
    fullscr=True,
    gammaErrorPolicy="warn",
    #waitBlanking=False,
)

EXP_MONITOR.setSizePix(EXP_WINDOW['size'])

CTL_WINDOW = dict(
    size=(1280, 1024),
    pos=(100, 0),
    screen=0 if os.name != 'nt' else 1, # don't ask why I reversed on windows
    gammaErrorPolicy="warn",
    #    swapInterval=0.,
    waitBlanking=False,  # avoid ctrl window to block the script in case of differing refresh rate.
)

FRAME_RATE = 60

# task parameters
INSTRUCTION_DURATION = 6

WRAP_WIDTH = 2

# port for meg setup
PARALLEL_PORT_ADDRESS = "/dev/parport0"
