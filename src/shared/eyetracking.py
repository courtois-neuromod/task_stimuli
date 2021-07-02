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

CALIBRATE_HOTKEY = "c"
INSTRUCTION_DURATION = 5

MARKER_SIZE = 50
MARKER_FILL_COLOR = (0.8, 0, 0.5)
MARKER_DURATION_FRAMES = 240
MARKER_POSITIONS = np.asarray(
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

# number of frames to eliminate at start and end of marker
CALIBRATION_LEAD_IN = 20
CALIBRATION_LEAD_OUT = 20

# Pupil settings
PUPIL_REMOTE_PORT = 50123
CAPTURE_SETTINGS = {
    "frame_size": [640, 480],
    "frame_rate": 250,
    "exposure_time": 4000,
    "global_gain": 1,
    "auto_noise_suppression": True,
    #"gev_packet_size": 9140,
    #"uid": "Aravis-Fake-GV01",  # for test purposes
    "uid": "MRC Systems GmbH-GVRD-MRC HighSpeed-MR_CAM_HS_0014",
}


class EyetrackerCalibration(Task):
    def __init__(
        self,
        eyetracker,
        markers_order="random",
        marker_fill_color=MARKER_FILL_COLOR,
        markers=MARKER_POSITIONS,
        use_eyetracking=True,
        **kwargs,
    ):
        self.markers_order = markers_order
        self.markers = markers
        self.marker_fill_color = marker_fill_color
        super().__init__(use_eyetracking=use_eyetracking, **kwargs)
        self.eyetracker = eyetracker

    def _instructions(self, exp_win, ctl_win):

        instruction_text = """Veuillez tournez vos yeux dans toutes les directions.
Des marqueurs apparaitront à l'écran, veuillez les fixer."""
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
        super()._setup(exp_win)

    def _pupil_cb(self, pupil):
        if pupil["timestamp"] > self.task_stop:
            self.eyetracker.unset_pupil_cb()
            return
        if pupil["timestamp"] > self.task_start:
            self._pupils_list.append(pupil)

    def _run(self, exp_win, ctl_win):
        calibration_success = False
        self.task_stop = np.inf
        task_first_attempt_start = time.monotonic()
        print("A")
        while not calibration_success:# and self.task_stop - task_first_attempt_start < 60.:
            print("CALIB LOOP")
            print("KEY LOOP")
            while True:
                allKeys = event.getKeys([CALIBRATE_HOTKEY])
                start_calibration = False
                for key in allKeys:
                    if key == CALIBRATE_HOTKEY:
                        start_calibration = True
                if start_calibration:
                    break
                text_roll.draw(exp_win)
                yield False
            print("KEY LOOP END")
            logging.info("calibration started")
            print("calibration started")

            window_size_frame = exp_win.size - MARKER_SIZE * 2
            circle_marker = visual.Circle(
                exp_win,
                edges=64,
                units="pixels",
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
                    np.linspace(MARKER_SIZE, 0, MARKER_DURATION_FRAMES // 2),
                    np.linspace(0, MARKER_SIZE, MARKER_DURATION_FRAMES // 2),
                ]
            )

            self.task_start = time.monotonic()
            self.task_stop = np.inf
            self.eyetracker.set_pupil_cb(self._pupil_cb)
            print("WAIT_PUPIL")

            while not len(self._pupils_list):  # wait until we get at least a pupil
                yield False

            print("START_CALIB")
            exp_win.logOnFlip(
                level=logging.EXP,
                msg="eyetracker_calibration: starting at %f" % time.time(),
            )
            for site_id in markers_order:
                marker_pos = self.markers[site_id]
                pos = (marker_pos - 0.5) * window_size_frame
                circle_marker.pos = pos
                print("DISPLAY_MARKER")
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
                        f > CALIBRATION_LEAD_IN
                        and f < len(radius_anim) - CALIBRATION_LEAD_OUT
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
            print("REGISTER_CALIB")
            logging.info(
                f"calibrating on {len(self._pupils_list)} pupils and {len(self.all_refs_per_flip)} markers"
            )
            self.eyetracker.calibrate(self._pupils_list, self.all_refs_per_flip)
            print("REGISTER_CALIB")
            while True:
                notes = getattr(self.eyetracker, '_last_calibration_notification',None)
                time.sleep(5*1e-3)
                if notes:
                    calibration_success = notes['topic'].startswith("notify.calibration.successful")
                    print('REGISTER_CALIB:SUCCESS')
                    if not calibration_success:
                        print('#### CALIBRATION FAILED: restart with <c> ####')
                    break
            print('REGISTER_CALIB:SUCCESS :)')

    def stop(self, exp_win, ctl_win):
        self.eyetracker.unset_pupil_cb()
        yield

    def _save(self):
        if hasattr(self, "_pupils_list"):
            fname = self._generate_unique_filename("calib-data", "npz")
            np.savez(fname, pupils=self._pupils_list, markers=self.all_refs_per_flip)


from subprocess import Popen, PIPE

from contextlib import contextmanager


@contextmanager
def nonblocking(lock):
    locked = lock.acquire(False)
    try:
        yield locked
    finally:
        if locked:
            lock.release()


# Write eyetracker log without breaking tqdm's progress bar while ensuring
# proper logging storage.
# def print_process_stderr(output):
#     logging.exp(msg="eyetracker stderr: " + output)
# def print_process_stdout(output):
#     logging.exp(msg="eyetracker stdout: " + output)

class EyeTrackerClient(threading.Thread):

    EYE = "eye0"

    def __init__(self, output_path, output_fname_base, profile=False, debug=False):
        super(EyeTrackerClient, self).__init__()
        self.stoprequest = threading.Event()
        self.lock = threading.Lock()

        self.pupil = None
        self.gaze = None
        self.unset_pupil_cb()

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

        if os.name != 'nt':
            self._pupil_process = Popen(
                [
                    "python3",
                    os.path.join(os.environ["PUPIL_PATH"], "pupil_src", "main.py"),
                    "capture",
                    "--port",
                    str(PUPIL_REMOTE_PORT),
                ]
                + dev_opts,
                # stdout=PIPE,
                # stderr=PIPE
            )
            # self._pupil_process_err_thread = threading.Thread(target=print_process_stderr, args=(self._pupil_process.stderr))
            # self._pupil_process_err_thread.daemon = True # thread gets killed when the main thread finishes
            # self._pupil_process_err_thread.start()
            # self._pupil_process_out_thread = threading.Thread(target=print_process_stdout, args=(self._pupil_process.stdout))
            # self._pupil_process_out_thread.daemon = True # thread gets killed when the main thread finishes
            # self._pupil_process_out_thread.start()


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
        for plugin in ["NDSI_Manager"]:
            self.send_recv_notification(
                {
                    "subject": "stop_eye_plugin",
                    "target": self.EYE,
                    "name": plugin,
                }
            )

        self.send_recv_notification(
            {
                "subject": "start_eye_plugin",
                "name": "Aravis_Source",
                "target": self.EYE,
                "args": CAPTURE_SETTINGS,
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
        if os.name != 'nt':
            self._pupil_process.wait(timeout)
            self._pupil_process.terminate()
            # self._pupil_process_out_thread.terminate()
            # self._pupil_process_err_thread.terminate()
        time.sleep(1 / 60.0)
        super(EyeTrackerClient, self).join(timeout)

    def run(self):

        self._req_socket.send_string("SUB_PORT")
        ipc_sub_port = int(self._req_socket.recv())
        logging.info(f"ipc_sub_port: {ipc_sub_port}")
        self.pupil_monitor = Msg_Receiver(
            self._ctx, f"tcp://localhost:{ipc_sub_port}",
            topics=("gaze", "pupil", "notify.calibration.successful", "notify.calibration.failed")
        )
        while not self.stoprequest.isSet():
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
                    elif topic.startswith("notify.calibration"):
                        self._last_calibration_notification = tmp
            time.sleep(1e-3)
        logging.info("eyetracker listener: stopping")

    def set_pupil_cb(self, pupil_cb):
        self._pupil_cb = pupil_cb

    def unset_pupil_cb(self):
        self._pupil_cb = None

    def get_pupil(self):
        with nonblocking(self.lock) as locked:
            if locked:
                return self.pupil

    def get_gaze(self):
        with nonblocking(self.lock) as locked:
            if locked:
                return self.gaze

    def calibrate(self, pupil_list, ref_list):
        if len(pupil_list) < 100:
            logging.error("Calibration: not enough pupil captured for calibration")
            # return

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



class GazeDrawer:
    def __init__(self, win):

        self.win = win
        self._gazepoint_stim = visual.Circle(
            self.win,
            radius=30,
            units="pixels",
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
