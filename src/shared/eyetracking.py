import os, sys
import numpy as np
from psychopy import visual, core, data, logging

from ..task import task_base

MARKER_SIZE = 50
MARKER_FILL_COLOR = (.8,0,.5)
MARKER_DURATION_FRAMES = 240
MARKER_POSITIONS = np.asarray([(.25, .5), (0, .5), (0., 1.), (.5, 1.), (1., 1.),
    (1., .5), (1., 0.), (.5, 0.), (0., 0.), (.75, .5)])

class EyetrackerCalibration(task_base.Task):

    def __init__(self,*args,**kwargs):
        super().__init__(**kwargs)

    def instructions(self, exp_win, ctl_win):
        instruction_text = """We're going to calibrate the eyetracker.
Please look at the markers that appear on the screen."""
        screen_text = visual.TextStim(
            exp_win, text=instruction_text,
            alignHoriz="center", color = 'white')

        for frameN in range(FRAMERATE * STIMULI_DURATION):
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield()

    def run(self, exp_win, ctl_win, order='random', marker_fill_color=MARKER_FILL_COLOR):
        window_size_frame = window.size-MARKER_SIZE*2
        circle_marker = visual.Circle(
            exp_win, edges=64, units='pixels',
            lineColor=None,fillColor=marker_fill_color,
            autoLog=False)

        random_order = np.random.permutation(np.arange(len(MARKER_POSITIONS)))

        for site_id in random_order:
            marker_pos = MARKER_POSITIONS[site_id]
            pos = marker_pos*window_size_frame - window_size_frame/2
            circle_marker.pos = pos
            window.logOnFlip(level=logging.EXP,
                msg="calibrate_position,%d,%d,%d,%d"%(marker_pos[0],marker_pos[1], pos[0],pos[1]))
            for r in np.hstack([np.linspace(MARKER_SIZE,0,MARKER_DURATION_FRAMES/2),
                                np.linspace(0,MARKER_SIZE,MARKER_DURATION_FRAMES/2)]):
                circle_marker.radius = r
                circle_marker.draw(exp_win)
                circle_marker.draw(ctl_win)
                yield()


import cv2
sys.path.append('/home/basile/data/src/pupil/pupil_src/shared_modules/')
from pupil_detectors.detector_2d import Detector_2D
from pupil_detectors.detector_3d import Detector_3D
from methods import Roi

from . import config

class Frame(object):
    """docstring of Frame"""
    def __init__(self, timestamp, frame, index):
        self._frame = frame
        self.timestamp = timestamp
        self.index = index
        self._img = None
        self._gray = None
        self.jpeg_buffer = None
        self.yuv_buffer = None
        self.height, self.width, _ = frame.shape

    def copy(self):
        return Frame(self.timestamp, self._frame, self.index)

    @property
    def img(self):
        return self._frame

    @property
    def bgr(self):
        return self.img

    @property
    def gray(self):
        if self._gray is None:
            self._gray = self._frame.mean(-1).astype(self._frame.dtype)
        return self._gray

class EyeTracker():

    def __init__(self, ctl_win, video_input=0, roi=None, detector='2d'):
        self.ctl_win = ctl_win

        self._videocap = cv2.VideoCapture(video_input)
        ret, self.cv_frame = self._videocap.read()

        self._width = int(self._videocap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._height = int(self._videocap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.roi = roi
        if roi is None:
            self.roi = Roi((self._width, self._height))
        pos_roi_y =  config.CTL_EYE_VIDEO_POSITION[0] + self.roi.get()[0]
        pos_roi_x =  config.CTL_EYE_VIDEO_POSITION[1] + self.roi.get()[1]

        self._image_stim = visual.ImageStim(ctl_win, pos=config.CTL_EYE_VIDEO_POSITION)
        self._roi_stim = visual.Rect(
            ctl_win,
            pos=(pos_roi_x, pos_roi_y),
            width=self.roi.get()[4][1], height=self.roi.get()[4][0],
            units='pixels')
        self._pupil_stim = visual.Circle(
            ctl_win,
            radius=0,
            units='pixels')

        if detector == '2d':
            self._detector = Detector_2D()
        elif detector == '3d':
            self._detector = Detector_3D()

    def update(self):
        #capture
        ret, self.cv_frame = self._videocap.read()
        #detect
        p_frame = Frame(0, self.cv_frame, 0)
        pupils = self._detector.detect(p_frame, self.roi, False)

        #render image roi pupil
        self._image_stim.setImage(self.cv_frame/255.)
        self._image_stim.draw(self.ctl_win)
        self._roi_stim.draw(self.ctl_win)

        self._pupil_stim.pos = pupils['ellipse']['center']
        self._pupil_stim.radius = pupils['diameter']
        self._pupil_stim.draw()

        #TODO: log pupil positions, maybe in separate logfile

        return pupils

    def release(self):
        self._videocap.release()
#window = visual.Window(monitor=0,fullscr=True)
#lastLog = logging.LogFile("lastRun.log", level=logging.INFO, filemode='w')
#calibrate(window)
#logging.flush()
