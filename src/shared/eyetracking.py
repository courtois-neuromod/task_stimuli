import os, sys
import numpy as np
from psychopy import visual, core, data, logging

from ..tasks.task_base import Task
from . import config

MARKER_SIZE = 50
MARKER_FILL_COLOR = (.8,0,.5)
MARKER_DURATION_FRAMES = 240
MARKER_POSITIONS = np.asarray([(.25, .5), (0, .5), (0., 1.), (.5, 1.), (1., 1.),
    (1., .5), (1., 0.), (.5, 0.), (0., 0.), (.75, .5)])

PUPIL_CONFIDENCE_THRESHOLD = .4

class EyetrackerCalibration(Task):

    def __init__(self,eyetracker, *args,**kwargs):
        kwargs['use_eyetracking'] = True
        super().__init__(**kwargs)
        self.eyetracker = eyetracker

    def instructions(self, exp_win, ctl_win):
        instruction_text = """We're going to calibrate the eyetracker.
Please look at the markers that appear on the screen."""
        screen_text = visual.TextStim(
            exp_win, text=instruction_text,
            alignHoriz="center", color = 'white')

        for frameN in range(config.FRAME_RATE * 5):
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield()

    def run(self, exp_win, ctl_win, order='random', marker_fill_color=MARKER_FILL_COLOR):
        window_size_frame = exp_win.size-MARKER_SIZE*2
        circle_marker = visual.Circle(
            exp_win, edges=64, units='pixels',
            lineColor=None,fillColor=marker_fill_color,
            autoLog=False)

        random_order = np.random.permutation(np.arange(len(MARKER_POSITIONS)))

        all_refs_per_flip = []
        all_pupils_normpos = []

        radius_anim = np.hstack([np.linspace(MARKER_SIZE,0,MARKER_DURATION_FRAMES/2),
                                 np.linspace(0,MARKER_SIZE,MARKER_DURATION_FRAMES/2)])

        for site_id in random_order:
            marker_pos = MARKER_POSITIONS[site_id]
            pos = marker_pos*window_size_frame - window_size_frame/2
            circle_marker.pos = pos
            exp_win.logOnFlip(level=logging.EXP,
                msg="calibrate_position,%d,%d,%d,%d"%(marker_pos[0],marker_pos[1], pos[0],pos[1]))
            for f,r in enumerate(radius_anim):
                circle_marker.radius = r
                circle_marker.draw(exp_win)
                circle_marker.draw(ctl_win)

                if f > 30 and f < len(radius_anim)-10:
                    pupil = self.eyetracker.pupils
                    if pupil['confidence'] > PUPIL_CONFIDENCE_THRESHOLD:
                        all_refs_per_flip.append(marker_pos)
                        all_pupils_normpos.append(pupils['norm_pos'])
                yield
        self.eyetracker.calibrate(all_refs_per_flip, all_pupils_normpos)

import threading
import cv2
sys.path.append('/home/basile/data/src/pupil/pupil_src/shared_modules/')
from pupil_detectors.detector_2d import Detector_2D
from pupil_detectors.detector_3d import Detector_3D
import calibration_routines.calibrate
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

class EyeTracker(threading.Thread):

    def __init__(self, ctl_win, video_input=0, roi=None, detector='2d'):
        super(EyeTracker, self).__init__()
        self.ctl_win = ctl_win
        self.eye_win = visual.Window(**config.EYE_WINDOW)

        self._videocap = cv2.VideoCapture(video_input)
        ret, self.cv_frame = self._videocap.read()

        self._width = int(self._videocap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._height = int(self._videocap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.roi = roi
        if roi is None:
            self.roi = Roi((self._width, self._height))

            #self.roi = Roi((75,50,self._width-150, self._height-100))
            print(self.roi.get())
        pos_roi_y =  self.roi.get()[0]
        pos_roi_x =  self.roi.get()[1]

        self._image_stim = visual.ImageStim(
            self.eye_win,
            size=(self._width,self._height),
            units='pixels')
        self._roi_stim = visual.Rect(
            self.eye_win,
            pos=(pos_roi_x, pos_roi_y),
            width=self.roi.get()[4][0], height=self.roi.get()[4][1],
            units='pixels',
            lineColor=(1,0,0))
        self._pupil_stim = visual.Circle(
            self.eye_win,
            radius=0,
            units='pixels')

        self._gazepoint_stim = visual.Circle(
            self.ctl_win,
            radius=30,
            units='pixels')

        if detector == '2d':
            self._detector = Detector_2D()
        elif detector == '3d':
            self._detector = Detector_3D()

        #TODO: load settings and/or GUI
        self._detector.get_settings()["pupil_size_min"] = 40
        self._detector.get_settings()["pupil_size_max"] = 140
        self._detector.get_settings()["intensity_range"] = 10
        print(self._detector.get_settings())

        self.pupils = None
        self.stoprequest = threading.Event()

    def join(self, timeout=None):
        self.stoprequest.set()
        super(EyeTracker, self).join(timeout)
        self.release()

    def run(self):
        while not self.stoprequest.isSet():
            self.update()
            self.draw()

    def update(self):
        #capture
        ret, self.cv_frame = self._videocap.read()
        #detect
        p_frame = Frame(0, self.cv_frame, 0)
        self.pupils = self._detector.detect(p_frame, self.roi, False)

    def draw(self):
        #render image roi pupil
        self._image_stim.setImage(self.cv_frame/255.)
        self._image_stim.draw(self.eye_win)

        self._roi_stim.draw(self.eye_win)

        center = self.pupils['ellipse']['center']
        self._pupil_stim.pos = (center[0]-self._width/2, center[1]-self._height/2)
        self._pupil_stim.radius = self.pupils['diameter']/2
        self._pupil_stim.draw(self.eye_win)

        #TODO: log pupil positions, maybe in separate logfile

        self.eye_win.flip()

    def draw_gazepoint(self,win):
        if hasattr(self,'map_fn'):
            self.pos_cal = self.map_fn(self.pupils['norm_pos'])
            self._gazepoint_stim.pos = ((self.pos_cal[0]-.5)*self.ctl_win.size[0],
                                        (self.pos_cal[1]-.5)*self.ctl_win.size[1])
            #self._gazepoint_stim.radius = self.pupils['diameter']/2
            #print(self._gazepoint_stim.pos, self._gazepoint_stim.radius)
        self._gazepoint_stim.draw(win)

    def release(self):
        self._videocap.release()

    def calibrate(self, all_refs_per_flip, all_pupils_normpos):
        all_points = np.hstack([all_refs_per_flip, all_pupils_normpos])
        print(all_points)
        self.map_fn, inliers, params = calibration_routines.calibrate.calibrate_2d_polynomial(
            all_points,
            (self._width,self._height),
            binocular=False)


#window = visual.Window(monitor=0,fullscr=True)
#lastLog = logging.LogFile("lastRun.log", level=logging.INFO, filemode='w')
#calibrate(window)
#logging.flush()
