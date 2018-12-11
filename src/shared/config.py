OUTPUT_DIR = 'output'

EYETRACKING_ROI = (60,30,660,450)

EXP_WINDOW = dict(
    size = (800,600),
    screen=1,
    fullscr=True,
)

CTL_WINDOW = dict(
    size = (800,600),
    pos = (100,0),
    screen=0
)

EYE_WINDOW = dict(
    size = (720,480),
    screen=0,
    units='pix',
    pos=(CTL_WINDOW['size'][0]+CTL_WINDOW['pos'][0],0)
)

FRAME_RATE=60
