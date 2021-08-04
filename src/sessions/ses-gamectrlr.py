import os, sys
import numpy as np


keys = "rludabxy"
n_sessions = 3
n_runs = 2
n_blocks_per_cond = 5
conditions = ['short', 'long']

final_wait = 9  # time to wait after last trial
initial_wait = 3  # time until first trial starts

tr = 1.49

short_press_duration = .3
long_duration_range = [1,3]
isi_range = [tr, tr*2]
blocks_isi = 2*tr

def generate_design_file(subject):
    import pandas
    import random
    import hashlib

    # same durations and ISI for all participants/runs
    np.random.seed(0)
    durations_set = np.random.rand(len(keys)*n_blocks_per_cond) * \
        np.diff(long_duration_range) + long_duration_range[0]

    isi_set = np.random.rand(len(keys)*n_blocks_per_cond*len(conditions) - 1)* \
        np.diff(isi_range) + isi_range[0]

    # seed with subject id to have reproducible design generation
    seed = int(
        hashlib.sha1(("%s" % (subject)).encode("utf-8")).hexdigest(), 16
    ) % (2 ** 32 - 1)
    print("seed", seed)
    random.seed(seed)
    np.random.seed(seed)

    for session in range(n_sessions):
        for run in range(n_runs):
            blocks = conditions * n_blocks_per_cond
            blocks = random.sample(blocks, len(blocks))

            durations = np.random.permutation(durations_set)
            isis = np.random.permutation(isi_set)

            design = pandas.DataFrame([
                {'block': block_idx, 'condition': block, 'key': key}
                for block_idx, block in enumerate(blocks)
                for key in random.sample(keys, len(keys))
                ])
            design['duration'] = short_press_duration
            design.loc[design.condition=='long','duration'] = durations
            design.loc[0, 'onset'] = initial_wait
            design.loc[1:, 'onset'] = (
                initial_wait +
                np.cumsum(design['duration'][:-1].to_numpy()) +
                np.cumsum(isis) +
                np.cumsum(np.ediff1d(design['block'][:-1].to_numpy(),to_begin=[0]))*blocks_isi)

            out_fname = os.path.join(
                "data",
                "game_ctrlr",
                "designs",
                f"sub-{parsed.subject}_ses-{session+1:03d}_run-{run+1:02d}_design.tsv",
            )
            design.to_csv(out_fname, sep="\t", index=False)
            print(design.onset[-1:]+design.duration[-1:])


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="generate design files for participant / session",
    )
    parser.add_argument("subject", type=str, help="participant id")
    parsed = parser.parse_args()
    generate_design_file(parsed.subject)


def get_tasks(parsed):
    from ..tasks.game_controller import ButtonPressTask

    tasks = [
        ButtonPressTask(
            os.path.join(
                "data",
                "game_ctrlr",
                "designs",
                f"sub-{parsed.subject}_ses-{parsed.session}_run-{run:02d}_design.tsv",
            ),
            run,
            name=f"task-gamectrlr_run-{run}")
        for run in range(1, n_runs+1)
    ]
    return tasks
