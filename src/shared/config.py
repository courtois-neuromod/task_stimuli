from psychopy import prefs

# avoids delay in movie3 audio seek
prefs.hardware['audioLib'] = ['sounddevice']


OUTPUT_DIR = 'output'

EYETRACKING_ROI = (60,30,660,450)

EXP_WINDOW = dict(
    #size = (1280,1024),
    #size = (1024, 768),
    size = (1920, 1080),
    screen=1,
    fullscr=True,
    gammaErrorPolicy='warn',
)

CTL_WINDOW = dict(
    size = (1920, 1080),
    #size = (1280, 1024),
    pos = (100,0),
    screen=0,
    gammaErrorPolicy='warn',
)

FRAME_RATE=60

# task parameters
INSTRUCTION_DURATION = 6

WRAP_WIDTH = 1

# port for meg setup
PARALLEL_PORT_ADDRESS = '/dev/parport0'
