import os, sys, time
from psychopy import visual, core, data, logging, event
from .task_base import Task
import numpy as np
from colorama import Fore

from ..shared import config, utils

RESPONSE_KEY = "d"
RESPONSE_TIME = 4
FINAL_WAIT = 9

class Things(Task):

    DEFAULT_INSTRUCTION = """You will see images on the screen.

Press the button when you see an unrecognizable object that was generated."""

    def __init__(self, design, images_path, run, *args, **kwargs):
        super().__init__(**kwargs)
        # TODO: image lists as params, subjects ....
        design = data.importConditions(design)
        self.run_id = run
        self.design = [trial for trial in design if trial["run"] == run]
        if os.path.exists(images_path) and os.path.exists(
            os.path.join(images_path, self.design[0]["image_path"])
        ):
            self.images_path = images_path
        else:
            raise ValueError("Cannot find the listed images in %s " % images_path)

    def _setup(self, exp_win):
        self.fixation_cross = visual.ImageStim(
            exp_win,
            os.path.join("data", "things", "pngs", "fixation_cross.png"),
            size=2,
            units='deg',
        )

        # preload all images
        self._stimuli = []
        for trial in self.design:
            self._stimuli.append(visual.ImageStim(
                exp_win, os.path.join(self.images_path, trial["image_path"]),
                size=10,
                units='deg',
            ))
        self.trials = data.TrialHandler(self.design, 1, method="sequential")
        self.duration = len(self.design)
        self._progress_bar_refresh_rate = 2  # 2 flips per trial
        super()._setup(exp_win)

    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield ()

    def _run(self, exp_win, ctl_win):

        exp_win.logOnFlip(
            level=logging.EXP, msg="Things: task starting at %f" % time.time()
        )
        self.fixation_cross.draw(exp_win)
        if ctl_win:
            self.fixation_cross.draw(ctl_win)
        yield True

        for trial_n, (trial, stimuli) in enumerate(zip(self.trials, self._stimuli)):
            exp_win.logOnFlip(
                level=logging.EXP,
                msg=f"image: {trial['condition']}:{trial['image_path']}",
            )
            self.progress_bar.set_description(
                f"Trial {trial_n}:: {trial['condition']}:{trial['image_path']}"
            )

            # draw to backbuffer
            stimuli.draw(exp_win)
            self.fixation_cross.draw(exp_win)
            if ctl_win:
                stimuli.draw(ctl_win)
                self.fixation_cross.draw(ctl_win)
            # wait onset
            utils.wait_until(self.task_timer, trial["onset"] - 1 / config.FRAME_RATE)
            yield True  # flip
            trial["onset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )

            # draw to backbuffer
            exp_win.logOnFlip(level=logging.EXP, msg="fixation")
            self.fixation_cross.draw(exp_win)
            if ctl_win:
                self.fixation_cross.draw(ctl_win)
            utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] - 1 / config.FRAME_RATE)
            yield True  # flip
            trial["offset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )

            utils.wait_until(self.task_timer, trial["onset"] + RESPONSE_TIME - 1 / config.FRAME_RATE)

            keypress = event.getKeys([RESPONSE_KEY], timeStamped=self.task_timer)
            trial["response"] = len(keypress) > 0
            trial["response_time"] = (
                (keypress[0][1] - trial["onset"]) if len(keypress) else None
            )
            trial["duration_flip"] = trial["offset_flip"] - trial["onset_flip"]

        utils.wait_until(self.task_timer, trial["onset"] + RESPONSE_TIME + FINAL_WAIT)

    def _restart(self):
        self.trials = data.TrialHandler(self.design, 1, method="sequential")

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False

    def unload(self):
        del self._stimuli


class ThingsMemory(Things):

    DEFAULT_INSTRUCTION = """You will see images on the screen.
Try to fixate the central marker at all time.
Press the buttons for each image to indicate your confidence in having seen or not that image previously.
"""

    EXTRA_INSTRUCTION = """ The response are:
-- surely not seen ,
- not sure not seen,
+ not sure seen,
++ and surely seen.




The button mapping will change from trial to trial as indicated at the center of the screen with that image.


    """
    RESPONSE_KEYS = ['up','right','left','down']
    RESPONSE_MAPPING = np.asarray(RESPONSE_KEYS).reshape(2,2)
    RESPONSE_VALUES = np.asarray([[2,1],[-2,-1]])

    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield frameN < 3
        yield True
        screen_text.text = self.EXTRA_INSTRUCTION
        if self.run_id == 1:
            for  frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION * 2):
                screen_text.draw(exp_win)
                self._response_mapping.draw(exp_win)
                if ctl_win:
                    screen_text.draw(ctl_win)
                    self._response_mapping.draw(ctl_win)
                yield frameN
        yield True

    def _setup(self, exp_win):
        super()._setup(exp_win)

        self._response_mapping = visual.ImageStim(
            exp_win,
            os.path.join("data", "things", "pngs", "response_mapping3.png"),
            size=2,
            units='deg',
        )

    def _run(self, exp_win, ctl_win):
        exp_win.logOnFlip(
            level=logging.EXP, msg="ThingsMemory: task starting at %f" % time.time()
        )
        self.fixation_cross.draw(exp_win)
        if ctl_win:
            self.fixation_cross.draw(ctl_win)
        yield True

        for trial_n, (trial, stimuli) in enumerate(zip(self.trials, self._stimuli)):
            exp_win.logOnFlip(
                level=logging.EXP,
                msg=f"image: {trial['condition']}:{trial['image_path']}",
            )
            exp_win.winHandle.activate()

            # draw to backbuffer
            stimuli.draw(exp_win)
            self._response_mapping.flipHoriz = trial["response_mapping_flip_h"]
            self._response_mapping.flipVert = trial["response_mapping_flip_v"]
            self._response_mapping.pos = (0,0) #force update to flip
            self._response_mapping.draw(exp_win)
            if ctl_win:
                stimuli.draw(ctl_win)
                self._response_mapping.draw(ctl_win)
            # wait onset
            utils.wait_until(self.task_timer, trial["onset"] - 1 / config.FRAME_RATE)
            keypresses = event.getKeys(self.RESPONSE_KEYS) # flush response keys
            yield True  # flip
            trial["onset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )
            self.progress_bar.set_description(
                f"Trial {trial_n}:: {trial['condition']}:{trial['image_path']}"
            )

            # draw to backbuffer
            exp_win.logOnFlip(level=logging.EXP, msg="fixation")
            self.fixation_cross.draw(exp_win)
            if ctl_win:
                self.fixation_cross.draw(ctl_win)
            utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] - 1 / config.FRAME_RATE)
            yield True  # flip
            trial["offset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )

            utils.wait_until(self.task_timer, trial["onset"] + RESPONSE_TIME - 1 / config.FRAME_RATE)

            keypresses = event.getKeys(self.RESPONSE_KEYS, timeStamped=self.task_timer)
            if len(keypresses):
                trial['keypresses'] = keypresses # log all keypresses with timing
                idxs = [np.where(self.RESPONSE_MAPPING == k[0]) for k in keypresses]
                response_mapping_flipped = self.RESPONSE_VALUES.copy()
                if trial["response_mapping_flip_h"]:
                    response_mapping_flipped = np.rot90(np.fliplr(response_mapping_flipped))
                if trial["response_mapping_flip_v"]:
                    response_mapping_flipped = np.rot90(np.fliplr(response_mapping_flipped),3)
                responses = [response_mapping_flipped[idx[0][0],idx[1][0]] for idx in idxs]

                main_key = keypresses[0] # take the first response as main one, to be decided
                main_response = responses[0]
                trial["response"] = main_response
                trial["response_txt"] = "seen" if main_response > 0 else "unseen"
                trial["error"] = trial["response_txt"] != trial["condition"]
                trial["response_confidence"] = abs(main_response) > 1
                trial["response_time"] = (main_key[1] - trial["onset"])
                if trial['error']:
                    self.progress_bar.set_description(
                        f"Trial {trial_n}:: {trial['condition']}:{trial['image_path']} \u274c")
                else:
                    self.progress_bar.set_description(
                        f"Trial {trial_n}:: {trial['condition']}:{trial['image_path']} \u2705")
            else:
                # we need to force empty values for the first trials
                # otherwise following values are not recorded!?
                for k in ['keypresses', 'response', 'response_txt', 'error', 'response_confidence', 'response_time']:
                    trial[k] = ''
                self.progress_bar.set_description(
                    f"{Fore.RED}Trial {trial_n}:: {trial['condition']}:{trial['image_path']}: no response{Fore.RESET}")

            trial["duration_flip"] = trial["offset_flip"] - trial["onset_flip"]

        utils.wait_until(self.task_timer, trial["onset"] + RESPONSE_TIME + FINAL_WAIT)
