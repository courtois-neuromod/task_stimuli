import os
import time
import argparse
import datetime
import threading
import zmq, msgpack
import logging

from subprocess import Popen
from contextlib import contextmanager
#from src.shared.eyetracking import EyeTrackerClient
from src.shared.zmq_tools import *


BASE_OUTPUT_DIR = '/home/basile/tests'
# Pupil settings
PUPIL_REMOTE_PORT = 50123
CAPTURE_SETTINGS = {
    "frame_size": [640, 480],
    "frame_rate": 50,
    "exposure_time": 4000,
    "global_gain": 1,
    "auto_noise_suppression": True,
    "gev_packet_size": 1500,
    "PixelMappingFormat":"HighBits",
    #"uid": "Aravis-Fake-GV01",  # for test purposes
    "uid": "MRC Systems GmbH-GVRD-MRC HighSpeed-MR_CAM_HS_0019",
}


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
        for plugin in ["NDSI_Manager"]:#, "Pye3DPlugin"]:
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
        self.resume()

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
                topics=(
                    "gaze", "pupil", "fixations",
                    "notify.calibration.successful",
                    "notify.calibration.failed",
                    "notify.aravis")

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
        Assign gaze to markers based on their timestamp
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


    def gaze_qc_per_marker(self, markers_dict, frames_per_marker, conf_thresh = 0.80):
        '''
        estimated eye-to-screen distance in pixels
        based on screen dim in pixels ((1280, 1024)) and screen deg of visual angle (17.5, 14)
        '''
        dist_in_pix = 4164 # in pixels

        val_qc = []
        #print('Distance between gaze and target in degrees of visual angle')
        #print('Good < 0.5 deg ; Fair = [0.5, 1.5[ deg ; Poor >= 1.5 deg')

        for count in range(len(markers_dict.keys())):
            m = markers_dict[count]
            #print(f"Marker {count}, Normalized position: {m['norm_pos']}")

            num_gz = len(m['gaze_data']['timestamps'])
            expected_gz_count = 250*(frames_per_marker/60)

            if num_gz:
                # transform marker's normalized position into dim = (3,) vector in pixel space
                m_vecpos = np.concatenate(((np.array(m['norm_pos']) - 0.5)*(1280, 1024), np.array([dist_in_pix])), axis=0)

                g_conf = np.array(m['gaze_data']['confidence'])
                # filtrate gaze based on confidence threshold
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
                markers_dict[count]['gaze_data']['distances'] = {'distances': distances,
                                                                 'timestamps': g_times,
                                                                 }

                num_dist = len(distances)
                good = np.sum(distances < 0.5) / num_dist
                fair = np.sum((distances >= 0.5)*(distances < 1.5)) / num_dist
                poor = np.sum(distances >= 1.5) / num_dist

                #print('Total gaze:' + str(num_gz) + ' , Good:' + str(good) + ' , Fair:' + str(fair) + ' , Poor:' + str(poor))
                val_qc.append({
                    'marker': count,
                    'norm_pos': m['norm_pos'],
                    'num_gz': num_gz,
                    'gz_count_ratio': num_gz/expected_gz_count,
                    'above_70conf_ratio': np.sum(g_conf > 0.7)/num_gz,
                    'above_80conf_ratio': np.sum(g_conf > 0.8)/num_gz,
                    'above_90conf_ratio': np.sum(g_conf > 0.9)/num_gz,
                    'median_distance': np.median(distances),
                    'good': good,
                    'fair': fair,
                    'poor': poor,
                })
            else:
                val_qc.append({
                    'marker': count,
                    'norm_pos': m['norm_pos'],
                    'num_gz': 0,
                })

        def abc_mapping(val_num, cutoff_vals):
            if val_num > cutoff_vals[0]:
                return 'A'
            elif val_num > cutoff_vals[1]:
                return 'B'
            else:
                return 'C'

        print('EYE-TRACKING VALIDATION METRICS (per marker)')
        print(f"RATIO OF DETECTED PUPILS: {[round(x['gz_count_ratio'], 3) for x in val_qc if 'gz_count_ratio' in x]}")
        print(f"CONFIDENCE >0.7 RATIO: {[round(x['above_70conf_ratio'], 3) for x in val_qc if 'above_70conf_ratio' in x]}")
        print(f"CONFIDENCE >0.8 RATIO: {[round(x['above_80conf_ratio'], 3) for x in val_qc if 'above_80conf_ratio' in x]}")
        print(f"CONFIDENCE >0.9 RATIO: {[round(x['above_90conf_ratio'], 3) for x in val_qc if 'above_90conf_ratio' in x]}")
        print(f"MEDIAN DISTANCE 2 TARGET (deg of visual angle): {[round(x['median_distance'], 3) for x in val_qc if 'median_distance' in x]}")
        print('****************QUICK SUMMARY*********************')
        print(f"PUPIL DETECTION: {[abc_mapping(x['gz_count_ratio'], [0.97, 0.95]) for x in val_qc if 'gz_count_ratio' in x]}")
        print(f">70% CONF: {[abc_mapping(x['above_70conf_ratio'], [0.90, 0.80]) for x in val_qc if 'above_70conf_ratio' in x]}")
        print(f">80% CONF: {[abc_mapping(x['above_80conf_ratio'], [0.85, 0.75]) for x in val_qc if 'above_80conf_ratio' in x]}")
        print(f"DISTANCE: {[abc_mapping(x['median_distance']*(-1), [-1.2, -2.2]) for x in val_qc if 'median_distance' in x]}")

        return markers_dict, val_qc


    def interleave_calibration(self, tasks):
        calibration_index=0
        for task in tasks:
            if task.use_eyetracking and task.et_calibrate:
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
            if task.use_eyetracking and self.validate_calib:
                yield EyetrackerCalibration_targets(
                    self,
                    name=f"eyeTrackercalib-validate-{calibration_index}",
                    validation=True
                    )

    def calibrate(self, pupil_list, ref_list):
        if len(pupil_list) < 100:
            logging.error("Calibration: not enough pupil captured for calibration")
            # return

        # TODO: check num of quality pupils per fixation points, set quality threshold...

        calib_data = {"ref_list": ref_list, "pupil_list": pupil_list}

        logging.info("sending calibration data to pupil")
        logging.flush()
        calib_res = self.send_recv_notification(
            {
                "subject": "start_plugin",
                "name": "Gazer2D",
                "args": {"calib_data": calib_data},
                "raise_calibration_error": True,
            }
        )
        logging.info("calibration data sent to pupil")
        logging.flush()

    def validate(self, gaze_list, ref_list, frames_per_marker):

        markers_dict = self.get_marker_dictionary(ref_list)
        markers_dict = self.assign_gaze_to_markers(gaze_list, markers_dict)
        markers_dict, val_qc = self.gaze_qc_per_marker(markers_dict,
                                                       frames_per_marker,
                                                       conf_thresh = 0.80,
                                                       )

        return val_qc



def start_eyetracker(args):

    output_path = f"{BASE_OUTPUT_DIR}/{parsed.study}/sub-{parsed.subject}{'/ses-'+parsed.session if parsed.session else ''}"
    os.makedirs(output_path, exist_ok=True)
    basename = f"pupil_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    eyetracker_client = EyeTrackerClient(
        output_path=output_path,
        output_fname_base=basename,
        profile=False,
        debug=True,
    )

    eyetracker_client.send_recv_notification(
        {
            "subject": "start_plugin",
            "name": "ScreenMarkerChoreographyPlugin",
            "args": {
                "fullscreen": True,
                "marker_scale": 1.0,
                "sample_duration": 360,
                "monitor_name": "DP-2 [1]",
                "fixed_screen": True,
                "selected_gazer_class_name": "Gazer2D",
            },
        }
    )

    eyetracker_client.send_recv_notification(
        {
            "subject": "start_plugin",
            "name": "Annotation_Capture",
            "args": {
                "annotation_definitions": [['Trigger','T'], ['Trigger5','5'], ['Trigger%','%']]
            },
        }
    )


    #print("starting et client")
    #eyetracker_client.start()

    #eyetracker_client.join(5)


def parse_args():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=("Run all tasks in a session"),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--study", "-p", required=True, help="Study name")
    parser.add_argument("--subject", "-s", required=True, help="Subject ID")
    parser.add_argument("--session", "-ss", help="Session")
    return parser.parse_args()

if __name__ == "__main__":
    parsed = parse_args()
    start_eyetracker(parsed)
