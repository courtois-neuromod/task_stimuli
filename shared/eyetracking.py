import os, sys
import numpy as np
from psychopy import visual, core, data, logging

MARKER_SIZE = 50
MARKER_FILL_COLOR = (.8,0,.5)
MARKER_DURATION_FRAMES = 240
MARKER_POSITIONS = np.asarray([(.25, .5), (0, .5), (0., 1.), (.5, 1.), (1., 1.),
    (1., .5), (1., 0.), (.5, 0.), (0., 0.), (.75, .5)])

def calibrate(window=None, order='random', marker_fill_color=MARKER_FILL_COLOR):
    if window is None:
        window = visual.Window()

    window_size_frame = window.size-MARKER_SIZE*2
    circle_marker = visual.Circle(
        window, edges=64, units='pixels',
        lineColor=None,fillColor=marker_fill_color,
        autoLog=False)

    random_order = np.random.permutation(np.arange(len(MARKER_POSITIONS)))

    for site_id in random_order:
        marker_pos = MARKER_POSITIONS[site_id]
        pos = marker_pos*window_size_frame - window_size_frame/2
        circle_marker.pos = pos
        window.logOnFlip(level=logging.EXP,
            msg="calibrate_position,%d,%d,%d,%d"%(marker_pos[0],marker_pos[1], pos[0],pos[1]))
        for r in np.hstack([np.linspace(MARKER_SIZE,0,120),
                            np.linspace(0,MARKER_SIZE,120)]):
            circle_marker.radius = r
            circle_marker.draw()
            window.flip()

window = visual.Window(monitor=0,fullscr=True)
lastLog = logging.LogFile("lastRun.log", level=logging.INFO, filemode='w')
calibrate(window)
logging.flush()
