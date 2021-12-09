import os
import argparse
import time
import pandas as pd
import numpy as np
from playsound import playsound
from psychopy.sound.backend_sounddevice import SoundDeviceSound as sds

#from ..shared import utils

# Time value when the experiment starts
# t_initial = time.perf_counter()


class PureTones():

    def _run():
        """
        This function fetches a wave file and pleays it.
        It also provides some feedback to the user regarding:
        - the number of the stimuli presentation (from 1 to 130)
        - the inter-stimuli waiting periods.
        """

        np.random.RandomState(seed=1)

        # Waiting period between stimuli presentation (in sec.)
        ISI = 0

        # sub_parser = argparse.ArgumentParser(description="subject")
        sub_parser = "sub01" #parsed.get("subject")
        sub_number = ""
        for i in range(0, len(sub_parser)):
            if sub_parser[i].isdigit():
                sub_number += str(sub_parser[i])
            else:
                continue

        # Stimuli duration (in sec.)
        sds.secs = 3

        stimuli_path = os.path.join("..", "..", "data", "audio")

        stimuli_L = pd.read_csv(os.path.join(stimuli_path,
                                             "sub-" + sub_number + "_desc-L.tsv"),
                                sep="\t")
        stimuli_R = pd.read_csv(os.path.join(stimuli_path,
                                             "sub-" + sub_number + "_desc-R.tsv"),
                                sep="\t")

        stimuli_df = pd.concat([stimuli_L, stimuli_R], ignore_index=True)

        stimuli_ls = stimuli_df.to_numpy().flatten().tolist()
        
        # Number of intensities/frequency/ear
        intensity_count = len(stimuli_df) / 2

        i = 1
        while len(stimuli_ls) > 0:

            position = np.random.randint(0, len(stimuli_ls))
            filename = stimuli_ls[position]
            
            to_play = os.path.join(stimuli_path, filename)
                                   
            print(f"Presentation number {i}: {to_play}")
            playsound(to_play)
            
            print("avant", len(stimuli_ls), stimuli_ls)
            del stimuli_ls[position]
            print("après", len(stimuli_ls), stimuli_ls)
            
            i = i + 1
            print(f"Waiting for {ISI} second(s)")
            time.sleep(ISI)
            # utils.wait_until("self.task_timer", "ISI")


PureTones._run()


# Calculation of the duration of the experiment
# t_final = time.perf_counter() - t_initial

# print(f"Sequence completed. The elapsed time is {t_final/60} minutes")
