# from concurrent.futures import thread
import struct
import threading
import time
from typing import Optional
import copy
from PIL import Image
import numpy as np
import pyglet
import socket
import cv2
import pickle
import av
from fractions import Fraction
import os
from pylsl import StreamInlet, resolve_stream, StreamInfo, StreamOutlet
from psychopy import visual, core, logging, event
from ast import literal_eval
from .task_base import Task
from ..shared import config


# keyset of the MRI controller :
# ["x", "a", "b", "y", "u", "d", "l", "r", "p", "s", "space"]

# Must launch antimicrox to map controller buttons to
# the appropriate keypresses.

DEFAULT_KEY_ACTION_DICT = {
    "u": "forward",
    "d": "backward",
    "l": "left",
    "r": "right",
    "x": "head_up",
    "b": "head_down",
}
ACTION_ACTU_DICT = {
    "forward": "drive",
    "backward": "drive",
    "left": "drive",
    "right": "drive",
    "head_up": "head",
    "head_down": "head",
}
COZMO_FPS = 15.0
ADDR_FAMILY = socket.AF_INET
SOCKET_TYPE = socket.SOCK_STREAM
BUFF_SIZE = 65536

_keyPressBuffer = []
_keyReleaseBuffer = []


def _onPygletKeyPress(symbol, modifier):
    if modifier:
        event._onPygletKey(symbol, modifier)
    global _keyPressBuffer
    keyTime = core.getTime()
    key = pyglet.window.key.symbol_string(symbol).lower().lstrip("_").lstrip("NUM_")
    _keyPressBuffer.append((key, keyTime))


def _onPygletKeyRelease(symbol, modifier):
    global _keyReleaseBuffer
    keyTime = core.getTime()
    key = pyglet.window.key.symbol_string(symbol).lower().lstrip("_").lstrip("NUM_")
    _keyReleaseBuffer.append((key, keyTime))


# ----------------------------------------------------------------- #
#                       Cozmo Abstract Task                         #
# ----------------------------------------------------------------- #
class CozmoBaseTask(Task):
    """Base task class, implementing the basic run loop and some facilities."""

    DEFAULT_INSTRUCTION = """You will perform a task with Cozmo."""

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """CozmoTask class constructor."""
        super().__init__(**kwargs)
        self.obs = None
        self.done = False
        self.info = None
        self.game_vis_stim = None

    def _setup(self, exp_win):
        """need to overwrite first part of function to get first frame from cozmo"""

        super()._setup(exp_win)

        if self._first_frame is not None:
            min_ratio = min(
                exp_win.size[0] / self._first_frame.size[0],
                exp_win.size[1] / self._first_frame.size[1],
            )
            width = int(min_ratio * self._first_frame.size[0])
            height = int(min_ratio * self._first_frame.size[1])

            self.game_vis_stim = visual.ImageStim(
                exp_win,
                size=(width, height),
                units="pix",
                interpolate=True,
                flipVert=True,
                autoLog=False,
            )

    def _handle_controller_presses(self, exp_win):  # k[0] : key, k[1] : time stamp
        exp_win.winHandle.dispatch_events()
        global _keyPressBuffer, _keyReleaseBuffer

        for k in _keyReleaseBuffer:
            if k[0] == "5" or k[0] == "percent" or k[0] == "lshift":
                continue
            if k[0] not in self.pressed_keys:
                continue  # weird case
            event = {
                "trial_type": "keypress",
                "onset": self.pressed_keys[k[0]]
                - self.task_timer._timeAtLastReset
                + core.monotonicClock._timeAtLastReset,
                "offset": k[1]
                - self.task_timer._timeAtLastReset
                + core.monotonicClock._timeAtLastReset,
                "duration": k[1] - self.pressed_keys[k[0]],
                "key": k[0],
                "sample": time.monotonic(),
            }
            self._events.append(event)

            if k[0] in self.pressed_keys:
                # check in case twice same key in keyreleasebuffer (happened once)
                del self.pressed_keys[k[0]]

            logging.data(f"Keyrelease: {k[0]}", t=k[1])
        _keyReleaseBuffer.clear()

        for k in _keyPressBuffer:
            self.pressed_keys[k[0]] = k[1]  # key : onset

        self._new_key_pressed = _keyPressBuffer[:]  # copy
        _keyPressBuffer.clear()

    def _set_key_handler(self, exp_win):
        exp_win.winHandle.on_key_press = _onPygletKeyPress
        exp_win.winHandle.on_key_release = _onPygletKeyRelease
        self.pressed_keys = dict()

    def _unset_key_handler(self, exp_win):
        # deactivate custom keys handling
        exp_win.winHandle.on_key_press = event._onPygletKey

    def _clear_key_buffers(self):
        global _keyPressBuffer, _keyReleaseBuffer
        self.pressed_keys.clear()
        _keyReleaseBuffer.clear()
        _keyPressBuffer.clear()

    def get_actions(self, *args, **kwargs):
        """Must update the actions instance dictionary of the task class.

        Raises:
            NotImplementedError: error raised if method not overwritten in child class.
        """
        raise NotImplementedError("Must override get_actions")


# ----------------------------------------------------------------- #
#                   Cozmo First Task (PsychoPy)                     #
# ----------------------------------------------------------------- #
class CozmoFirstTaskPsychoPy(CozmoBaseTask):
    DEFAULT_INSTRUCTION = "Let's explore the maze !"

    def __init__(
        self,
        max_duration=5 * 60,
        controller=None,
        key_actions=DEFAULT_KEY_ACTION_DICT,
        img_path: Optional[str] = None,
        sound_path: Optional[str] = None,
        capture_path: Optional[str] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.controller = controller
        self.actions = {
            "display": False,
            "sound": False,
            "picture": False,
            "head": [],
            "lift": [],
            "drive": [],
            "acc_rate": 0.0,
        }
        self.previous_actions = {
            "display": False,
            "sound": False,
            "picture": False,
            "head": [],
            "lift": [],
            "drive": [],
            "acc_rate": 0.0,
        }
        self.key_actions = key_actions
        self.img_path = img_path
        self.sound_path = sound_path
        self.capture_path = capture_path

        self.max_duration = max_duration
        self.frame_timer = core.Clock()
        self.cnter = 0

    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="red",
            wrapWidth=1.2,
        )

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield ()

    def _setup(self, exp_win):
        self.controller.reset()
        if self.controller._test is False:
            while self.controller.last_frame is None:  # wait for frame to be captured
                pass
            self._first_frame = self.controller.last_frame

        super()._setup(exp_win)

    def _set_key_handler(self, exp_win):
        exp_win.winHandle.on_key_press = _onPygletKeyPress
        exp_win.winHandle.on_key_release = _onPygletKeyRelease
        self.pressed_keys = dict()

    def _unset_key_handler(self, exp_win):
        # deactivate custom keys handling
        exp_win.winHandle.on_key_press = event._onPygletKey

    def _handle_controller_presses(
        self, exp_win
    ):  # k[0] : actual key, k[1] : time stamp
        exp_win.winHandle.dispatch_events()
        global _keyPressBuffer, _keyReleaseBuffer

        for k in _keyReleaseBuffer:
            self._log_event(
                {
                    "trial_type": "button_press",
                    "onset": self.pressed_keys[k[0]],
                    "offset": k[1],
                    "duration": k[1] - self.pressed_keys[k[0]],
                    "key": k[0],
                }
            )
            del self.pressed_keys[k[0]]
            logging.data(f"Keyrelease: {k[0]}", t=k[1])

        _keyReleaseBuffer.clear()

        for k in _keyPressBuffer:
            self.pressed_keys[k[0]] = k[1]  # key : onset
        self._new_key_pressed = _keyPressBuffer[:]  # copy

        _keyPressBuffer.clear()

        return self.pressed_keys

    def _run(self, exp_win, *args, **kwargs):
        self._set_key_handler(exp_win)
        self._reset()
        self._clear_key_buffers()
        while self.task_timer.getTime() < self.max_duration:
            time.sleep(0.01)
            actions_list = self.get_actions(exp_win)
            if self.actions != self.previous_actions:
                self.previous_actions = copy.deepcopy(self.actions)
                self._step()

            flip = self.loop_fun(*args, **kwargs)
            if flip:
                yield True  # True if new frame, False otherwise

        print("timeout !")
        self._stop_cozmo()

    def _stop(self, exp_win, ctl_win):
        exp_win.setColor((0, 0, 0), "rgb")
        for _ in range(2):
            yield True

    def _save(self):
        pass
        return False

    def _update_actuator_value(self, actu, value):
        """Update a value in the dictionnary containing the motors commands."""
        if type(self.actions[actu]) is bool:
            self.actions[actu] = True
        elif type(self.actions[actu]) is list:
            self.actions[actu].append(value)

    def _progressive_mov(self):
        """Compute a progressive acceleration rate, for smoother movement."""
        self.cnter += 1
        if not self.actions["drive"]:
            self.cnter = 0.0
        self.actions["acc_rate"] = self.cnter * 0.05

    def _update_actuator_actions(self, actions_list):
        """Update the dictionnary to control the motors."""
        for action in actions_list:
            if action in ACTION_ACTU_DICT:
                actu = ACTION_ACTU_DICT[action]
                self._update_actuator_value(actu, action)
        self._progressive_mov()

    def _clear_key_buffers(self):
        global _keyPressBuffer, _keyReleaseBuffer
        self.pressed_keys.clear()
        _keyReleaseBuffer.clear()
        _keyPressBuffer.clear()

    def _reset(self):
        """Initializes/Resets display, sound and image capture handles."""
        self.controller.reset(
            img_path=self.img_path,
            sound_path=self.sound_path,
            capture_path=self.capture_path,
        )
        self.frame_timer.reset()

    def _step(self):
        """Sends actions dictionary to the Controller."""
        self.controller.step(self.previous_actions)

    def reset_dict(self):
        """Resets the action dictionary with default values."""
        self.actions["display"] = False
        self.actions["sound"] = False
        self.actions["picture"] = False
        self.actions["head"] = []
        self.actions["lift"] = []
        self.actions["drive"] = []
        self.actions["acc_rate"] = 0.0

    def _stop_cozmo(self):
        self.controller.stop()

    def _render_graphics(self, exp_win):
        # self.obs = ImageOps.grayscale(self.obs)
        self.obs = self.obs.transpose(Image.FLIP_TOP_BOTTOM)
        self.game_vis_stim.image = self.obs
        self.game_vis_stim.draw(exp_win)

    def loop_fun(self, exp_win):
        t = self.frame_timer.getTime()
        if t >= 1 / COZMO_FPS:
            self.frame_timer.reset()
            self.info = self.controller.infos
            self.obs = self.controller.last_frame
            if self.controller._test is False:
                self._render_graphics(exp_win)
                return True
        return False

    def get_actions(self, exp_win):
        keys = self._handle_controller_presses(exp_win)
        self.reset_dict()
        actions_list = []
        for key in keys:
            if key in self.key_actions:
                actions_list.append(self.key_actions[key])
        self._update_actuator_actions(actions_list)
        return actions_list


# ----------------------------------------------------------------- #
#                     Cozmo NUC Task (PsychoPy)                     #
# ----------------------------------------------------------------- #
class CozmoFirstTaskPsychoPyNUC(CozmoBaseTask):
    DEFAULT_INSTRUCTION = "Let's explore the maze !"

    def __init__(
        self,
        nuc_addr,
        tcp_port_send,
        tcp_port_recv,
        tcp_port_recv_tracking,
        max_duration=5 * 60,
        key_actions=DEFAULT_KEY_ACTION_DICT,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.max_duration = max_duration
        self.actions_to_send = {
            "forward": False,
            "backward": False,
            "left": False,
            "right": False,
            "head_up": False,
            "head_down": False,
        }
        self.new_obs = False
        self.send_timer = core.Clock()
        self.cnter = 0
        self.tracking_frame = None
        self.key_actions = key_actions

        self.nuc_addr = nuc_addr
        self.tcp_port_send = tcp_port_send
        self.tcp_port_recv = tcp_port_recv
        self.tcp_port_recv_tracking = tcp_port_recv_tracking

        self.sock_send = socket.socket(ADDR_FAMILY, SOCKET_TYPE)
        self.sock_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_send.bind(("", self.tcp_port_send))
        self.sock_send.listen(10)
        self.sock_send.settimeout(1.5)  # in seconds, to avoid being stuck

        self.thread_send = threading.Thread(target=self.send_loop)
        self.lock_send = threading.Lock()

        self.frame_timestamp_pos_pycozmo = []
        self.frame_timestamp_psychopy = []
        self.curr_obs_id = None

    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="red",
            wrapWidth=1.2,
        )
        # create img stims
        for _ in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield ()

    def _setup(self, exp_win):
        cozmo_feed_fname = self._generate_unique_filename("cozmo-feed", "mp4")
        self.container = av.open(cozmo_feed_fname, "w")
        self.stream = self.container.add_stream(codec_name="mjpeg", rate=15)
        self.stream.pix_fmt = "yuvj422p"

        self.thread_recv = threading.Thread(target=self.recv_loop)
        self.thread_recv.start()
        self.lock_recv = threading.Lock()

        self.thread_recv_tracking = threading.Thread(target=self.recv_loop_tracking)
        self.thread_recv_tracking.start()
        self.lock_recv_tracking = threading.Lock()

        while self.obs is None:  # wait until a first frame is received
            pass
        self._first_frame = self.obs[1]
        super()._setup(exp_win)

    def _run(self, exp_win, *args, **kwargs):
        self._set_key_handler(exp_win)
        self._reset()
        self._clear_key_buffers()
        self.thread_send.start()
        while not self.done:
            time.sleep(0.01)
            actions_list = self.get_actions(exp_win)
            flip = self.loop_fun(*args, **kwargs)
            if flip:
                yield True  # True if new frame, False otherwise
                self.frame_timestamp_psychopy.append(
                    (self.curr_obs_id, self._exp_win_last_flip_time)
                )
            if self.max_duration and self.task_timer.getTime() > self.max_duration:
                print("timeout !")
                self.done = True

    def _stop(self, exp_win, ctl_win):
        cv2.destroyAllWindows()
        self.done = True
        self.thread_recv.join()
        self.container.close()

        # save timestamp arrays
        self.frame_timestamp_pycozmo = np.asarray(self.frame_timestamp_pycozmo)
        pycozmo_ts_fname = self._generate_unique_filename("timestamp-pycozmo", "npy")
        np.save(pycozmo_ts_fname, self.frame_timestamp_pycozmo)
        self.frame_timestamp_psychopy = np.asarray(self.frame_timestamp_psychopy)
        psychopy_ts_fname = self._generate_unique_filename("timestamp-psychopy", "npy")
        np.save(psychopy_ts_fname, self.frame_timestamp_psychopy)

        self.thread_send.join()
        self.sock_send.close()
        # need to close it otherwise error 98 address already in use
        yield True

    def _reset(self):
        pass

    def _render_graphics(self, exp_win, obs, tracking_frame=None):
        self.curr_obs_id = obs[0]
        self.game_vis_stim.image = obs[1]
        self.game_vis_stim.draw(exp_win)

    def loop_fun(self, exp_win):
        self.lock_recv.acquire()
        new_obs = self.new_obs
        self.new_obs = False
        obs = self.obs
        self.lock_recv.release()

        if new_obs:
            self._render_graphics(exp_win, obs, tracking_frame)
            return True

        return False

    # RECEIVING SECTION
    def recv_connect(self, tcp_port):
        self.sock_recv = socket.socket(ADDR_FAMILY, SOCKET_TYPE)
        self.sock_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        while not self.done:
            try:
                self.sock_recv.connect((self.nuc_addr, tcp_port))
                break
            except ConnectionError:
                continue
            except OSError as error:
                print(error)

    def save_mjpeg(self, id, buffer):
        packet = av.packet.Packet(buffer)
        packet.stream = self.stream
        packet.time_base = Fraction(1, int(COZMO_FPS))
        packet.pts = id
        self.container.mux(packet)

    def img_decode(self, img_raw, is_color_image):
        obs_tmp = cv2.imdecode(img_raw, cv2.IMREAD_COLOR)
        if obs_tmp is not None:
            obs_tmp = cv2.cvtColor(
                obs_tmp, cv2.COLOR_BGR2RGB
            )  # OpenCV stores images in B G R ordering
            obs_tmp = Image.fromarray(obs_tmp)
            if is_color_image:
                obs_tmp = obs_tmp.resize((320, 240))
        return obs_tmp

    def recv_loop(self):
        self.recv_connect(self.tcp_port_recv)
        id = 0
        img_raw = np.array(0)
        while not self.done:
            time.sleep(1 / COZMO_FPS / 8)

            received = bytearray()
            try:
                sz = int.from_bytes(self.sock_recv.recv(3), byteorder="big")
                # TODO change if not long enough
                if sz > 0:
                    while len(received) < sz:
                        received += self.sock_recv.recv(sz - len(received))
                else:
                    pass  # TODO
            except ConnectionError as error:
                print(error)
                self.done = True

            if len(received) > 0 and not self.done:
                # self.save_mjpeg(id, received[3:])
                offset = 0
                onset = 3
                timestamp = int.from_bytes(
                    received[offset : offset + onset], byteorder="big"
                )
                # timestamp sent as 3 first bytes after 3 first bytes (size of message)
                offset += onset
                self.frame_timestamp_pycozmo.append((id, timestamp))

                cozmo_img = received[offset:]
                self.save_mjpeg(id, cozmo_img)
                img_raw = np.asarray(cozmo_img, dtype="uint8")
                is_color_image = img_raw[0] != 0
                if img_raw.size != 0:
                    obs_tmp = self.img_decode(img_raw, is_color_image)
                    self.lock_recv.acquire()
                    self.obs = (id, obs_tmp.transpose(Image.FLIP_TOP_BOTTOM))
                    self.new_obs = True
                    self.lock_recv.release()
                id += 1

        self.sock_recv.close()
        # TODO: use context managers and/or generators to deal with closing

    def recv_loop_tracking(self):
        self.recv_connect(self.tcp_port_recv_tracking)
        id = 0
        while not self.done:
            time.sleep(1 / COZMO_FPS / 8)

            received = bytearray()
            try:
                sz = int.from_bytes(self.sock_recv.recv(3), byteorder="big")
                # TODO change if not long enough
                if sz > 0:
                    while len(received) < sz:
                        received += self.sock_recv.recv(sz - len(received))
                else:
                    pass  # TODO
            except ConnectionError as error:
                print(error)
                self.done = True

            if len(received) > 0 and not self.done:
                offset = 0
                onset = 3
                timestamp = int.from_bytes(
                    received[offset : offset + onset], byteorder="big"
                )
                # timestamp sent as 3 first bytes after 3 first bytes (size of message)
                offset += onset
                onset = 3
                onset_track = onset
                sz = int.from_bytes(received[offset : offset + onset], byteorder="big")
                onset_track += onset
                offset += onset
                onset = 8
                x_pos = struct.unpack("d", received[offset : offset + onset])
                # x_pos encoded as C double (8 bytes)
                y_pos = struct.unpack(
                    "d", received[offset + onset : offset + (2 * onset)]
                )  # y_pos encoded as C double (8 bytes)
                self.lock_recv_tracking.acquire()
                self.robot_pos = (x_pos, y_pos)
                self.lock_recv_tracking.release()
                # TODO : log position with timestamp and id.
                id += 1

        self.sock_recv.close()

    # SENDING SECTION
    def send_connect(self):
        while not self.done:
            try:
                conn, _ = self.sock_send.accept()
                break
            except socket.timeout:
                continue
        if self.done:
            return None
        return conn

    def send_loop(self):
        conn = self.send_connect()
        actions_prev = dict()
        self.send_timer.reset()

        while not self.done and conn:
            time.sleep(1 / COZMO_FPS / 4)
            self.lock_send.acquire()
            actions = copy.deepcopy(self.actions_to_send)
            self.lock_send.release()

            if actions is not None and (
                actions != actions_prev or self.send_timer.getTime() > 0.5
            ):
                actions_prev = copy.deepcopy(actions)
                self.send_timer.reset()
                data = pickle.dumps(actions, protocol=4)
                try:
                    conn.sendall(data)
                except ConnectionError as error:
                    print(error)
                    self.done = True

        # avoid unwanted movement
        if conn and not self.done:
            data = pickle.dumps(dict.fromkeys(actions, False), protocol=4)
            conn.sendall(data)
            conn.close()

    def get_actions(self, exp_win):
        self._handle_controller_presses(exp_win)
        actions_to_send = dict.fromkeys(self.actions_to_send, False)  # reset to False
        actions_list = []
        for key in self.pressed_keys.keys():
            if key in self.key_actions:
                if self.key_actions[key] in actions_to_send:
                    actions_to_send[self.key_actions[key]] = True
                actions_list.append(self.key_actions[key])

        self.lock_send.acquire()
        self.actions_to_send = copy.deepcopy(actions_to_send)
        self.lock_send.release()
        return actions_list


# ----------------------------------------------------------------- #
#                     Cozmo Friends Task (PsychoPy)                 #
# ----------------------------------------------------------------- #
class CozmoFriends(CozmoBaseTask):
    def __init__(
        self,
        source_id_imgs,
        source_id_pos,
        source_id_actions,
        target_names,
        target_positions,
        target_imgs_dir,
        cell_width,
        cell_height,
        max_duration=15 * 60,
        key_actions={**DEFAULT_KEY_ACTION_DICT, "a": "find"},
        *args,
        **kwargs,
    ):
        self.max_duration = max_duration
        self.actions_to_send = {
            "forward": False,
            "backward": False,
            "left": False,
            "right": False,
            "head_up": False,
            "head_down": False,
            "lift_up": False,
            "lift_down": False,
            "picture": False,
            "display": False,
            "sound": False,
        }
        self.name = "cozmofriends"
        self.done = False
        self.obs = None
        self.new_obs = False
        self.send_timer = core.Clock()
        self.cnter = 0
        self.key_actions = key_actions

        self.thread_send = threading.Thread(
            target=self.send_loop, args=(source_id_actions,)
        )
        self.lock_send = threading.Lock()
        self.thread_recv_obs = threading.Thread(
            target=self.recv_loop_obs, args=(source_id_imgs,)
        )
        self.lock_recv_obs = threading.Lock()
        self.thread_recv_pos = threading.Thread(
            target=self.recv_loop_pos, args=(source_id_pos,)
        )
        self.lock_recv_pos = threading.Lock()

        self.frame_timestamp_pycozmo = []
        self.frame_timestamp_psychopy = []
        self.curr_obs_id = None

        self.robot_pos = None
        self.target_names = target_names
        self.target_positions = target_positions
        self.target_imgs_dir = target_imgs_dir
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.next_target_inst_time = None
        self.wrong_place_txt_time = None
        self.next_target_imgstim = None
        self.showing_next_target_inst = False
        self.showing_wrong_place_txt = False
        self.all_found = False

        self.wrong_place_txt_duration = 5
        self.next_target_inst_duration = 5

    def _instructions(self, exp_win, ctl_win):
        instruction = visual.ImageStim(
            exp_win,
            image=os.path.join(self.target_imgs_dir, "begin_task.png"),
            size=(2, 2),
            units="norm",
        )
        for _ in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            instruction.draw(exp_win)
            if ctl_win:
                instruction.draw(ctl_win)
            yield ()

    def _end_instructions(self, exp_win):
        instruction = visual.ImageStim(
            exp_win,
            image=os.path.join(self.target_imgs_dir, "end_task.png"),
            size=(2, 2),
            units="norm",
        )
        for _ in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            instruction.draw(exp_win)
            yield True

    def _setup(self, exp_win):
        cozmo_feed_fname = self._generate_unique_filename("cozmo-feed", "mp4")
        self.container = av.open(cozmo_feed_fname, "w")
        self.stream = self.container.add_stream(codec_name="mjpeg", rate=15)
        self.stream.pix_fmt = "yuvj422p"

        self.thread_recv_obs.start()
        self.thread_recv_pos.start()

        # wait until a first frame and first position are received
        print("Waiting to receive first frame and position.")
        while self.obs is None or self.robot_pos is None:
            time.sleep(0.01)
            pass
        self._first_frame = self.obs[1]

        self.wrong_place_txtstim = visual.TextStim(
            exp_win,
            text="Wrong place, keep searching.",
            color="red",
            pos=(0, -0.7),
        )
        self.target_img_pos = (0.7, 0.7)
        self.target_img_size = (0.3, 0.5)
        super()._setup(exp_win)

    def _run(self, exp_win, *args, **kwargs):
        self._set_key_handler(exp_win)
        self._clear_key_buffers()
        self.thread_send.start()
        self.i_target = 0
        target_name = self.target_names[self.i_target]
        self._update_target_imgstim(exp_win, target_name)
        while not self.done:
            time.sleep(0.01)
            actions_list = self.get_actions(exp_win)
            new_obs, obs = self.get_robot_frame()
            if "find" in actions_list:
                current_cell = (
                    self.robot_pos[0] // self.cell_width,
                    self.robot_pos[1] // self.cell_height,
                )
                if current_cell in self.target_positions[self.i_target] or True:
                    self.i_target += 1
                    if self.i_target < len(self.target_names):
                        target_name = self.target_names[self.i_target]
                        self._update_target_imgstim(exp_win, target_name)
                    else:
                        self.all_found = True
                        yield from self._end_instructions(exp_win)
                        self.done = True

                else:  # in wrong place
                    if self.wrong_place_txt_time is None:
                        self.wrong_place_txt_time = (
                            self.task_timer.getTime() + self.wrong_place_txt_duration
                        )

            flip = self._render_graphics(exp_win, new_obs, obs)
            if flip:
                yield True  # True if new frame, False otherwise
                self.frame_timestamp_psychopy.append(
                    (self.curr_obs_id, self._exp_win_last_flip_time)
                )

            if self.max_duration and self.task_timer.getTime() > self.max_duration:
                print("timeout !")
                yield from self._end_instructions(exp_win)
                self.done = True

    def _stop(self, exp_win, ctl_win):
        cv2.destroyAllWindows()
        self.done = True
        self.thread_recv_pos.join()
        self.thread_recv_obs.join()
        self.container.close()

        # save timestamp arrays
        self.frame_timestamp_pycozmo = np.asarray(self.frame_timestamp_pycozmo)
        pycozmo_ts_fname = self._generate_unique_filename("timestamp-pycozmo", "npy")
        np.save(pycozmo_ts_fname, self.frame_timestamp_pycozmo)

        self.frame_timestamp_psychopy = np.asarray(self.frame_timestamp_psychopy)
        psychopy_ts_fname = self._generate_unique_filename("timestamp-psychopy", "npy")
        np.save(psychopy_ts_fname, self.frame_timestamp_psychopy)

        self.thread_send.join()
        yield True

    def _reset(self):
        pass

    def _update_target_imgstim(self, exp_win, target_name):
        next_target_img_path = os.path.join(
            self.target_imgs_dir, f"find_{target_name}.png"
        )
        self.next_target_imgstim = visual.ImageStim(
            exp_win,
            image=next_target_img_path,
            size=(2, 2),
            units="norm",
        )
        if self.next_target_inst_time is None:
            self.next_target_inst_time = (
                self.task_timer.getTime() + self.next_target_inst_duration
            )
        target_img_path = os.path.join(self.target_imgs_dir, f"{target_name}.png")
        self.target_imgstim = visual.ImageStim(
            exp_win,
            image=target_img_path,
            size=self.target_img_size,
            pos=self.target_img_pos,
        )

    def _render_graphics(self, exp_win, new_obs, obs):
        now = self.task_timer.getTime()
        show_next_target_inst = False
        if self.next_target_inst_time is not None:
            if now < self.next_target_inst_time:
                show_next_target_inst = True
            else:
                self.next_target_inst_time = None
        show_wrong_place_txt = False
        if self.wrong_place_txt_time is not None:
            if now < self.wrong_place_txt_time:
                show_wrong_place_txt = True
            else:
                self.wrong_place_txt_time = None

        if new_obs or show_next_target_inst or show_wrong_place_txt:
            n_target_stim = visual.TextStim(
                exp_win,
                text=f"{self.i_target}/{len(self.target_names)}",
                color="blue",
                pos=(0.7, -0.8),
            )
            self.curr_obs_id = obs[0]
            self.game_vis_stim.image = obs[1]
            self.game_vis_stim.draw(exp_win)
            self.target_imgstim.draw(exp_win)
            n_target_stim.draw(exp_win)
            if show_wrong_place_txt:
                self.wrong_place_txtstim.draw(exp_win)
            if show_next_target_inst:
                self.next_target_imgstim.draw(exp_win)

        flip = (
            new_obs
            or (show_wrong_place_txt and not self.showing_wrong_place_txt)
            or (show_next_target_inst and not self.showing_next_target_inst)
        )
        self.showing_wrong_place_txt = show_wrong_place_txt
        self.showing_next_target_inst = show_next_target_inst
        return flip

    def get_robot_frame(self):
        self.lock_recv_obs.acquire()
        new_obs = self.new_obs
        self.new_obs = False
        obs = self.obs
        self.lock_recv_obs.release()
        return new_obs, obs

    def get_actions(self, exp_win):
        self._handle_controller_presses(exp_win)
        actions_to_send = dict.fromkeys(self.actions_to_send, False)  # reset to False
        actions_list = []
        for key in self.pressed_keys.keys():
            if key in self.key_actions:
                if self.key_actions[key] in actions_to_send:
                    actions_to_send[self.key_actions[key]] = True
                actions_list.append(self.key_actions[key])

        self.lock_send.acquire()
        self.actions_to_send = copy.deepcopy(actions_to_send)
        self.lock_send.release()
        return actions_list

    def save_mjpeg(self, id, buffer):
        packet = av.packet.Packet(buffer)
        packet.stream = self.stream
        packet.time_base = Fraction(1, int(COZMO_FPS))
        packet.pts = id
        self.container.mux(packet)

    def img_decode(self, img_raw, is_color_image):
        obs_tmp = cv2.imdecode(img_raw, cv2.IMREAD_COLOR)
        if obs_tmp is not None:
            obs_tmp = cv2.cvtColor(
                obs_tmp, cv2.COLOR_BGR2RGB
            )  # OpenCV stores images in B G R ordering
            obs_tmp = Image.fromarray(obs_tmp)
            if is_color_image:
                obs_tmp = obs_tmp.resize((320, 240))
        return obs_tmp

    def recv_loop_obs(self, source_id):
        streams = resolve_stream("source_id", source_id)
        if not streams:
            raise RuntimeError(f"Stream of id {source_id} not found.")
        inlet = StreamInlet(streams[0])
        id = 0
        while not self.done:
            data, nuc_ts = inlet.pull_sample()
            obs = literal_eval(data[0])
            pycozmo_ts = data[1]
            img_raw = np.frombuffer(obs, dtype=np.uint8)
            self.save_mjpeg(id, obs)
            is_color_image = img_raw[0] != 0
            obs_tmp = self.img_decode(img_raw, is_color_image)
            self.lock_recv_obs.acquire()
            self.obs = (id, obs_tmp.transpose(Image.FLIP_TOP_BOTTOM))
            self.new_obs = True
            self.lock_recv_obs.release()
            id += 1

    def recv_loop_pos(self, source_id):
        streams = resolve_stream("source_id", source_id)
        if not streams:
            raise RuntimeError(f"Stream of id {source_id} not found.")
        inlet = StreamInlet(streams[0])
        id = 0
        while not self.done:
            pos, timestamp = inlet.pull_sample()
            # TODO : log position
            pos = np.array(pos, dtype=np.float32)
            self.lock_recv_pos.acquire()
            self.robot_pos = pos
            self.lock_recv_pos.release()
            id += 1

    def send_loop(self, source_id):
        info = StreamInfo(
            name="cozmofriends",
            type="cozmo_actions",
            channel_count=11,
            channel_format="int8",
            source_id=source_id,
        )
        outlet = StreamOutlet(info)
        previous_actions = np.zeros(11, dtype=np.uint8)
        while not self.done:
            self.lock_send.acquire()
            actions_to_send = copy.deepcopy(self.actions_to_send)
            self.lock_send.release()
            data = np.array(list(actions_to_send.values()), dtype=np.uint8)
            if not (data == previous_actions).all():
                outlet.push_sample(data)
                previous_actions = data
            time.sleep(0.01)
