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

EXP_SCREEN_XRANDR_NAME = "DP-2"


EXP_MONITOR = Monitor(
    name='__blank__',
    width=55,
    distance=180,
    )

EXP_WINDOW = dict(
    size=(1920, 1080),
    screen=1,
    fullscr=True,
    gammaErrorPolicy="warn",
    #waitBlanking=False,
)

EXP_MONITOR.setSizePix(EXP_WINDOW['size'])

CTL_WINDOW = dict(
    size=(1280, 1024),
    pos=(100, 0),
    screen=0,
    gammaErrorPolicy="warn",
    #    swapInterval=0.,
    waitBlanking=False,  # avoid ctrl window to block the script in case of differing refresh rate.
)

FRAME_RATE = 120

# task parameters
INSTRUCTION_DURATION = 3

WRAP_WIDTH = 2

# port for meg setup
PARALLEL_PORT_ADDRESS = "/dev/parport1"
