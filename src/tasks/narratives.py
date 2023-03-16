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
    Please listen to the following story carefully.
    You will be asked a few questions once it is over..
"""


class FreeRecall(Task):
    """docstring for FreeRecall."""

    DEFAULT_INSTRUCTION = """
    Please provide an account of what you heard.
    Remember you have as much time as you need.
    Please provide as many details as you can.
    Please try to keep your head as still as possible while you talk.
    Please start talking when instructed on the screen.
    Press A when done.
"""

    def __init__(self, mic_device, initial_wait=4, final_wait=9, max_duration=600, *args, **kwargs):
        super().__init__(**kwargs)
        self.initial_wait, self.final_wait, self.max_duration = initial_wait, final_wait, max_duration
        self.mic_device = mic_device


    def _setup(self, exp_win,):
        import psychopy.sound
        self._mic = psychopy.sound.Microphone(
            device = mic_device
        )
        self.screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )


    def _run(self, exp_win, ctl_win):
        self._mic.start()

        for _ in utils.wait_until_yield(
            self.task_timer,
            self.initial_wait,
            keyboard_accuracy=.1):
            self._mic.poll()
            yield False

        self.screen_text.draw(exp_win)
        if ctl_win:
            self.screen_text.draw(ctl_win)

        for _ in utils.wait_until_yield(
            self.task_timer,
            self.max_duration - self.final_wait,
            keyboard_accuracy=.1):
            self._mic.poll()
            yield False

        yield True
        for _ in utils.wait_until_yield(
            self.task_timer,
            self.task_timer.getTime() + self.final_wait,
            keyboard_accuracy=.1):
            self._mic.poll()
            yield False
        self._mic.stop()
        self._audioClip = mic.getRecording()

    def _save(self):
        output_wav_file = self._generate_unique_filename("audio", "wav")
        self._audioClip.save(output_wav_file)
