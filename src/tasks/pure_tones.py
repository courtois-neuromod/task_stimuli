import os
import time
import pandas as pd
import numpy as np
# import psychtoolbox as ptb
from psychopy import prefs
from psychopy.sound.backend_ptb import SoundPTB as sound
# from playsound import playsound

from .task_base import Task
# from ..shared import utils

prefs.hardware['audioLib'] = ['PTB']

# Time value when the experiment starts
# t_initial = time.perf_counter()


class PureTones(Task):

    def __init__(self, sub, design, ISI=0):
        super(Task, self).__init__()
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
        self.stimuli_ls = self.stimuli_df["trial_type"]

    def _run(self, run_number):
        """
        This function fetches a wave file and plays it.
        It also provides some feedback to the user regarding
        the number of the stimuli presentation (from 1 to 48)
        """

        for i, sound_file in enumerate(self.stimuli_ls):

            # to_play = os.path.join(self.stimuli_path, sound_file)
            to_play = sound(value=os.path.join(self.stimuli_path, sound_file),
                            stereo=True,
                            sampleRate=44100,
                            volume=0.5)

            print(f"Presentation number {i+1}: {sound_file}")

            # playsound(to_play)
            to_play.play()

            print(f"Waiting for {self.ISI} second(s)")

            # !!! Needs to be replaced by the utils wait function
            time.sleep(self.ISI)
            # utils.wait_until("self.task_timer", "ISI")


# Calculation of the duration of the experiment
# t_final = time.perf_counter() - t_initial

# print(f"Sequence completed. The elapsed time is {t_final/60} minutes")
