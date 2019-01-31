import os, sys, datetime, time
import threading

from .zmq_tools import *
import msgpack

import numpy as np
from psychopy import visual, core, data, logging, event
from .ellipse import Ellipse

from ..tasks.task_base import Task
from . import config

INSTRUCTION_DURATION = 5

CALIBRATE_HOTKEY = 'c'
INSTRUCTION_DURATION = 5

MARKER_SIZE = 50
MARKER_FILL_COLOR = (.8,0,.5)
MARKER_DURATION_FRAMES = 240
MARKER_POSITIONS = np.asarray([(.25, .5), (0, .5), (0., 1.), (.5, 1.), (1., 1.),
    (1., .5), (1., 0.), (.5, 0.), (0., 0.), (.75, .5)])

# number of frames to eliminate at start and end of marker
CALIBRATION_LEAD_IN = 20
CALIBRATION_LEAD_OUT = 20
# remove pupil samples with low confidence
PUPIL_CONFIDENCE_THRESHOLD = .4

class EyetrackerCalibration(Task):

    def __init__(self,eyetracker, order='random', marker_fill_color=MARKER_FILL_COLOR, **kwargs):
        self.use_eyetracking = True
        self.order = order
        self.marker_fill_color = marker_fill_color
        super().__init__(**kwargs)
        self.eyetracker = eyetracker

    def instructions(self, exp_win, ctl_win):
        instruction_text = """We're going to calibrate the eyetracker.
Please look at the markers that appear on the screen."""
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
        print('calibration started')

        window_size_frame = exp_win.size-MARKER_SIZE*2
        print(window_size_frame)
        circle_marker = visual.Circle(
            exp_win, edges=64, units='pixels',
            lineColor=None,fillColor=self.marker_fill_color,
            autoLog=False)

        random_order = np.random.permutation(np.arange(len(MARKER_POSITIONS)))

        all_refs_per_flip = []
        all_pupils = []

        radius_anim = np.hstack([np.linspace(MARKER_SIZE,0,MARKER_DURATION_FRAMES/2),
                                 np.linspace(0,MARKER_SIZE,MARKER_DURATION_FRAMES/2)])

        pupil = None
        while pupil is None: # wait until we get at least a pupil
            pupil = self.eyetracker.get_pupil()
            yield

        exp_win.logOnFlip(level=logging.EXP,msg='eyetracker_calibration: starting at %f'%time.time())
        for site_id in random_order:
            marker_pos = MARKER_POSITIONS[site_id]
            pos = (marker_pos-.5)*window_size_frame
            circle_marker.pos = pos
            exp_win.logOnFlip(level=logging.EXP,
                msg="calibrate_position,%d,%d,%d,%d"%(marker_pos[0],marker_pos[1], pos[0],pos[1]))
            for f,r in enumerate(radius_anim):
                circle_marker.radius = r
                circle_marker.draw(exp_win)
                circle_marker.draw(ctl_win)

                pupil = self.eyetracker.get_pupil()

                exp_win.logOnFlip(level=logging.EXP,
                    msg="pupil: pos=(%f,%f), diameter=%d"%tuple(pupil['norm_pos']+[pupil['diameter']]))
                if f > CALIBRATION_LEAD_IN and f < len(radius_anim)-CALIBRATION_LEAD_OUT:
                    if pupil and pupil['confidence'] > PUPIL_CONFIDENCE_THRESHOLD:
                        pos_decenter = (pos/exp_win.size*2).tolist()
                        ref = {
                            'norm_pos': pos_decenter,
                            'screen_pos': pos_decenter,
                            'timestamp': pupil['timestamp']}
                        all_refs_per_flip.append(ref)
                        all_pupils.append(pupil)
                yield
        self.eyetracker.calibrate(all_pupils, all_refs_per_flip, exp_win.size)

from subprocess import Popen

class EyeTrackerClient(threading.Thread):

    def __init__(self, output_path, output_fname_base):
        super(EyeTrackerClient, self).__init__()
        self.stoprequest = threading.Event()
        self.lock = threading.Lock()

        self.pupil = None
        self.gaze = None

        self.output_path = output_path
        self.output_fname_base = output_fname_base
        self.record_dir = os.path.join(self.output_path, self.output_fname_base + '.pupil')
        os.makedirs(self.record_dir)

        self._pupil_process = Popen([
            'python3',
            os.path.join(os.environ['PUPIL_PATH'],'pupil_src','main.py'),
            'capture'])

        self._ctx = zmq.Context()
        self._req_socket = self._ctx.socket(zmq.REQ)
        self._req_socket.connect('tcp://localhost:50020')

        # start eye0 if not started yet (from pupil saved config)
        self.send_recv_notification({
            'subject':'eye_process.should_start.0',
            'eye_id':0, 'args':{}})
        # setup recorder output path
        # quit existing plugin
        self.send_recv_notification({
            'subject':'stop_plugin',
            'name':'Recorder',})
        self.send_recv_notification({
            'subject':'stop_plugin',
            'name':'Accuracy_Visualizer','args':{}})

        #restart with new params
        self.send_recv_notification({
            'subject':'start_plugin',
            'name':'Recorder','args':{'rec_path':self.record_dir,'rec_root_dir':self.record_dir,'raw_jpeg':False}})
        self.send_recv_notification({
            'subject':'start_plugin',
            'name':'Pupil_Remote','args':{}})

        self.send_recv_notification({'subject':'recording.should_start',})
        # wait for the whole schmilblick to boot
        time.sleep(4)

    def send_recv_notification(self, n):
        # REQ REP requirese lock step communication with multipart msg (topic,msgpack_encoded dict)
        self._req_socket.send_multipart((bytes('notify.%s'%n['subject'],'utf-8'), msgpack.dumps(n)))
        return self._req_socket.recv()

    def get_pupil_timestamp(self):
        self._req_socket.send('t') #see Pupil Remote Plugin for details
        return float(self._req_socket.recv())

    def join(self, timeout=None):
        self.stoprequest.set()
        # stop recording
        self.send_recv_notification({'subject':'recording.should_stop',})
        # stop world and children process
        self.send_recv_notification({'subject':'world_process.should_stop'})
        self._pupil_process.wait(timeout)

        super(EyeTrackerClient, self).join(timeout)

    def run(self):

        self._req_socket.send_string('SUB_PORT')
        ipc_sub_port = int(self._req_socket.recv())
        self.pupil_monitor = Msg_Receiver(self._ctx,'tcp://localhost:%d'%ipc_sub_port,topics=('gaze','pupil'))
        while not self.stoprequest.isSet():
            msg = self.pupil_monitor.recv()
            if not msg is None:
                topic, tmp = msg
                with self.lock:
                    if topic.startswith('pupil'):
                        self.pupil = tmp
                    if topic.startswith('gaze'):
                        self.gaze = tmp

        print('eyetracker listener: stopping')


    def get_pupil(self):
        with self.lock:
            return self.pupil

    def get_gaze(self):
        with self.lock:
            return self.gaze

    def calibrate(self, pupil_list, ref_list, frame_size):
        if len(pupil_list) < 100:
            # TODO: log
            return

        self.send_recv_notification({
            'subject':'start_plugin',
            'name':'Mock_Calibration',
            'args':{'frame_size': frame_size.tolist()}})

        self.send_recv_notification({
            'subject':'calibrate.from_external_data',
            'pupil_list':pupil_list,
            'ref_list':ref_list})



class GazeDrawer():

    def __init__(self, win):

        self.win = win
        self._gazepoint_stim = visual.Circle(
            self.win,
            radius=30,
            units='pixels',
            lineColor=(1,0,0),fillColor=None, lineWidth=2,
            autoLog=False)

    def draw_gazepoint(self, gaze):
        pos = gaze['norm_pos']
        self._gazepoint_stim.pos = (int(pos[0]/2*self.win.size[0]),
                                   int(pos[1]/2*self.win.size[1]))
        #self._gazepoint_stim.radius = self.pupils['diameter']/2
        #print(self._gazepoint_stim.pos, self._gazepoint_stim.radius)
        self._gazepoint_stim.draw(self.win)



def read_pl_data(fname):
    with open(fname, "rb") as fh:
        for data in msgpack.Unpacker(fh, raw=False, use_list=False):
            yield(data)
