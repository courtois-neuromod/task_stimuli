import threading
import time
from typing import Optional
import copy

import numpy as np
import pyglet

from psychopy import visual, core, logging, event
from .task_base import Task
from ..shared import config

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
                units="pixels",
                interpolate=True,
                flipVert=True,
                autoLog=False,
            )

    def get_actions(self, *args, **kwargs):
        """Must update the actions instance dictionary of the task class.

        Raises:
            NotImplementedError: error raised if method not overwritten in child class.
        """
        raise NotImplementedError("Must override get_actions")


# ----------------------------------------------------------------- #
#                   Cozmo First Task (PsychoPy)                     #
# ----------------------------------------------------------------- #

# KEY_SET = ["x", "a", "b", "y", "u", "d", "l", "r", "p", "s", "space",]
KEY_SET = [
    "x",
    "_",
    "b",
    "_",
    "u",
    "d",
    "l",
    "r",
    "_",
    "_",
    "_",
]

KEY_ACTION_DICT = {
    KEY_SET[4]: "forward",
    KEY_SET[5]: "backward",
    KEY_SET[6]: "left",
    KEY_SET[7]: "right",
    KEY_SET[0]: "head_up",
    KEY_SET[2]: "head_down",
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


from PIL import Image
from cozmo_api.controller import Controller


class CozmoFirstTaskPsychoPy(CozmoBaseTask):

    DEFAULT_INSTRUCTION = "Let's explore the maze !"

    def __init__(
        self,
        max_duration=5 * 60,
        controller: Controller = None,
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
        self.actions_old = {
            "display": False,
            "sound": False,
            "picture": False,
            "head": [],
            "lift": [],
            "drive": [],
            "acc_rate": 0.0,
        }
        self.img_path = img_path
        self.sound_path = sound_path
        self.capture_path = capture_path

        self.max_duration = max_duration
        self.actions_list = []
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
        self.pressed_keys = set()

    def _unset_key_handler(self, exp_win):
        # deactivate custom keys handling
        exp_win.winHandle.on_key_press = event._onPygletKey

    def _handle_controller_presses(
        self, exp_win
    ):  # k[0] : actual key, k[1] : time stamp
        exp_win.winHandle.dispatch_events()
        global _keyPressBuffer, _keyReleaseBuffer

        for k in _keyReleaseBuffer:
            self.pressed_keys.discard(k[0])
            logging.data(f"Keyrelease: {k[0]}", t=k[1])
        _keyReleaseBuffer.clear()
        for k in _keyPressBuffer:
            self.pressed_keys.add(k[0])
        self._new_key_pressed = _keyPressBuffer[:]  # copy
        _keyPressBuffer.clear()
        return self.pressed_keys

    def actions_is_new(self):
        """Checks if the updated actions instance dictionary is different from the previous actions dictionary sent for controlling Cozmo.

        Returns:
            bool: True if the updated actions instance dictionary is different from the previous actions dictionary sent for controlling Cozmo. False otherwise.
        """

        return self.actions != self.actions_old

    def _run(self, exp_win, *args, **kwargs):
        self._set_key_handler(exp_win)
        _done = False
        self._reset()
        self._clear_key_buffers()
        while not _done:
            time.sleep(0.01)
            # breakpoint()
            _done = self.get_actions(exp_win)
            if _done:
                break
            elif self.actions_is_new():
                self.actions_old = copy.deepcopy(self.actions)
                self._step()

            flip = self.loop_fun(*args, **kwargs)
            if flip:
                yield True  # True if new frame, False otherwise

            if (
                self.max_duration and self.task_timer.getTime() > self.max_duration
            ):  # stop if we are above the planned duration
                print("timeout !")
                break

        self._stop_cozmo()

    def _stop(self, exp_win, ctl_win):
        exp_win.setColor((0, 0, 0), "rgb")
        for _ in range(2):
            yield True

    def _save(self):
        pass
        return False

    def _update_value(self, actu, value):
        if type(self.actions[actu]) is bool:
            self.actions[actu] = True
        elif type(self.actions[actu]) is list:
            self.actions[actu].append(value)

    def _progressive_mov(self):
        self.cnter += 1
        if not self.actions["drive"]:
            self.cnter = 0.0
        self.actions["acc_rate"] = self.cnter * 0.05

    def _update_dict(self):
        for action in self.actions_list:
            actu = ACTION_ACTU_DICT[action]
            self._update_value(actu, action)
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
        self.controller.step(self.actions_old)

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
        self.actions_list.clear()
        key_action_dict_keys = list(KEY_ACTION_DICT.keys())
        for key in keys:
            if key in key_action_dict_keys:
                self.actions_list.append(KEY_ACTION_DICT[key])
        self._update_dict()
        return False


# ----------------------------------------------------------------- #
#                     Cozmo NUC Task (PsychoPy)                     #
# ----------------------------------------------------------------- #

# KEY_SET = ["x", "a", "b", "y", "u", "d", "l", "r", "p", "s", "space",]
KEY_SET = [
    "x",
    "_",
    "b",
    "_",
    "u",
    "d",
    "l",
    "r",
    "_",
    "_",
    "_",
]

KEY_ACTION_DICT = {
    KEY_SET[4]: "forward",
    KEY_SET[5]: "backward",
    KEY_SET[6]: "left",
    KEY_SET[7]: "right",
    KEY_SET[0]: "head_up",
    KEY_SET[2]: "head_down",
}

COZMO_FPS = 15.0

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


from PIL import Image
import socket
import cv2
import pickle

ADDR_FAMILY = socket.AF_INET
SOCKET_TYPE = socket.SOCK_STREAM


class CozmoFirstTaskPsychoPyNUC(CozmoBaseTask):

    DEFAULT_INSTRUCTION = "Let's explore the maze !"

    def __init__(
        self,
        nuc_addr,
        tcp_port_send,
        tcp_port_recv,
        max_duration=5 * 60,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.max_duration = max_duration
        self.actions_list = []
        self.frame_timer = core.Clock()
        self.cnter = 0

        self.nuc_addr = nuc_addr
        self.tcp_port_send = tcp_port_send
        self.tcp_port_recv = tcp_port_recv

        self.sock_send = socket.socket(ADDR_FAMILY, SOCKET_TYPE)
        self.sock_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_send.bind(("", self.tcp_port_send))
        self.sock_send.listen(10)
        self.sock_send.settimeout(1.5)  # in seconds, to avoid being stuck

        self.thread_send = threading.Thread(target=self.send_loop)
        self.thread_send.start()

        self.thread_recv = threading.Thread(target=self.recv_loop)
        self.thread_recv.start()

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
        while self.obs is None:  # wait until a first frame is received
            pass
        self._first_frame = self.obs

        super()._setup(exp_win)

    def _set_key_handler(self, exp_win):
        exp_win.winHandle.on_key_press = _onPygletKeyPress
        exp_win.winHandle.on_key_release = _onPygletKeyRelease
        self.pressed_keys = set()

    def _unset_key_handler(self, exp_win):
        # deactivate custom keys handling
        exp_win.winHandle.on_key_press = event._onPygletKey

    def _handle_controller_presses(
        self, exp_win
    ):  # k[0] : actual key, k[1] : time stamp
        exp_win.winHandle.dispatch_events()
        global _keyPressBuffer, _keyReleaseBuffer

        for k in _keyReleaseBuffer:
            self.pressed_keys.discard(k[0])
            logging.data(f"Keyrelease: {k[0]}", t=k[1])
        _keyReleaseBuffer.clear()
        for k in _keyPressBuffer:
            self.pressed_keys.add(k[0])
        self._new_key_pressed = _keyPressBuffer[:]  # copy
        _keyPressBuffer.clear()
        return self.pressed_keys

    def _run(self, exp_win, *args, **kwargs):

        self._set_key_handler(exp_win)
        self._reset()
        self._clear_key_buffers()

        while not self.done:
            time.sleep(0.01)
            self.get_actions(exp_win)

            flip = self.loop_fun(*args, **kwargs)
            if flip:
                yield True  # True if new frame, False otherwise

            if (
                self.max_duration and self.task_timer.getTime() > self.max_duration
            ):  # stop if we are above the planned duration
                print("timeout !")
                self.done = True

    def _stop(self, exp_win, ctl_win):
        self.done = True
        self.thread_send.join()
        self.thread_recv.join()
        self.sock_send.close()  # need to close it otherwise error 98 address already in use

        yield True

    def _save(self):
        pass
        return False

    def _clear_key_buffers(self):
        global _keyPressBuffer, _keyReleaseBuffer
        self.pressed_keys.clear()
        _keyReleaseBuffer.clear()
        _keyPressBuffer.clear()

    def _reset(self):
        self.frame_timer.reset()

    def _render_graphics(self, exp_win):
        self.game_vis_stim.image = self.obs
        self.game_vis_stim.draw(exp_win)

    def loop_fun(self, exp_win):
        t = self.frame_timer.getTime()
        if t >= 1 / COZMO_FPS:
            self.frame_timer.reset()
            self._render_graphics(exp_win)

            return True

        return False

    # RECEIVING SECTION

    def recv_loop(self):

        while not self.done:
            self.sock_recv = socket.socket(ADDR_FAMILY, SOCKET_TYPE)

            while True:
                try:
                    self.sock_recv.connect((self.nuc_addr, self.tcp_port_recv))
                    break
                except ConnectionRefusedError:
                    pass
            # receive data
            received = bytearray()
            while True:
                recvd_data = self.sock_recv.recv(230400)
                if not recvd_data:
                    break
                else:
                    recvd_data = bytearray(recvd_data)
                    received += recvd_data

            nparr = np.asarray(received, dtype="uint8")
            if nparr.size != 0:
                obs_tmp = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                obs_tmp = Image.fromarray(obs_tmp)

                self.obs = obs_tmp.transpose(Image.FLIP_TOP_BOTTOM)

            self.sock_recv.close()

    # SENDING SECTION

    def send_loop(self):
        while not self.done:
            conn, _ = self.sock_send.accept()
            if self.actions_list is not None:
                data = pickle.dumps(self.actions_list)
                conn.sendall(data)
            conn.close()

        # avoid unwanted movement
        conn, _ = self.sock_send.accept()
        data = pickle.dumps([])
        conn.sendall(data)
        conn.close()

    def get_actions(self, exp_win):
        keys = self._handle_controller_presses(exp_win)
        actions = []
        key_action_dict_keys = list(KEY_ACTION_DICT.keys())
        for key in keys:
            if key in key_action_dict_keys:
                actions.append(KEY_ACTION_DICT[key])
        self.actions_list = actions
