import numpy as np
from psychopy import visual, core, data, logging, event
from ..shared.ellipse import Ellipse
import time
from .task_base import Task
from ..shared import config

# Constants
CALIBRATE_HOTKEY = 'c'
INSTRUCTION_DURATION = 5
MARKER_SIZE = 50
MARKER_FILL_COLOR = (.0,1,.0)
MARKER_DURATION_FRAMES = 120 # 2 seconds at 60fps
MARKER_DURATION_FRAMES_SP = 240 # 4 seconds to cross the screen
DIRECTIONS = [0,1,2,3]
REPETITIONS = 10
DIREC_NAMES = ['left', 'right', 'up', 'down']
DIREC_POS = np.asarray([((0,0.5),(1,0.5)), # left
                        ((1,0.5),(0,0.5)), # right
                        ((0.5,0),(0.5,1)), # up
                        ((0.5,1),(0.5,0))]) # down # [direction][start/end][x/y]
DIREC_VECTOR = DIRECTIONS * REPETITIONS


class EyetrackerTask(Task):

    def __init__(self, order='random', marker_fill_color=MARKER_FILL_COLOR, **kwargs):
        self.order = order
        self.marker_fill_color = marker_fill_color
        super().__init__(**kwargs)

    def instructions(self, exp_win, ctl_win):
        instruction_text = """Please look at the markers that appear on the screen."""
        screen_text = visual.TextStim(
            exp_win, text=instruction_text,
            alignHoriz="center", color = 'white', wrapWidth=config.WRAP_WIDTH)

        for frameN in range(config.FRAME_RATE * INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield()

    def _setup(self, exp_win):
        self.use_fmri = False

    def _run(self, exp_win, ctl_win):
        while True:
            allKeys = event.getKeys([CALIBRATE_HOTKEY])
            start_calibration = False
            for key in allKeys:
                if key == CALIBRATE_HOTKEY:
                    start_calibration = True
            if start_calibration:
                break
            yield
        window_size_frame = exp_win.size-MARKER_SIZE*2
        scr_ratio = window_size_frame[0]/window_size_frame[1]
        print(window_size_frame)
        circle_marker = visual.Circle(
            exp_win, edges=64, units='pixels',
            lineColor=None,fillColor=self.marker_fill_color,
            autoLog=False)

        random_order = np.random.permutation(np.arange(len(DIREC_VECTOR)))
        random_order_SP = np.random.permutation(np.arange(len(DIREC_VECTOR)))


        all_refs_per_flip = []
        all_pupils = []

        radius_anim = np.hstack([np.linspace(MARKER_SIZE,0,MARKER_DURATION_FRAMES/2),
                                 np.linspace(0,MARKER_SIZE,MARKER_DURATION_FRAMES/2)])

        exp_win.logOnFlip(level=logging.EXP,msg='eyetracker_calibration: starting at %f'%time.time())
        # Run saccades
        for site_id in random_order:
            current_direc = DIREC_VECTOR[site_id]
            for marker_pos in DIREC_POS[current_direc]:
                pos = (marker_pos-.5)*window_size_frame
                circle_marker.pos = pos
                exp_win.logOnFlip(level=logging.EXP,
                msg="calibrate_Saccade,%s,%d,%d,%d,%d"%(DIREC_NAMES[current_direc],marker_pos[0],marker_pos[1], pos[0],pos[1]))
                if self.use_meg:
                    meg.send_signal(meg.MEG_eyemvt['sacc_{}'.format(DIREC_NAMES[current_direc])])
                for f,r in enumerate(radius_anim):
                    circle_marker.radius = r
                    circle_marker.draw(exp_win)
                    circle_marker.draw(ctl_win)
                    yield

        # Run smooth poursuits
        for site_id in random_order_SP:
            current_direc = DIREC_VECTOR[site_id]
            marker_pos_start = (DIREC_POS[current_direc][0]-.5)*[window_size_frame[1]] # in smooth poursuit we want the distance and speed to be constant between v/h
            marker_pos_stop = (DIREC_POS[current_direc][1]-.5)*[window_size_frame[1]] # so we use only the shortest distance (likely constrained by vertical)
            pos_anim = np.vstack([np.linspace(marker_pos_start[0], marker_pos_stop[0], MARKER_DURATION_FRAMES_SP),
                              np.linspace(marker_pos_start[1], marker_pos_stop[1], MARKER_DURATION_FRAMES_SP)])
            exp_win.logOnFlip(level=logging.EXP,
            msg="calibrate_SmoothPoursuit,%s,%d,%d,%d,%d"%(DIREC_NAMES[current_direc],marker_pos_start[0],marker_pos_start[1], marker_pos_stop[0],marker_pos_stop[1]))
            if self.use_meg:
                meg.send_signal(meg.MEG_eyemvt['SP_{}'.format(DIREC_NAMES[current_direc])])
            for f in range(pos_anim.shape[1]):
                circle_marker.pos = tuple(pos_anim[:,f])
                circle_marker.radius = MARKER_SIZE
                circle_marker.draw(exp_win)
                circle_marker.draw(ctl_win)
                yield
