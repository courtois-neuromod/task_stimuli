import os

THINGS_DATA_PATH = os.path.join("data", "things")
IMAGE_PATH = os.path.join(THINGS_DATA_PATH, "images")


def get_tasks(parsed):
    from ..tasks.things import Things

    session_design_filename = os.path.join(
        THINGS_DATA_PATH,
        "designs",
        f"sub-{parsed.subject}_ses-{parsed.session}_design.tsv",
    )
    tasks = [
        Things(session_design_filename, IMAGE_PATH, run, name=f"task-things_run-{run}")
        for run in range(1, n_runs + 1)
    ]
    return tasks


# experiment

n_sessions = 18  # number of sessions
n_runs = 12  # number of runs
n_trials = 60  # number of trials for each run
splits = n_trials * 2

final_wait = 9  # time to wait after last trial
initial_wait = 3  # time until first trial starts

# trial
tr = 1.49
trial_duration = 3*tr  # mean trial duration
jitters = 0  # chosen to be a range that minimizes phase synchrony and that can be presented exactly on most screens
image_duration = 2*tr  # duration of image presentation
rm_duration = 4.  # duration of response mapping screen
max_rt = 4.0  # from stimulus onset

# constraints
min_catch_spacing = 3
max_catch_spacing = 20


def generate_design_file(subject):
    import pandas
    import numpy as np
    import random
    import hashlib

    images_list = pandas.read_csv(
        os.path.join(THINGS_DATA_PATH, "image_paths_fmri.csv")
    )

    images_exp = images_list[
        images_list.condition.eq("exp") & images_list.exemplar_nr < 7
    ]

    design = pandas.DataFrame()

    seed = int(
        hashlib.sha1(("%s" % (subject)).encode("utf-8")).hexdigest(), 16
    ) % (2 ** 32 - 1)
    print("seed", seed)
    np.random.seed(seed)

    all_run_trials = pandas.DataFrame()

    # permute categories per participant
    categories = np.random.permutation(720)+1

    for session in range(n_sessions):
        exemplar = session//3+1
        cat_unseen_within = categories[splits*(session%6):splits*(session%6+1)]
        cat_unseen_between = categories[splits*((session+1)%6):splits*((session+1)%6+1)]

        img_unseen_within = images_exp[
            images_exp.category_nr.isin(cat_unseen_within) &
            images_exp.exemplar_nr.eq(exemplar)]
        img_unseen_between = images_exp[
            images_exp.category_nr.isin(cat_unseen_between) &
            images_exp.exemplar_nr.eq(exemplar)]

        n_runs_session = n_runs
        if session == 0:
            # show twice the within set and once the between set
            all_run_trials = pandas.concat(
                [img_unseen_within]*2 +
                [img_unseen_between])
            n_runs_session = n_runs//2
        else:
            all_run_trials = pandas.concat(
                [img_unseen_within]*2 +
                [img_unseen_between]+
                [img_between_within]*2 +
                [img_within_between]
                )
        # pass to next session
        img_between_within = img_unseen_between
        img_within_between = img_unseen_within

        all_run_trials = all_run_trials.sample(frac=1)
        all_run_trials["run"] = np.arange(1, n_runs_session+1).repeat(n_trials)
        all_run_trials["onset"] = np.tile(initial_wait + np.arange(n_trials) * trial_duration, n_runs_session)
        all_run_trials["duration"] = image_duration

        out_fname = os.path.join(
            THINGS_DATA_PATH,
            "memory_designs",
            f"sub-{parsed.subject}_ses-{session+1}_design.tsv",
        )
        all_run_trials.to_csv(out_fname, sep="\t", index=False)


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
