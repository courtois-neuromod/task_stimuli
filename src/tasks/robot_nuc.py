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

ADDR_FAMILY = socket.AF_INET
SOCKET_TYPE = socket.SOCK_STREAM


class CozmoFirstTaskPsychoPyNUC(CozmoBaseTaskNUC):

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
        """ self.sock_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_recv.connect((self.nuc_addr, self.tcp_port_recv))
        self._get_obs(exp_win)
        self.sock_recv.close() """
        while self.obs is None: # wait until a first frame is received
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

        self.done = True
        self.thread_send.join()
        self.thread_recv.join()
        self.sock_send.close()  # need to close it otherwise error 98 address already in use

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


