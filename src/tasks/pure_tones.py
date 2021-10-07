import os, time
import pandas as pd
import numpy as np
import math
from playsound import playsound

# Time value when the experiment starts
t_initial = time.perf_counter()

# Waiting period between stimuli presentation (in sec.)
ISI = 5

np.random.RandomState(seed=1)
csv = ".csv"
stimuli_path = os.path.join("..", "..", "data", "audio", "pure_tones")

stimuli_df = pd.read_csv(os.path.join(stimuli_path, "stimuli") + csv)

ls_columns = stimuli_df.columns.tolist()
ls_index = stimuli_df.index.tolist()

# Initialization of a reference grid to keep track of the already presented stimuli
grid = np.full((len(ls_index), len(ls_columns)), True)


def fetch_filename():
    """
    This function returns a wave file name from the list of available files.
    It also makes sure that the file hasn't already been presented.
    """

    keep_going = True

    while keep_going:
        coordinates = (np.random.randint(0, len(ls_columns)), np.random.randint(0, len(ls_index)))
        v_axis = ls_columns[coordinates[0]]
        h_axis = ls_index[coordinates[1]]

        if grid[coordinates[1], coordinates[0]] == True:
            filename = stimuli_df.at[h_axis, v_axis]
            grid[coordinates[1], coordinates[0]] = False
            keep_going = False
        else:
            pass

    return filename


def stimulus_presentation():
    """
    This function fetches a wave file and pleays it.
    It also provides some feedback to the user regarding:
    - the number of the stimuli presentation (from 1 to 130)
    - the inter-stimuli waiting periods.
    """

    i = 1
    while True in grid:
        to_play = os.path.join(stimuli_path, fetch_filename())
        print(f"Presentation number {i}: {to_play}")
        playsound(to_play)
        i = i + 1
        print(f"Waiting for {ISI} second(s)")
        time.sleep(ISI)

stimulus_presentation()

# Calculation of the duration of the experiment
t_final = time.perf_counter() - t_initial

print(f"Sequence completed. The elapsed time is {t_final/60} minutes")
