import os
import argparse
import time
import pandas as pd
import numpy as np
from playsound import playsound
from psychopy.sound.backend_sounddevice import SoundDeviceSound as sds

from ..shared import utils

ls_freq = [250, 500, 1000, 2000,
           3000, 4000, 6000, 8000]
ls_intensities = []

sds.secs = 3



# Time value when the experiment starts
t_initial = time.perf_counter()

# Waiting period between stimuli presentation (in sec.)
ISI = 0

np.random.RandomState(seed=1)
csv = ".csv"
stimuli_path = os.path.join("data", "audio", "pure_tones")

stimuli_df = pd.read_csv(os.path.join(stimuli_path, "stimuli") + csv)

ls_columns = stimuli_df.columns.tolist()
ls_index = stimuli_df.index.tolist()

# Initialization of a reference grid to keep track
# of the already presented stimuli
grid = np.full((len(ls_index), len(ls_columns)), True)


class PureTones(Task):


    def fetch_filename():
        """
        Returns a wave file name from the list of available files.
        It also makes sure that the file hasn't already been presented.
        """

        keep_going = True

        while keep_going:
            v_value = np.random.randint(0, len(ls_columns))
            h_value = np.random.randint(0, len(ls_index))

            coordinates = (v_value, h_value)

            v_axis = ls_columns[coordinates[0]]
            h_axis = ls_index[coordinates[1]]
            # print(type(grid[coordinates[1], coordinates[0]]))

            if grid[coordinates[1], coordinates[0]] == True:
                print(True)
                filename = stimuli_df.at[h_axis, v_axis]
                grid[coordinates[1], coordinates[0]] = False
                keep_going = False
            else:
                print(False)
                continue

        return filename


    def _run():
        """
        This function fetches a wave file and pleays it.
        It also provides some feedback to the user regarding:
        - the number of the stimuli presentation (from 1 to 130)
        - the inter-stimuli waiting periods.
        """

        sub_parser = argparse.ArgumentParser(description="Subject ID")

        i = 1
        while True in grid:
            to_play = os.path.join(stimuli_path, fetch_filename())
            print(f"Presentation number {i}: {to_play}")
            playsound(to_play)
            i = i + 1
            print(f"Waiting for {ISI} second(s)")
            time.sleep(ISI)
            # utils.wait_until("self.task_timer", "ISI")


_run()


# Calculation of the duration of the experiment
t_final = time.perf_counter() - t_initial

print(f"Sequence completed. The elapsed time is {t_final/60} minutes")
