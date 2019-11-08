from psychopy import prefs

# avoids delay in movie3 audio seek
prefs.general['audioLib'] = ['sounddevice']


OUTPUT_DIR = 'output'

EYETRACKING_ROI = (60,30,660,450)

EXP_WINDOW = dict(
#    size = (800,600),
    #size = (1024,768),
    size = (1280,1024),
    screen=1,
    fullscr=True,
)

CTL_WINDOW = dict(
    size = (1024,768),
    pos = (100,0),
    screen=0
)

FRAME_RATE=60

# task parameters
INSTRUCTION_DURATION = 6

WRAP_WIDTH = 1.6

# port for meg setup
PARALLEL_PORT_ADDRESS = '/dev/parport0'
