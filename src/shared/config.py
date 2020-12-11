from psychopy import prefs

# avoids delay in movie3 audio seek
prefs.hardware["audioLib"] = ["sounddevice"]
# prefs.hardware['general'] = ['glfw']

OUTPUT_DIR = "output"

EYETRACKING_ROI = (60, 30, 660, 450)

EXP_SCREEN_XRANDR_NAME = "eDP-1"

EXP_WINDOW = dict(
    size=(1280, 1024),
    screen=1,
    fullscr=True,
    gammaErrorPolicy="warn",
    #waitBlanking=False,
)

CTL_WINDOW = dict(
    size=(1280, 1024),
    pos=(100, 0),
    screen=0,
    gammaErrorPolicy="warn",
    #    swapInterval=0.,
    waitBlanking=False,  # avoid ctrl window to block the script in case of differing refresh rate.
)

FRAME_RATE = 60

# task parameters
INSTRUCTION_DURATION = 6

WRAP_WIDTH = 1

# port for meg setup
PARALLEL_PORT_ADDRESS = "/dev/parport0"
