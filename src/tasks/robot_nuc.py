import threading
import time
from typing import Optional
import copy
import numpy as np

from psychopy import visual, core, logging, event
from .task_base import Task

from ..shared import config

# ----------------------------------------------------------------- #
#                       Cozmo Abstract Task                         #
# ----------------------------------------------------------------- #


class CozmoBaseTaskNUC(Task):
    """Base task class, implementing the basic run loop and some facilities."""

    DEFAULT_INSTRUCTION = """You will perform a task with Cozmo."""

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """CozmoTask class constructor.

        Args:
            #controller (cozmo_api.controller.Controller): Controller object for interacting with Cozmo.
            img_path (Optional[str], optional): path of the image to display on Cozmo's screen. Defaults to None.
            sound_path (Optional[str], optional): path of the sound to play in Cozmo's speaker. Defaults to None.
            capture_path (Optional[str], optional): path for picture saving. Defaults to None.
        """
        super().__init__(**kwargs)
        self.obs = None
        self.done = False
        self.info = None
        self.game_vis_stim = None

    def _setup(self, exp_win):
        """need to overwrite first part of function to get first frame from cozmo"""

        super()._setup(exp_win)

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
import pyglet

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

NUC_ADDRESS = "10.30.6.17"
TCP_PORT_RECV = 1024
TCP_PORT_SEND = 1025
ADDR_FAMILY = socket.AF_INET
SOCKET_TYPE = socket.SOCK_STREAM


class CozmoFirstTaskPsychoPyNUC(CozmoBaseTaskNUC):

    DEFAULT_INSTRUCTION = "Let's explore the maze !"

    def __init__(self, max_duration=5 * 60, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_duration = max_duration
        self.actions_list = []
        self.frame_timer = core.Clock()
        self.cnter = 0

        self.sock_send = socket.socket(ADDR_FAMILY, SOCKET_TYPE)
        self.sock_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_send.bind(("", TCP_PORT_SEND))
        self.sock_send.listen(10)
        self.thread_send = None

        self.sock_recv = None
        self.thread_recv = None


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
        self.sock_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_recv.connect((NUC_ADDRESS, TCP_PORT_RECV))
        self._get_obs(exp_win)
        self.sock_recv.close()
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

        while True:
            time.sleep(0.01)
            self.get_actions(exp_win)

            flip = self.loop_fun(*args, **kwargs)
            if flip:
                yield True  # True if new frame, False otherwise

            if (
                self.max_duration and self.task_timer.getTime() > self.max_duration
            ):  # stop if we are above the planned duration
                print("timeout !")
                break

        self.sock_send.close()
    
    def _stop(self, exp_win, ctl_win):
        exp_win.setColor((0, 0, 0), "rgb")
        for _ in range(2):
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

    def _get_obs(self, exp_win):
        # socket init
        self.sock_recv = socket.socket(ADDR_FAMILY, SOCKET_TYPE)
        self.sock_recv.connect((NUC_ADDRESS, TCP_PORT_RECV))
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
            self.obs = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            self.obs = Image.fromarray(
                self.obs
            )  # maybe a way to send/recv PIL images directly (TODO: try pickle.dumps(my PIL Image))
            self.obs = self.obs.transpose(Image.FLIP_TOP_BOTTOM)
        
        self.sock_recv.close()

    def loop_fun(self, exp_win):
        t = self.frame_timer.getTime()
        if t >= 1 / COZMO_FPS:
            self.frame_timer.reset()
            
            if self.thread_recv is None or not self.thread_recv.is_alive():
                self.thread_recv = threading.Thread(target=self._get_obs, args=(exp_win,))
                self.thread_recv.start()
            
            self._render_graphics(exp_win)

            return True

        return False

    def send_key_data(self):
        conn, _ = self.sock_send.accept()
        data = pickle.dumps(self.actions_list)
        conn.sendall(data)
        #time.sleep(0.05)
        conn.close()

    def _send_actions_list(self):
        #if self.thread_send is not None:
        #    self.thread_send.join()
        if self.thread_send is None or not self.thread_send.is_alive():
            self.thread_send = threading.Thread(target=self.send_key_data)
            self.thread_send.start()

    def get_actions(self, exp_win):
        keys = self._handle_controller_presses(exp_win)
        self.actions_list.clear()
        key_action_dict_keys = list(KEY_ACTION_DICT.keys())
        for key in keys:
            if key in key_action_dict_keys:
                self.actions_list.append(KEY_ACTION_DICT[key])

        self._send_actions_list()