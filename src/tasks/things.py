import os, sys, time
from psychopy import visual, core, data, logging, event
from .task_base import Task

from ..shared import config

RESPONSE_KEY = "d"
RESPONSE_TIME = 4


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
            os.path.join("data", "things", "images", "fixation_cross.png"),
            size=(0.1, 0.1),
            units="height",
            opacity=0.5,
        )

        # preload all images
        for trial in self.design:
            trial["stim"] = visual.ImageStim(
                exp_win, os.path.join(self.images_path, trial["image_path"])
            )
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

        for trial_n, trial in enumerate(self.trials):
            exp_win.logOnFlip(
                level=logging.EXP,
                msg=f"image: {trial['condition']}:{trial['image_path']}",
            )
            self.progress_bar.set_description(
                f"Trial {trial_n}:: {trial['condition']}:{trial['image_path']}"
            )

            # draw to backbuffer
            trial["stim"].draw(exp_win)
            self.fixation_cross.draw(exp_win)
            if ctl_win:
                trial["stim"].draw(ctl_win)
                self.fixation_cross.draw(ctl_win)
            # wait onset
            while self.task_timer.getTime() < trial["onset"] - 1 / config.FRAME_RATE:
                time.sleep(0.0005)  # just to avoid looping to fast
            yield True  # flip
            trial["onset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )

            # draw to backbuffer
            exp_win.logOnFlip(level=logging.EXP, msg="fixation")
            self.fixation_cross.draw(exp_win)
            if ctl_win:
                self.fixation_cross.draw(ctl_win)
            while (
                self.task_timer.getTime()
                < trial["onset"] + trial["duration"] - 1 / config.FRAME_RATE
            ):
                time.sleep(0.0005)  # just to avoid looping to fast
            yield True  # flip
            trial["offset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )

            while (
                self.task_timer.getTime()
                < trial["onset"] + RESPONSE_TIME - 1 / config.FRAME_RATE
            ):
                time.sleep(0.0005)  # just to avoid looping to fast
            keypress = event.getKeys([RESPONSE_KEY], timeStamped=self.task_timer)
            trial["response"] = len(keypress) > 0
            trial["response_time"] = (
                (keypress[0][1] - trial["onset"]) if len(keypress) else None
            )
            trial["duration_flip"] = trial["offset_flip"] - trial["onset_flip"]
            del trial["stim"]

        while self.task_timer.getTime() < trial["onset"] + RESPONSE_TIME:
            time.sleep(0.0005)

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False


class ThingsMemory(Things):

    DEFAULT_INSTRUCTION = """You will see images on the screen.

Press the buttons to indicate your confidence in having seen or not that image previously.
"""

    EXTRA_INSTRUCTION = """ The response are:
    surely not seen(bold red -),
    not sure not seen (small red -),
    not sure seen (small green +)
    and surely seen (bold green +).


The button mapping will change from trial to trial as indicated at the center of the screen with that image.
    """

    RESPONSE_MAPPING = ['a','b','c','d']

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
            yield
        screen_text.text = self.EXTRA_INSTRUCTION
        if self.run_id == 1:
            for  frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION * 2):
                screen_text.draw(exp_win)
                self._response_mapping.draw(exp_win)
                if ctl_win:
                    screen_text.draw(ctl_win)
                    self._response_mapping.draw(ctl_win)
                yield frameN <2

    def _setup(self, exp_win):
        super()._setup(exp_win)

        self._response_mapping = visual.ImageStim(
            exp_win,
            os.path.join("data", "things", "images", "response_mapping.png"),
            size=(234, 50),
            units="pixels",
        )

    def _run(self, exp_win, ctl_win):
        exp_win.logOnFlip(
            level=logging.EXP, msg="ThingsMemory: task starting at %f" % time.time()
        )
        self.fixation_cross.draw(exp_win)
        if ctl_win:
            self.fixation_cross.draw(ctl_win)
        yield True

        for trial_n, trial in enumerate(self.trials):
            exp_win.logOnFlip(
                level=logging.EXP,
                msg=f"image: {trial['condition']}:{trial['image_path']}",
            )
            self.progress_bar.set_description(
                f"Trial {trial_n}:: {trial['condition']}:{trial['image_path']}"
            )

            # draw to backbuffer
            trial["stim"].draw(exp_win)
            self._response_mapping.flipHoriz = trial["response_mapping_flip"]
            self._response_mapping.pos = (0,0) #force update to flip
            self._response_mapping.draw(exp_win)
            if ctl_win:
                trial["stim"].draw(ctl_win)
                self._response_mapping.draw(ctl_win)
            # wait onset
            while self.task_timer.getTime() < trial["onset"] - 1 / config.FRAME_RATE:
                time.sleep(0.0005)  # just to avoid looping to fast
            yield True  # flip
            trial["onset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )

            # draw to backbuffer
            exp_win.logOnFlip(level=logging.EXP, msg="fixation")
            self.fixation_cross.draw(exp_win)
            if ctl_win:
                self.fixation_cross.draw(ctl_win)
            while (
                self.task_timer.getTime()
                < trial["onset"] + trial["duration"] - 1 / config.FRAME_RATE
            ):
                time.sleep(0.0005)  # just to avoid looping to fast
            yield True  # flip
            trial["offset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )

            while (
                self.task_timer.getTime()
                < trial["onset"] + RESPONSE_TIME - 1 / config.FRAME_RATE
            ):
                time.sleep(0.0005)  # just to avoid looping to fast
            keypresses = event.getKeys(self.RESPONSE_MAPPING, timeStamped=self.task_timer)
            if len(keypresses):
                keypress = keypresses[0] #only take the first keypress, TODO: log extra keypresses?
                key = keypress[0]
                idx = self.RESPONSE_MAPPING.index(key)
                # map to -2 -1 1 2 for not-seen to seen
                idx = idx - 2 + int(idx > 1)
                if trial["response_mapping_flip"]:
                    idx = - idx
                trial["response"] = idx
                trial["response_txt"] = "seen" if idx > 0 else "unseen"
                trial["response_confidence"] = abs(idx) > 1
                trial["response_time"] = (keypress[1] - trial["onset"])
            else:
                print('Warning: no response')
            trial["duration_flip"] = trial["offset_flip"] - trial["onset_flip"]
            del trial["stim"]

        while self.task_timer.getTime() < trial["onset"] + RESPONSE_TIME:
            time.sleep(0.0005)
