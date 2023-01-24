import os, sys, datetime, time
import threading

from .zmq_tools import *
import msgpack

import numpy as np
from scipy.spatial.distance import pdist
from psychopy import visual, core, data, logging, event
from .ellipse import Ellipse

from ..tasks.task_base import Task
from . import config

INSTRUCTION_DURATION = 4
STARTCUE_DURATION = 2
FEEDBACK_DURATION = 3
CALIBRATE_HOTKEY = "c"

MARKER_FILL_COLOR = (0.8, 0, 0.5)

# 10-pt calibration
MARKER_POSITIONS_10 = np.asarray(
    [
        (0.25, 0.5),
        (0, 0.5),
        (0.0, 1.0),
        (0.5, 1.0),
        (1.0, 1.0),
        (1.0, 0.5),
        (1.0, 0.0),
        (0.5, 0.0),
        (0.0, 0.0),
        (0.75, 0.5),
    ]
)

# 9-pt calibration
MARKER_POSITIONS_9 = np.asarray(
    [
        (0.5, 0.5),
        (0, 0.5),
        (0.0, 1.0),
        (0.5, 1.0),
        (1.0, 1.0),
        (1.0, 0.5),
        (1.0, 0.0),
        (0.5, 0.0),
        (0.0, 0.0),
    ]
)


# Pupil settings
PUPIL_REMOTE_PORT = 50123
CAPTURE_SETTINGS = {
    "frame_size": [640, 480],
    "frame_rate": 250,
    "exposure_time": 4000,
    "global_gain": 1,
    "gev_packet_size": 1400,
    "uid": "Aravis-Fake-GV01",  # for test purposes
    #"uid": "MRC Systems GmbH-GVRD-MRC HighSpeed-MR_CAM_HS_0019",
}


class EyetrackerCalibration_targets(Task):
    def __init__(
        self,
        eyetracker,
        markers_order="random",
        markers=MARKER_POSITIONS_9,
        use_eyetracking=True,
        validation=False,
        feedback=False,
        **kwargs,
    ):
        self.markers_order = markers_order
        self.markers = markers
        self.marker_size = 20
        self.marker_duration_frames = 120 # 60 fps, 4s = 240; 60fps, 1.5s = 90 frames, 2s = 120
        super().__init__(use_eyetracking=use_eyetracking, **kwargs)
        self.eyetracker = eyetracker

        # number of frames to eliminate at start and end of marker
        self.calibration_lead_in = 20
        self.calibration_lead_out = 0

        self.validation = validation
        self.feedback = feedback

    def _instructions(self, exp_win, ctl_win):
        if self.validation:
            instruction_text = """Eyetracker Validation"""
        else:
            instruction_text = """Eyetracker Calibration

    Roll your eyes, then fixate on the CENTER of the markers"""
        screen_text = visual.TextStim(
            exp_win,
            text=instruction_text,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )

        # screen fades to dark during instructions, dark screen during calibration
        for frameN in range(config.FRAME_RATE * INSTRUCTION_DURATION):
            grey = [-float(frameN) / (config.FRAME_RATE*5) / INSTRUCTION_DURATION] * 3
            #grey = [-float(frameN) / config.FRAME_RATE / INSTRUCTION_DURATION] * 3
            exp_win.setColor(grey, colorSpace='rgb')
            #ctl_win.setColor(grey, colorSpace='rgb')
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield True

    def _setup(self, exp_win):
        self.use_fmri = False
        super()._setup(exp_win)
        self.fixation_dot = fixation_dot(exp_win, radius=self.marker_size)
        self.startcue = visual.Circle(exp_win, units='pix', pos=(0,0), radius=self.marker_size*0.5, lineWidth=0, fillColor=(1, 1, 1))

    def _pupil_cb(self, pupil):
        if pupil["timestamp"] > self.task_stop:
            self.eyetracker.unset_pupil_cb()
            return
        if pupil["timestamp"] > self.task_start:
            self._pupils_list.append(pupil)

    def _gaze_cb(self, gaze):
        if gaze["timestamp"] > self.task_stop:
            self.eyetracker.unset_gaze_cb()
            return
        if gaze["timestamp"] > self.task_start:
            self._gaze_list.append(gaze)

    def _run(self, exp_win, ctl_win):

        self.eyetracker.resume()
        roll_eyes_text = "Roll your eyes"

        text_roll = visual.TextStim(
            exp_win,
            text=roll_eyes_text,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
            )

        calibration_success = False
        while not calibration_success:
            start_calibration = self.validation
            while not start_calibration:
                allKeys = event.getKeys([CALIBRATE_HOTKEY])
                for key in allKeys:
                    if key == CALIBRATE_HOTKEY:
                        start_calibration = True
                text_roll.draw(exp_win)
                yield False
            if self.validation:
                logging.info("validation started")
                print("validation started")
            else:
                logging.info("calibration started")
                print("calibration started")

            window_size_frame = exp_win.size - 100 * 2 # 50 = previous MARKER_SIZE; hard-coded to maintain distance from screen edge regardless of target shape

            markers_order = np.arange(len(self.markers))
            if self.markers_order == "random":
                markers_order = np.random.permutation(markers_order)

            self.all_refs_per_flip = []
            self._pupils_list = []
            self._gaze_list = []

            self.task_start = time.monotonic()
            self.task_stop = np.inf
            self.eyetracker.set_pupil_cb(self._pupil_cb)
            self.eyetracker.set_gaze_cb(self._gaze_cb)

            while not len(self._pupils_list):  # wait until we get at least a pupil
                yield False

            if self.validation:
                exp_win.logOnFlip(
                    level=logging.EXP,
                    msg="eyetracker_validation: starting at %f" % time.time(),
                )
            else:
                exp_win.logOnFlip(
                    level=logging.EXP,
                    msg="eyetracker_calibration: starting at %f" % time.time(),
                )

            for frameN in range(config.FRAME_RATE * STARTCUE_DURATION):
                self.startcue.draw(exp_win)
                self.startcue.draw(ctl_win)
                yield True

            for site_id in markers_order:
                marker_pos = self.markers[site_id]
                pos = (marker_pos - 0.5) * window_size_frame # remove 0.5 since 0, 0 is the middle in psychopy
                for stim in self.fixation_dot:
                    stim.pos = pos
                if self.validation:
                    exp_win.logOnFlip(
                        level=logging.EXP,
                        msg="validate_position,%d,%d,%d,%d"
                        % (marker_pos[0], marker_pos[1], pos[0], pos[1]),
                    )
                else:
                    exp_win.logOnFlip(
                        level=logging.EXP,
                        msg="calibrate_position,%d,%d,%d,%d"
                        % (marker_pos[0], marker_pos[1], pos[0], pos[1]),
                    )
                exp_win.callOnFlip(
                    self._log_event, {"marker_x": pos[0], "marker_y": pos[1]}
                )
                for f in range(self.marker_duration_frames):
                    for stim in self.fixation_dot:
                        stim.draw(exp_win)
                        stim.draw(ctl_win)

                    if (
                        f > self.calibration_lead_in
                        and f < self.marker_duration_frames - self.calibration_lead_out
                    ):
                        screen_pos = pos + exp_win.size / 2
                        norm_pos = screen_pos / exp_win.size
                        ref = {
                            "norm_pos": norm_pos.tolist(),
                            "screen_pos": screen_pos.tolist(),
                            "timestamp": time.monotonic(),  # =pupil frame timestamp on same computer
                        }
                        self.all_refs_per_flip.append(ref)  # accumulate all refs
                    yield True
            yield True
            self.task_stop = time.monotonic()

            if self.validation:
                logging.info(
                    f"validating on {len(self._pupils_list)} pupils and {len(self.all_refs_per_flip)} markers"
                )

                print('Ǹumber of received gaze: ', str(len(self._gaze_list)))
                val_qc = self.eyetracker.validate(self._gaze_list, self.all_refs_per_flip)

                # If self.feedback = True, display calib results on screen
                if self.feedback:
                    dot_colors = [(-0.5, 1, -0.5), (1, 1, -0.5), (1, -0.5, -0.5)]
                    qc_dots = []

                for vqc in val_qc:
                    self._events[vqc['marker']].update(vqc)
                    if self.feedback:
                        pos = (np.array(vqc['norm_pos']) - 0.5) * window_size_frame
                        if 'good' in vqc:
                            fill_col = dot_colors[np.argmax([vqc['good'], vqc['fair'], vqc['poor']])]
                        else:
                            fill_col = (1, 1, 1) # white indicates no fixations reccorded for that marker
                        qc_dots.append(visual.Circle(exp_win, units='pix', pos=pos, radius=self.marker_size*0.8,
                                                     lineWidth=0, fillColor=fill_col))

                if self.feedback:
                    for frameN in range(config.FRAME_RATE * FEEDBACK_DURATION):
                        for qc_dot in qc_dots:
                            qc_dot.draw(exp_win)
                            qc_dot.draw(ctl_win)
                        yield True

                #exp_win.clearBuffer(color=True, depth=True)
                black_bgd = visual.Rect(exp_win, size=exp_win.size, lineWidth=0,
                                        #colorSpace='rgb', fillColor=(-1, -1, -1))
                                        colorSpace='rgb', fillColor=(-0.2, -0.2, -0.2))

                for frameN in range(5):
                    black_bgd.draw(exp_win)
                    black_bgd.draw(ctl_win)
                    yield True

                calibration_success = True

            else:
                logging.info(
                    f"calibrating on {len(self._pupils_list)} pupils and {len(self.all_refs_per_flip)} markers"
                )

                #exp_win.clearBuffer(color=True, depth=True)
                black_bgd = visual.Rect(exp_win, size=exp_win.size, lineWidth=0,
                                        #colorSpace='rgb', fillColor=(-1, -1, -1))
                                        colorSpace='rgb', fillColor=(-0.2, -0.2, -0.2))

                for frameN in range(5):
                    black_bgd.draw(exp_win)
                    black_bgd.draw(ctl_win)
                    yield True

                self.eyetracker.calibrate(self._pupils_list, self.all_refs_per_flip)
                while True:
                    notes = getattr(self.eyetracker, '_last_calibration_notification',None)
                    if notes:
                        calibration_success = notes['topic'].startswith("notify.calibration.successful")
                        if not calibration_success:
                            print('#### CALIBRATION FAILED: restart with <c> ####')
                        break
        self.eyetracker.pause()


    def stop(self, exp_win, ctl_win):
        self.eyetracker.unset_pupil_cb()
        self.eyetracker.unset_gaze_cb()
        yield

    def _save(self):
        if hasattr(self, "_pupils_list"):
            if self.validation:
                fname = self._generate_unique_filename("valid-data", "npz")
            else:
                fname = self._generate_unique_filename("calib-data", "npz")
            np.savez(fname, pupils=self._pupils_list,
                            gaze=self._gaze_list,
                            markers=self.all_refs_per_flip)


class EyetrackerCalibration(Task):
    def __init__(
        self,
        eyetracker,
        markers_order="random",
        marker_fill_color=MARKER_FILL_COLOR,
        markers=MARKER_POSITIONS_10,
        use_eyetracking=True,
        **kwargs,
    ):
        self.markers_order = markers_order
        self.markers = markers
        self.marker_size = 50
        self.marker_duration_frames = 240
        self.marker_fill_color = marker_fill_color
        super().__init__(use_eyetracking=use_eyetracking, **kwargs)
        self.eyetracker = eyetracker

        # number of frames to eliminate at start and end of marker
        self.calibration_lead_in = 20
        self.calibration_lead_out = 20

    def _instructions(self, exp_win, ctl_win):
        instruction_text = """We're going to calibrate the eyetracker.
Please look at the markers that appear on the screen.
While awaiting for the calibration to start you will be asked to roll your eyes."""
        screen_text = visual.TextStim(
            exp_win,
            text=instruction_text,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )

        for frameN in range(config.FRAME_RATE * INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield True

    def _setup(self, exp_win):
        self.use_fmri = False
        self.eyetracker.stop_capture()
        time.sleep(.1)
        self.eyetracker.start_capture()
        super()._setup(exp_win)

    def _pupil_cb(self, pupil):
        if pupil["timestamp"] > self.task_stop:
            self.eyetracker.unset_pupil_cb()
            return
        if pupil["timestamp"] > self.task_start:
            self._pupils_list.append(pupil)

    def _run(self, exp_win, ctl_win):

        roll_eyes_text = "Please roll your eyes ~2-3 times in clockwise and counterclockwise directions"

        instructions = visual.TextStim(
            exp_win,
            text=roll_eyes_text,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
            )

        self.eyetracker.resume()

        calibration_success = False
        while not calibration_success:
            while True:
                allKeys = event.getKeys([CALIBRATE_HOTKEY])
                start_calibration = False
                for key in allKeys:
                    if key == CALIBRATE_HOTKEY:
                        start_calibration = True
                if start_calibration:
                    break
                instructions.draw(exp_win)
                yield False
            logging.info("calibration started")
            print("calibration started")

            window_size_frame = exp_win.size - self.marker_size * 2
            circle_marker = visual.Circle(
                exp_win,
                edges=64,
                units="pix",
                lineColor=None,
                fillColor=self.marker_fill_color,
                autoLog=False,
            )

            markers_order = np.arange(len(self.markers))
            if self.markers_order == "random":
                markers_order = np.random.permutation(markers_order)

            self.all_refs_per_flip = []
            self._pupils_list = []

            radius_anim = np.hstack(
                [
                    np.linspace(self.marker_size, 0, self.marker_duration_frames // 2),
                    np.linspace(0, self.marker_size, self.marker_duration_frames // 2),
                ]
            )

            self.task_start = time.monotonic()
            self.task_stop = np.inf
            self.eyetracker.set_pupil_cb(self._pupil_cb)

            instructions.text = "Waiting for pupil"
            for _ in range(2):
                instructions.draw(exp_win)
                yield True
            while not len(self._pupils_list):  # wait until we get at least a pupil
                yield False

            exp_win.logOnFlip(
                level=logging.EXP,
                msg="eyetracker_calibration: starting at %f" % time.time(),
            )
            for site_id in markers_order:
                marker_pos = self.markers[site_id]
                pos = (marker_pos - 0.5) * window_size_frame
                circle_marker.pos = pos
                exp_win.logOnFlip(
                    level=logging.EXP,
                    msg="calibrate_position,%d,%d,%d,%d"
                    % (marker_pos[0], marker_pos[1], pos[0], pos[1]),
                )
                exp_win.callOnFlip(
                    self._log_event, {"marker_x": pos[0], "marker_y": pos[1]}
                )
                for f, r in enumerate(radius_anim):
                    circle_marker.radius = r
                    circle_marker.draw(exp_win)
                    circle_marker.draw(ctl_win)

                    if (
                        f > self.calibration_lead_in
                        and f < len(radius_anim) - self.calibration_lead_out
                    ):
                        screen_pos = pos + exp_win.size / 2
                        norm_pos = screen_pos / exp_win.size
                        ref = {
                            "norm_pos": norm_pos.tolist(),
                            "screen_pos": screen_pos.tolist(),
                            "timestamp": time.monotonic(),  # =pupil frame timestamp on same computer
                        }
                        self.all_refs_per_flip.append(ref)  # accumulate all refs
                    yield True
            yield True
            self.task_stop = time.monotonic()
            logging.info(
                f"calibrating on {len(self._pupils_list)} pupils and {len(self.all_refs_per_flip)} markers"
            )
            self.eyetracker.calibrate(self._pupils_list, self.all_refs_per_flip)
            while True:
                notes = getattr(self.eyetracker, '_last_calibration_notification',None)
                if notes:
                    calibration_success = notes['topic'].startswith("notify.calibration.successful")
                    if not calibration_success:
                        print('#### CALIBRATION FAILED: restart with <c> ####')
                    break



    def stop(self, exp_win, ctl_win):
        self.eyetracker.unset_pupil_cb()
        self.eyetracker.pause()
        yield

    def _save(self):
        if hasattr(self, "_pupils_list"):
            fname = self._generate_unique_filename("calib-data", "npz")
            np.savez(fname, pupils=self._pupils_list, markers=self.all_refs_per_flip)


class EyetrackerSetup(Task):
    def __init__(
        self,
        eyetracker,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.eyetracker = eyetracker

    def _setup(self, exp_win):
        self.use_fmri = False

    def _run(self, exp_win, ctl_win):

        self.eyetracker.resume()
        con_text_str = "Trying to establish connection to the eyetracker %s"

        con_text = visual.TextStim(
            exp_win,
            text=con_text_str % ' ...',
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
            )
        con_text.draw(exp_win)
        yield True

        while True:
            notif = self.eyetracker._aravis_notification
            if (
                notif and
                notif["subject"] == "aravis.start_capture.successful" and
                notif["target"] == "eye0" and
                notif["name"] == "Aravis_Source"):
                break

            self.eyetracker.start_source()
            con_text.text = con_text_str % 'failed, retrying'
            con_text.draw(exp_win)
            yield True
            time.sleep(3)
        self.eyetracker.pause()

from subprocess import Popen

from contextlib import contextmanager


@contextmanager
def nonblocking(lock):
    locked = lock.acquire(False)
    try:
        yield locked
    finally:
        if locked:
            lock.release()


class EyeTrackerClient(threading.Thread):

    EYE = "eye0"

    def __init__(self, output_path, output_fname_base, profile=False,
                 debug=False, use_targets=False, validate_calib=False):
        super(EyeTrackerClient, self).__init__()
        self.stoprequest = threading.Event()
        self.paused = True
        self.pause_cond = threading.Condition(threading.Lock())
        self.pause_cond.acquire()
        self.lock = threading.Lock()
        self._pupil_cb = self._gaze_cb = self._fix_cb = None

        self.pupil_monitor = None

        self.pupil = None
        self.gaze = None
        self.unset_pupil_cb()
        self.unset_gaze_cb()

        self.use_targets = use_targets
        self.validate_calib = validate_calib

        CAPTURE_SETTINGS["exposure_time"] = 4000

        self.output_path = output_path
        self.output_fname_base = output_fname_base
        self.record_dir = os.path.join(
            self.output_path, self.output_fname_base + ".pupil"
        )
        os.makedirs(self.record_dir, exist_ok=True)

        dev_opts = []
        if debug:
            dev_opts.append("--debug")
        if profile:
            dev_opts.append("--profile")

        pupil_logfile = open(os.path.join(self.record_dir, "pupil.log"), "wb")
        pupil_env = os.environ.copy()
        pupil_env.update({'ARV_DEBUG':'all:2'})

        self._pupil_process = Popen(
            [
                "python3",
                os.path.join(os.environ["PUPIL_PATH"], "pupil_src", "main.py"),
                "capture",
                "--port",
                str(PUPIL_REMOTE_PORT),
            ]
            + dev_opts,
            env=pupil_env,
            stdout=pupil_logfile,
            stderr=pupil_logfile,
        )

        self._ctx = zmq.Context()
        self._req_socket = self._ctx.socket(zmq.REQ)
        self._req_socket.connect(f"tcp://localhost:{PUPIL_REMOTE_PORT}")

        # stop eye1 if started: monocular eyetracking in the MRI
        notif = self.send_recv_notification(
            {"subject": "eye_process.should_stop.1", "eye_id": 1, "args": {}}
        )

        # start eye0 if not started yet (from pupil saved config)
        notif = self.send_recv_notification(
            {"subject": "eye_process.should_start.0", "eye_id": 0, "args": {}}
        )

        # wait for eye process to start before starting plugins
        time.sleep(1)

        # quit existing recorder plugin
        self.send_recv_notification(
            {
                "subject": "stop_plugin",
                "name": "Recorder",
            }
        )
        # restart recorder plugin with custom output settings
        self.send_recv_notification(
            {
                "subject": "start_plugin",
                "name": "Recorder",
                "args": {
                    "rec_root_dir": self.record_dir,
                    "session_name": self.output_fname_base + ".pupil",
                    "raw_jpeg": False,
                    "record_eye": True,
                },
            }
        )

        # restart 2d detector plugin with custom output settings
        self.send_recv_notification(
            {
                "subject": "start_eye_plugin",
                "name": "Detector2DPlugin",
                "target": self.EYE,
                "args": {
                    "properties": {
                        "intensity_range": 4,
                    }
                },
            }
        )

        # stop a bunch of eye plugins for performance
        for plugin in ["NDSI_Manager", "Pye3DPlugin"]:
            self.send_recv_notification(
                {
                    "subject": "stop_eye_plugin",
                    "target": self.EYE,
                    "name": plugin,
                }
            )
        self.start_source()

        self._req_socket.send_string("SUB_PORT")
        self._ipc_sub_port = int(self._req_socket.recv())
        logging.info(f"ipc_sub_port: {self._ipc_sub_port}")

    def start_source(self):
        self.send_recv_notification(
            {
                "subject": "start_eye_plugin",
                "name": "Aravis_Source",
                "target": self.EYE,
                "args": CAPTURE_SETTINGS,
            }
        )


    def start_capture(self):
        self.send_recv_notification(
            {
                "subject": "capture.should_start",
                "target": self.EYE
            }
        )

    def stop_capture(self):
        self.send_recv_notification(
            {
                "subject": "capture.should_stop",
                "target": self.EYE
            }
        )


    def send_recv_notification(self, n):
        # REQ REP requires lock step communication with multipart msg (topic,msgpack_encoded dict)
        self._req_socket.send_multipart(
            (bytes("notify.%s" % n["subject"], "utf-8"), msgpack.dumps(n))
        )
        return self._req_socket.recv()

    def get_pupil_timestamp(self):
        self._req_socket.send("t")  # see Pupil Remote Plugin for details
        return float(self._req_socket.recv())

    def start_recording(self, recording_name):
        logging.info("starting eyetracking recording")
        return self.send_recv_notification(
            {"subject": "recording.should_start", "session_name": recording_name}
        )

    def stop_recording(self):
        logging.info("stopping eyetracking recording")
        return self.send_recv_notification({"subject": "recording.should_stop"})

    def join(self, timeout=None):
        self.stoprequest.set()
        # stop recording
        self.send_recv_notification(
            {
                "subject": "recording.should_stop",
            }
        )
        # stop world and children process
        self.send_recv_notification({"subject": "world_process.should_stop"})
        self.send_recv_notification({"subject": "launcher_process.should_stop"})
        self._pupil_process.wait(timeout)
        self._pupil_process.terminate()
        time.sleep(1 / 60.0)
        super(EyeTrackerClient, self).join(timeout)

    def pause(self):
        self.paused = True
        print('pause eyetracking coms')
        self.pause_cond.acquire()
        del self.pupil_monitor

    def resume(self):
        if self.paused:
            print('resume eyetracking coms')
            self.pupil_monitor = Msg_Receiver(

                self._ctx, f"tcp://localhost:{self._ipc_sub_port}",
                topics=("gaze", "pupil", "fixations", "notify.calibration.successful", "notify.calibration.failed", "notify.aravis")

            )
            self.paused = False
            self.pause_cond.notify()
            self.pause_cond.release()

    def run(self):

        self._aravis_notification = None

        while not self.stoprequest.isSet():
            if self.paused:
                time.sleep(1e-3)
                continue
            with self.pause_cond:
                msg = self.pupil_monitor.recv()
                if not msg is None:
                    topic, tmp = msg
                    with self.lock:
                        if topic.startswith("pupil"):
                            self.pupil = tmp
                            if self._pupil_cb:
                                self._pupil_cb(tmp)
                        elif topic.startswith("gaze"):
                            self.gaze = tmp
                            if self._gaze_cb:
                                self._gaze_cb(tmp)
                        elif topic.startswith("fixations"):
                            self.fixation = tmp
                            if self._fix_cb:
                                self._fix_cb(tmp)
                        elif topic.startswith("notify.calibration"):
                            self._last_calibration_notification = tmp
                        elif topic.startswith("notify.aravis.start_capture"):
                            self._aravis_notification = tmp
        logging.info("eyetracker listener: stopping")

    def set_pupil_cb(self, pupil_cb):
        self._pupil_cb = pupil_cb

    def set_gaze_cb(self, gaze_cb):
        self._gaze_cb = gaze_cb

    def unset_pupil_cb(self):
        self._pupil_cb = None

    def unset_gaze_cb(self):
        self._gaze_cb = None

    def get_pupil(self):
        with nonblocking(self.lock) as locked:
            if locked:
                return self.pupil

    def get_gaze(self):
        with nonblocking(self.lock) as locked:
            if locked:
                return self.gaze


    def get_marker_dictionary(self, ref_list):
        position_list = []
        markers_dict = {}
        count = 0

        for i in range(len(ref_list)):
            m = ref_list[i]
            if not (m['norm_pos']) in position_list:
                markers_dict[count] = {
                    'norm_pos': m['norm_pos'],
                    'screen_pos': m['screen_pos'],
                    'onset': m['timestamp'],
                    'offset': -1.0,
                }
                count += 1
                position_list.append(m['norm_pos'])
            elif m['timestamp'] > markers_dict[count-1]['offset']:
                markers_dict[count-1]['offset'] = m['timestamp']

        return markers_dict


    def assign_gaze_to_markers(self, gaze_list, markers_dict):
        '''
        Assign gaze/fixations to markers based on their onset.
        A fixation is assigned to a marker if its ONSET overlaps with the time the marker is on the screen
        '''
        i = 0
        #print(markers_dict[0]['onset'], fixation_list[0]['timestamp'])
        for count in range(len(markers_dict.keys())):
            marker = markers_dict[count]
            gaze_data = {'timestamps': [],
                         'norm_pos': [],
                         'confidence': [],
                        }

            while i < len(gaze_list) and gaze_list[i]['timestamp'] < marker['onset']:
                i += 1

            while i < len(gaze_list) and gaze_list[i]['timestamp'] < marker['offset']:
                gaze = gaze_list[i]
                gaze_data['timestamps'].append(gaze['timestamp'])
                gaze_data['norm_pos'].append(gaze['norm_pos'])
                gaze_data['confidence'].append(gaze['confidence'])
                i += 1

            markers_dict[count]['gaze_data'] = gaze_data

        return markers_dict


    def gaze_to_marker_distances(self, markers_dict, conf_thresh = 0.9):
        '''
        estimated eye-to-screen distance in pixels
        based on screen dim in pixels ((1280, 1024)) and screen deg of visual angle (17.5, 14)
        '''
        dist_in_pix = 4164 # in pixels

        val_qc = []
        print('Distance between gaze and target in degrees of visual angle')
        print('Good < 0.5 deg ; Fair = [0.5, 1.5[ deg ; Poor >= 1.5 deg')

        for count in range(len(markers_dict.keys())):
            m = markers_dict[count]
            print('Marker ' + str(count) + ', Normalized position: ' +  str(m['norm_pos']))
            # transform marker's normalized position into dim = (3,) vector in pixel space
            m_vecpos = np.concatenate(((np.array(m['norm_pos']) - 0.5)*(1280, 1024), np.array([dist_in_pix])), axis=0)

            if len(m['gaze_data']['timestamps']) > 0:
                # filtrate gaze based on confidence threshold
                g_conf = np.array(m['gaze_data']['confidence'])
                g_filter = g_conf > conf_thresh

                g_pos = np.array(m['gaze_data']['norm_pos'])[g_filter]
                g_times = np.array(m['gaze_data']['timestamps'])[g_filter]

                gaze = (g_pos - 0.5)*(1280, 1024)
                gaze_vecpos = np.concatenate((gaze, np.repeat(dist_in_pix, len(gaze)).reshape((-1, 1))), axis=1)

                distances = []
                for gz_vec in gaze_vecpos:
                    vectors = np.stack((m_vecpos, gz_vec), axis=0)
                    distance = np.rad2deg(np.arccos(1.0 - pdist(vectors, metric='cosine')))
                    distances.append(distance[0])

                distances = np.array(distances)
                assert(len(distances)==len(g_times))
                markers_dict[count]['gaze_data']['distances'] = {'distances': distances,
                                                                 'timestamps': g_times,
                                                                 }

                num_gz = len(distances)
                good = np.sum(distances < 0.5) / num_gz
                fair = np.sum((distances >= 0.5)*(distances < 1.5)) / num_gz
                poor = np.sum(distances >= 1.5) / num_gz

                print('Total gaze:' + str(num_gz) + ' , Good:' + str(good) + ' , Fair:' + str(fair) + ' , Poor:' + str(poor))
                val_qc.append({
                    'marker': count,
                    'norm_pos': m['norm_pos'],
                    'num_gz': num_gz,
                    'good': good,
                    'fair': fair,
                    'poor': poor
                })
            else:
                val_qc.append({
                    'marker': count,
                    'norm_pos': m['norm_pos'],
                    'num_gz': 0
                })

        return markers_dict, val_qc


    def interleave_calibration(self, tasks):
        calibration_index=0
        for task in tasks:
            if task.use_eyetracking:
                calibration_index += 1
                if self.use_targets:
                    yield EyetrackerCalibration_targets(
                        self,
                        name=f"eyeTrackercalibration-{calibration_index}"
                        )
                else:
                    yield EyetrackerCalibration(
                        self,
                        name=f"eyeTrackercalibration-{calibration_index}"
                        )
                if self.validate_calib:
                    yield EyetrackerCalibration_targets(
                        self,
                        name=f"eyeTrackercalib-validate-{calibration_index}",
                        validation=True
                        )
            yield task

    def calibrate(self, pupil_list, ref_list):
        if len(pupil_list) < 100:
            logging.error("Calibration: not enough pupil captured for calibration")
            # return

        # TODO: check num of quality pupils per fixation points, set quality threshold...

        calib_data = {"ref_list": ref_list, "pupil_list": pupil_list}

        logging.info("sending calibration data to pupil")
        calib_res = self.send_recv_notification(
            {
                "subject": "start_plugin",
                "name": "Gazer2D",
                "args": {"calib_data": calib_data},
                "raise_calibration_error": False,
            }
        )

    def validate(self, gaze_list, ref_list):

        markers_dict = self.get_marker_dictionary(ref_list)
        markers_dict = self.assign_gaze_to_markers(gaze_list, markers_dict)
        markers_dict, val_qc = self.gaze_to_marker_distances(markers_dict, conf_thresh = 0.9)

        return val_qc

class GazeDrawer:
    def __init__(self, win):

        self.win = win
        self._gazepoint_stim = visual.Circle(
            self.win,
            radius=30,
            units="pix",
            lineColor=(1, 0, 0),
            fillColor=None,
            lineWidth=2,
            autoLog=False,
        )

    def draw_gazepoint(self, gaze):
        pos = gaze["norm_pos"]
        self._gazepoint_stim.pos = (
            int(pos[0] / 2 * self.win.size[0]),
            int(pos[1] / 2 * self.win.size[1]),
        )
        # self._gazepoint_stim.radius = self.pupils['diameter']/2
        # print(self._gazepoint_stim.pos, self._gazepoint_stim.radius)
        self._gazepoint_stim.draw(self.win)


def read_pl_data(fname):
    with open(fname, "rb") as fh:
        for data in msgpack.Unpacker(fh, raw=False, use_list=False):
            yield (data)


def fixation_dot(win, **kwargs):
    radius = kwargs.pop('radius', 20)
    kwargs = {
        'lineColor': (1,-.5,-.5),
        'fillColor': (1,1,1),
        'units': 'pix',
        **kwargs
    }
    circle = visual.Circle(win, lineWidth=radius*.4, **kwargs, radius=radius)
    dot = visual.Circle(win, units=kwargs["units"], radius=radius*.25, lineWidth=0, fillColor=(-1,-1,-1))
    return (circle, dot)
