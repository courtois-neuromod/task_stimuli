import os, sys, time
from psychopy import visual, core, data, logging, event, sound
from pandas import read_csv
from .task_base import Task
from colorama import Fore

from ..shared import config, utils
from ..shared.eyetracking import fixation_dot

INSTRUCTION_DURATION = 4

class SoundTaskBase(Task):

    def __init__(self, sound_file, initial_wait=4, final_wait=9, *args, **kwargs):
        super().__init__(**kwargs)
        self.initial_wait, self.final_wait = initial_wait, final_wait
        if os.path.exists(sound_file):
            self.sound_file = sound_file
        else:
            raise ValueError("File %s does not exists" % sound_file)

    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )

        screen_text.draw(exp_win)
        if ctl_win:
            screen_text.draw(ctl_win)
        yield True
        time.sleep(INSTRUCTION_DURATION)
        yield True

    def _setup(self, exp_win):
        self.sound = sound.Sound(self.sound_file)
        self.fixation = fixation_dot(exp_win)

    def _run(self, exp_win, ctl_win):
        yield True
        for _ in utils.wait_until_yield(
            self.task_timer,
            self.initial_wait,
            keyboard_accuracy=.1):
            for stim in self.fixation:
                stim.draw(exp_win)
            yield False

        self.sound.play()
        for _ in utils.wait_until_yield(
            self.task_timer,
            self.initial_wait + self.sound.duration + self.final_wait,
            keyboard_accuracy=.1):
            yield False
        while self.sound.status > 0:
            pass
        self.sound.stop()


class Story(SoundTaskBase):
    """docstring for Story."""

    DEFAULT_INSTRUCTION = """
    Listen to the story.
"""
