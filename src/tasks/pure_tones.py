import os
import argparse
import time
import pandas as pd
import numpy as np
from playsound import playsound
from psychopy.sound.backend_sounddevice import SoundDeviceSound as sds

from .task_base import Task
# from ..shared import utils

# Time value when the experiment starts
# t_initial = time.perf_counter()


class PureTones(Task):

    def __init__(self, sub, ISI=0, design):
        super(Task, self).__init__()
        self.ISI = ISI
        self.sub = sub
        self.session_filename = design
        np.random.RandomState(seed=1)

        # sub_parser = argparse.ArgumentParser(description="subject")
        # sub_parser = "sub01"  # parsed.get("subject")
        self.sub_number = ""
        for i in range(0, len(self.sub)):
            if self.sub[i].isdigit():
                self.sub_number += str(self.sub[i])
            else:
                continue

        # Stimuli duration (in sec.)
        # sds.secs = 3

        self.stimuli_path = os.path.join("..", "..", "data", "audio")

#        stimuli_L = pd.read_csv(os.path.join(stimuli_path,
#                                             ("sub-" + self.sub_number +
#                                              "_desc-L.tsv")),
#                                sep="\t")
#        stimuli_R = pd.read_csv(os.path.join(stimuli_path,
#                                             ("sub-" + self.sub_number +
#                                              "_desc-R.tsv")),
#                                sep="\t")

#        stimuli_df = pd.concat([stimuli_L, stimuli_R], ignore_index=True)

        self.stimuli_df = pd.read_csv(self.session_filename, sep="\t")
        self.stimuli_ls = self.stimuli_df["trial_type"]
        print(self.stimuli_ls)


    def _run(self, run_number):
        """
        This function fetches a wave file and plays it.
        It also provides some feedback to the user regarding:
        - the number of the stimuli presentation (from 1 to 130)
        - the inter-stimuli waiting periods.
        """

        random_stimuli_ls = np.random.shuffle(self.stimuli_ls)
        
        for i, sound_file in enumerate(random_stimuli_ls):
            
            to_play = os.path.join(self.stimuli_path, sound_file)
            
            print(f"Presentation number {i}: {sound_file}")
            
            # !!! Needs to be replaced by a psychopy functionality
            playsound(to_play)
            
            print(f"Waiting for {self.ISI} second(s)")
            
            # !!! Needs to be replaced by the utils wait function
            time.sleep(self.ISI)
            # utils.wait_until("self.task_timer", "ISI")


# Calculation of the duration of the experiment
# t_final = time.perf_counter() - t_initial

# print(f"Sequence completed. The elapsed time is {t_final/60} minutes")
