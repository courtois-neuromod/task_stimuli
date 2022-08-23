import os
import time
import pandas as pd
import numpy as np
# import psychtoolbox as ptb
from psychopy import prefs
from psychopy.sound.backend_ptb import SoundPTB as sound
from psychopy.sound._base import apodize
# from playsound import playsound

from .task_base import Task
from ..shared import utils

#prefs.hardware['audioLib'] = ['PTB']

# Time value when the experiment starts
# t_initial = time.perf_counter()


class PureTones(Task):

    def __init__(self, sub, design, ISI=0, **kwargs):
        super().__init__(**kwargs)
        self.ISI = ISI
        self.sub = sub
        self.session_filename = design
        np.random.RandomState(seed=1)

        self.sub_number = ""
        for i in range(0, len(self.sub)):
            if self.sub[i].isdigit():
                self.sub_number += str(self.sub[i])
            else:
                continue

        self.stimuli_path = os.path.join("data", "audio", "stimuli")

        self.stimuli_df = pd.read_csv(self.session_filename, sep="\t")


    def _run(self, exp_win, ctl_win):
        """
        This function fetches a wave file and plays it.
        It also provides some feedback to the user regarding
        the number of the stimuli presentation (from 1 to 48)
        """

        for i, stimuli in self.stimuli_df.iterrows():

            # reimplement
            lr_idx = 0 if stimuli.ear == 'L' else 1
            sampleRate = 22050
            nSamples = int(stimuli.duration * sampleRate)
            snd = np.zeros((nSamples,2))
            snd[:,lr_idx] = np.sin(np.arange(0.0, 1.0, 1.0 / nSamples) * 2 * np.pi * stimuli.frequency * stimuli.duration)
            snd[:,lr_idx] = apodize(snd[:,lr_idx], sampleRate)

            # to_play = os.path.join(self.stimuli_path, sound_file)
            to_play = sound(value=snd,
                            stereo=True,
                            secs=stimuli.duration,
                            sampleRate=sampleRate,
                            volume=np.power(10,stimuli.volume/20))

            print(f"Presentation number {i+1}: {stimuli.ear} {stimuli.frequency} {stimuli.volume} {np.power(10,stimuli.volume/20)}")

            utils.wait_until(self.task_timer, stimuli.onset)
            # playsound(to_play)
            to_play.play()
            utils.wait_until(self.task_timer, stimuli.onset+stimuli.duration)
            yield True


# Calculation of the duration of the experiment
# t_final = time.perf_counter() - t_initial

# print(f"Sequence completed. The elapsed time is {t_final/60} minutes")
