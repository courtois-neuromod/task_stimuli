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


import pyaudio
import wave

class AudioRecording(Task):
    """docstring for AudioRecording."""

    def __init__(
        self,
        initial_wait=4, final_wait=9,
        max_duration=600, done_key='a',
        audio_rate=48000, audio_channels=1,
        *args, **kwargs):
        super().__init__(**kwargs)
        self.initial_wait, self.final_wait, self.max_duration = initial_wait, final_wait, max_duration
        self.audio_rate, self. audio_channels= audio_rate, audio_channels
        self.done_key = done_key


    def _setup(self, exp_win,):

        """
        import psychopy.sound
        self._mic = psychopy.sound.Microphone(
            device = self.mic_device,
            channels = 1,
            maxRecordingSize = 24000 * (self.max_duration/60) # 24000~=62s
        )"""

        self._pyaudio_if = pyaudio.PyAudio()

        self.screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )
        self.fixation = fixation_dot(exp_win)


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

    def _start_recording(self):
        self._audio_stream = self._pyaudio_if.open(
            format=pyaudio.paInt16,
            channels=self.audio_channels,
            rate=self.audio_rate,
            frames_per_buffer=1024,
            input=True)
        self._audio_buffers = []

    def _stop_recording(self):

        # Stop and close the stream
        self._audio_stream.stop_stream()
        self._audio_stream.close()

    def _poll_audio(self):
        self._audio_buffers.append(self._audio_stream.read(1024))

    def unload(self):
        self._pyaudio_if.terminate()

    def _run(self, exp_win, ctl_win):
        self._start_recording()
        for _ in utils.wait_until_yield(
            self.task_timer,
            self.initial_wait,
            keyboard_accuracy=.05):
            self._poll_audio()
            yield True

        for _ in utils.wait_until_yield(
            self.task_timer,
            self.max_duration - self.final_wait,
            keyboard_accuracy=.05):
            self._poll_audio()
            if len(event.getKeys(self.done_key)):
                break
            for stim in self.fixation:
                stim.draw(exp_win)
            yield True

        for _ in utils.wait_until_yield(
            self.task_timer,
            self.task_timer.getTime() + self.final_wait,
            keyboard_accuracy=.05):
            self._poll_audio()
            yield True

    def _stop(self, exp_win, ctl_win):
        #self._mic.stop()
        self._stop_recording()
        yield True


    def _save(self):
        output_wav_file = self._generate_unique_filename("audio", "wav")
        wf = wave.open(output_wav_file, 'wb')
        wf.setnchannels(self.audio_channels)
        wf.setsampwidth(self._pyaudio_if.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.audio_rate)
        wf.writeframes(b''.join(self._audio_buffers))
        wf.close()


class FreeRecall(AudioRecording):

    DEFAULT_INSTRUCTION = """
Please provide an account of what you heard.
Remember you have as much time as you need.
Please provide as many details as you can.
Please try to keep your head as still as possible while you talk.
Please start talking when the fixation dot appears.
Press A when done.
    """



class RecencyJudgments(Task):
    """docstring for RecencyJudgments."""


    DEFAULT_INSTRUCTION = """
Please choose which of the two fragments came first.
If you are unsure, choose the best possible answer.
Use up/down buttons to answer.
"""

    def __init__(
        self,
        design_file,
        initial_wait=4, final_wait=9, max_response_time=15
        *args, **kwargs):
        super().__init__(**kwargs)
        self.initial_wait, self.final_wait, self.max_response_time = initial_wait, final_wait, max_response_time
        if not os.path.exists(design_file):
            raise ValueError(f"{design_file} does not exists")
        self.design_file = design_file
        self.design = data.importConditions(design)

    def _setup(self, exp_win):


        self.text1 = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
            pos=(0, -.5),
        )

        self.text2 = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
            pos=(0, .5),
        )

        self.fixation = fixation_dot(exp_win)


    def _run(self, exp_win, ctl_win):

        
