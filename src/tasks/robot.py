# from concurrent.futures import thread
import struct
import threading
import time
from typing import Optional
import copy
from PIL import Image
import numpy as np
import pyglet
import cv2
import pickle
import av
from fractions import Fraction
import os
from pylsl import StreamInlet, resolve_byprop, StreamInfo, StreamOutlet
from pylsl import local_clock as lsl_local_clock
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
        self._first_frame = None

    def _setup(self, exp_win):
        """need to overwrite first part of function to get first frame from cozmo"""
        super()._setup(exp_win)
        if self._first_frame is not None:
            self._set_camera_feed_stim(exp_win)

    def _set_camera_feed_stim(self, exp_win):
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

    def _handle_controller_presses(self, exp_win):
        exp_win.winHandle.dispatch_events()
        global _keyPressBuffer, _keyReleaseBuffer

        for k in _keyReleaseBuffer:
            self.pressed_keys.discard(k[0])
            logging.data(f"Keyrelease: {k[0]}", t=k[1])

        for kp in _keyPressBuffer:
            already_released = False
            for kr in _keyReleaseBuffer:
                if kp[0] == kr[0] and kp[1] < kr[1]:
                    already_released = True
                    break
            if not already_released:
                self.pressed_keys.add(kp[0])

        self._new_key_pressed = _keyPressBuffer[:]  # copy

        _keyPressBuffer.clear()
        _keyReleaseBuffer.clear()

        return self.pressed_keys

    def _set_key_handler(self, exp_win):
        exp_win.winHandle.on_key_press = _onPygletKeyPress
        exp_win.winHandle.on_key_release = _onPygletKeyRelease
        self.pressed_keys = set()

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
#                     Cozmo Friends Task (PsychoPy)                 #
# ----------------------------------------------------------------- #
class CozmoFriends(CozmoBaseTask):
    def __init__(
        self,
        name,
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
        super().__init__(name=name, **kwargs)
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
        self.name = name
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

        self.frame_timestamps_pycozmo = []
        self.frame_timestamps_psychopy = []
        self.frame_timestamps_nuc = []
        self.positions_log = []
        self.curr_obs_id = None

        self.robot_pos = None
        self.robot_pos_ts = None
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
        self.run_started = False

        self.wrong_place_txt_duration = 2
        self.next_target_inst_duration = 2

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
        _ = 0
        while self.obs is None or self.robot_pos is None:
            _ += 1
            if not _ % 300:
                if self.obs is None:
                    print("Waiting to receive images.")
                if self.robot_pos is None:
                    print("Waiting to receive position.")
            time.sleep(0.01)

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
        self.run_started = True
        self._set_key_handler(exp_win)
        self._clear_key_buffers()
        self.thread_send.start()
        self.i_target = 0
        already_pressing_find = False
        target_name = self.target_names[self.i_target]
        self._update_target_imgstim(exp_win, target_name)
        position, current_cell_onset, last_current_cell = self.get_position()
        while not self.done:
            time.sleep(0.01)
            actions_list = self.get_actions(exp_win)
            new_obs, obs = self.get_robot_frame()
            position, position_timestamp, cell = self.get_position()
            current_cell = cell if cell is not None else current_cell
            if current_cell != last_current_cell:
                name = None
                for i, target_cells in self.target_positions:
                    if current_cell in target_cells:
                        name = self.target_names[i]
                        break
                self._add_cell_event(
                    position, current_cell, name, current_cell_onset, position_timestamp
                )
                last_current_cell = current_cell
                current_cell_onset = position_timestamp
            if "find" in actions_list and not already_pressing_find:
                if (
                    current_cell in self.target_positions[self.i_target]
                    or "head_up" in actions_list  # TODO: remove this
                ):
                    self._add_find_event(found=True, cell=current_cell)
                    self._add_search_event(
                        target_inst_offset,
                        self._exp_win_last_flip_time - self.task_timer._timeAtLastReset,
                    )
                    self.i_target += 1
                    if self.i_target < len(self.target_names):
                        target_name = self.target_names[self.i_target]
                        self._update_target_imgstim(exp_win, target_name)
                    else:
                        self.all_found = True
                        yield from self._end_instructions(exp_win)
                        self.done = True

                else:  # in wrong place
                    self._add_find_event(found=False, cell=current_cell)
                    if self.wrong_place_txt_time is None:
                        self.wrong_place_txt_time = (
                            self.task_timer.getTime() + self.wrong_place_txt_duration
                        )
            already_pressing_find = "find" in actions_list

            flip, start_target_inst, end_target_inst = self._render_graphics(
                exp_win, new_obs, obs
            )
            if new_obs:
                self.frame_timestamps_psychopy.append(
                    (
                        self.curr_obs_id,
                        self._exp_win_last_flip_time - self.task_timer._timeAtLastReset,
                    )
                )
            if start_target_inst:
                target_inst_onset = (
                    self._exp_win_last_flip_time - self.task_timer._timeAtLastReset
                )
            elif end_target_inst:
                self._add_next_target_instruction_event(
                    target_inst_onset,
                    self._exp_win_last_flip_time - self.task_timer._timeAtLastReset,
                )
                target_inst_offset = (
                    self._exp_win_last_flip_time - self.task_timer._timeAtLastReset
                )
            if flip:
                yield True

            if self.max_duration and self.task_timer.getTime() > self.max_duration:
                print("timeout !")
                yield from self._end_instructions(exp_win)
                self.done = True

    def _stop(self, exp_win, ctl_win):
        self.lock_send.acquire()
        self.actions_to_send = dict.fromkeys(self.actions_to_send, False)
        self.lock_send.release()
        cv2.destroyAllWindows()
        self.done = True
        self.thread_recv_pos.join()
        self.thread_recv_obs.join()
        time.sleep(0.01)  # wait for action to be sent (to stop the robot)
        self.thread_send.join()
        self.container.close()

        # save timestamp arrays and positions
        pycozmo_ts_fname = self._generate_unique_filename("timestamp-pycozmo", "npy")
        np.save(pycozmo_ts_fname, np.asarray(self.frame_timestamps_pycozmo))

        psychopy_ts_fname = self._generate_unique_filename("timestamp-psychopy", "npy")
        np.save(psychopy_ts_fname, np.asarray(self.frame_timestamps_psychopy))

        nuc_ts_fname = self._generate_unique_filename("timestamp-nuc", "npy")
        np.save(nuc_ts_fname, np.asarray(self.frame_timestamps_nuc))

        pos_fname = self._generate_unique_filename("positions", "npy")
        np.save(pos_fname, np.asarray(self.positions_log))

        yield True

    def _reset(self):
        pass

    def _add_cell_event(self, position, cell, name, onset, offset):
        event = {
            "trial_type": "visited_cell",
            "onset": onset,
            "offset": offset,
            "duration": offset - onset,
            "robot_position": position,
            "robot_cell": cell,
            "character_in_cell": name,
        }
        self._events.append(event)

    def _add_find_event(self, found, cell):
        event = {
            "trial_type": "find",
            "onset": self.task_timer.getTime(),
            "sample": time.monotonic(),
            "found": found,
            "robot_position": self.robot_pos,
            "robot_cell": cell,
            "target_name": self.target_names[self.i_target],
            "target_cells": self.target_positions[self.i_target],
            "target_index": self.i_target,
        }
        self._events.append(event)

    def _add_next_target_instruction_event(self, onset, offset):
        event = {
            "trial_type": "next_target_instruction",
            "onset": onset,
            "offset": offset,
            "duration": offset - onset,
            "target_name": self.target_names[self.i_target],
            "target_number": self.i_target,
            "target_cells": self.target_positions[self.i_target],
        }
        self._events.append(event)

    def _add_search_event(self, onset, offset):
        event = {
            "trial_type": "search_sequence",
            "onset": onset,
            "offset": offset,
            "duration": offset - onset,
            "target_name": self.target_names[self.i_target - 1],
            "target_number": self.i_target - 1,
            "target_cells": self.target_positions[self.i_target - 1],
        }
        self._events.append(event)

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

        start_next_target_inst = (
            show_next_target_inst and not self.showing_next_target_inst
        )
        end_next_target_inst = (
            not show_next_target_inst and self.showing_next_target_inst
        )

        flip = (
            new_obs
            or (show_wrong_place_txt and not self.showing_wrong_place_txt)
            or start_next_target_inst
        )
        self.showing_wrong_place_txt = show_wrong_place_txt
        self.showing_next_target_inst = show_next_target_inst
        return flip, start_next_target_inst, end_next_target_inst

    def get_robot_frame(self):
        self.lock_recv_obs.acquire()
        new_obs = self.new_obs
        self.new_obs = False
        obs = self.obs
        self.lock_recv_obs.release()
        return new_obs, obs

    def get_position(self):
        self.lock_recv_pos.acquire()
        position = self.robot_pos
        position_timestamp = self.robot_pos_ts
        self.lock_recv_pos.release()
        if not np.nan in position:
            cell = (
                position[0] // self.cell_width,
                position[1] // self.cell_height,
            )
        else:
            cell = None
        return position, position_timestamp, cell

    def get_actions(self, exp_win):
        self._handle_controller_presses(exp_win)
        actions_to_send = dict.fromkeys(self.actions_to_send, False)  # reset to False
        actions_list = []
        for key in self.pressed_keys:
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
        streams = resolve_byprop("source_id", source_id, timeout=300)
        if not streams:
            raise RuntimeError(f"Stream of id {source_id} not found.")
        inlet = StreamInlet(streams[0], processing_flags=1)
        id = 0
        print("Found image stream.")
        while not self.done:
            data, nuc_ts = inlet.pull_sample()
            obs = literal_eval(data[0])
            self.obs = (
                id,
                Image.frombytes(mode="RGB", size=(320, 240), data=obs).transpose(
                    Image.FLIP_TOP_BOTTOM
                ),
            )
            pycozmo_ts = data[1]
            self.save_mjpeg(id, obs)
            self.lock_recv_obs.acquire()
            self.new_obs = True
            self.lock_recv_obs.release()
            if self.run_started:
                # TODO ask Basile for a smarter way to sync lsl clock with task_timer
                lsl_clock_offset = lsl_local_clock() - self.task_timer.getTime()
                lsl_clock_offset += -self.task_timer.getTime() + lsl_local_clock()
                lsl_clock_offset = lsl_clock_offset / 2
                self.frame_timestamps_pycozmo.append([id, float(pycozmo_ts)])
                self.frame_timestamps_nuc.append([id, nuc_ts - lsl_clock_offset])
                id += 1

    def recv_loop_pos(self, source_id):
        streams = resolve_byprop("source_id", source_id, timeout=300)
        if not streams:
            raise RuntimeError(f"Stream of id {source_id} not found.")
        inlet = StreamInlet(streams[0], processing_flags=1)
        print("Found position stream.")
        while not self.done:
            pos, timestamp = inlet.pull_sample()
            if self.run_started:
                recv_ts = self.task_timer.getTime()
                # TODO ask Basile for a smarter way to sync lsl clock with task_timer
                lsl_clock_offset = lsl_local_clock() - self.task_timer.getTime()
                lsl_clock_offset += -self.task_timer.getTime() + lsl_local_clock()
                lsl_clock_offset = lsl_clock_offset / 2
            pos = np.array(pos, dtype=np.float32)
            self.lock_recv_pos.acquire()
            self.robot_pos = pos
            if self.run_started:
                self.robot_pos_ts = timestamp - lsl_clock_offset
            self.lock_recv_pos.release()
            if self.run_started:
                self.positions_log.append([pos[0], pos[1], self.robot_pos_ts, recv_ts])

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
