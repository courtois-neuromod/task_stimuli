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

    def fetch_filename(stimuli_df, ls_columns, ear):
        """
        Returns a wave file name from the list of available files.
        It also makes sure that the file hasn't already been presented.
        """

        if ear == 0:
            indices = ls_index_L
        elif ear == 1:
            indices = ls_index_R

        keep_going = True

        while keep_going:
            v_value = ls_columns[np.random.randint(0, len(ls_columns))]
            h_value = np.random.randint(indices[0], indices[-1] + 1)
            # print(h_value)

            coordinates = (v_value, h_value)
            print(coordinates)
            print(type(grid[coordinates[1], coordinates[0]]))

            if grid[coordinates[1], coordinates[0]] == True:
                # print(True)
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

        np.random.RandomState(seed=1)

        # Waiting period between stimuli presentation (in sec.)
        ISI = 1

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

        stimuli_path = os.path.join("..", "..", "data", "audio", "pure_tones")

        intensities_L = pd.read_csv(os.path.join(stimuli_path, "sub-" + sub_number + "_desc-L.tsv"),
                                    sep="\t")
        intensities_R = pd.read_csv(os.path.join(stimuli_path, "sub-" + sub_number + "_desc-R.tsv"),
                                    sep="\t")

        stimuli_df = pd.concat([intensities_L, intensities_R], ignore_index=True)

        # List of frequencies
        ls_columns = stimuli_df.columns.tolist()

        # Number of intensities/frequency
        intensity_count = 3

        ls_index_L = list(range(0, intensity_count))
        ls_index_R = list(range(intensity_count, 2 * intensity_count))
        ls_index_all = ls_index_L + ls_index_R

        # Initialization of a reference grid to keep track
        # of the already presented stimuli
        grid = np.full((len(ls_index_all), len(ls_columns)), True)

        i = 1
        while True in grid:

            # selection of the side of the presentation (0 = left, 1 = right)
            ear_select = np.random.randint(0, 2)

            to_play = os.path.join(stimuli_path,
                                   fetch_filename(stimuli_df,
                                                  ls_columns,
                                                  ear_select))
            print(f"Presentation number {i}: {to_play}")
            playsound(to_play)
            i = i + 1
            print(f"Waiting for {ISI} second(s)")
            time.sleep(ISI)
            utils.wait_until("self.task_timer", "ISI")


PureTones._run()


# Calculation of the duration of the experiment
# t_final = time.perf_counter() - t_initial

# print(f"Sequence completed. The elapsed time is {t_final/60} minutes")
