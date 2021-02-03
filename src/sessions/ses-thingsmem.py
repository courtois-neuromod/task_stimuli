import os

THINGS_DATA_PATH = os.path.join("data", "things")
IMAGE_PATH = os.path.join(THINGS_DATA_PATH, "stimuli")


def get_tasks(parsed):
    from ..tasks.things import ThingsMemory

    session_design_filename = os.path.join(
        THINGS_DATA_PATH,
        "memory_designs",
        f"sub-{parsed.subject}_ses-{parsed.session}_design.tsv",
    )
    n_runs_session = n_runs if int(parsed.session) > 1 else 6
    tasks = [
        ThingsMemory(session_design_filename, IMAGE_PATH, run, name=f"task-thingsmemory_run-{run}")
        for run in range(1, n_runs_session + 1)
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
max_seen_spacing = 8


def generate_design_file(subject):
    import pandas
    import numpy as np
    import random
    import hashlib

    images_list = pandas.read_csv(
        os.path.join(THINGS_DATA_PATH, "stimuli", "image_paths_fmri.csv")
    )

    # we select only the exp trial from Martin's BIG experiment
    # and only the first (or second for pilot) half of the 12 exemplar of each category
    images_exp = images_list.loc[
        images_list.condition.eq("exp") &
        (images_list.exemplar_nr > 6 ) # > 6 for pilot < 7 for study
    ]

    design = pandas.DataFrame()

    # seed numpy with subject id to have reproducible design generation
    seed = int(
        hashlib.sha1(("%s" % (subject)).encode("utf-8")).hexdigest(), 16
    ) % (2 ** 32 - 1)
    print("seed", seed)
    np.random.seed(seed)

    all_run_trials = pandas.DataFrame()

    # permute categories per participant
    categories = np.random.permutation(720)+1

    for session in range(n_sessions):
        # select the examplar
        exemplar = session//3+1 + 6 #  + 6 here for pilot, remove for study!!

        # subselect 240 categories for new stimuli
        # loop through the 3 sets of 240 across sessions and thus avoid
        # having distractors from the same category within-session
        # but there will still be between session distractors
        new_stimuli_categories = categories[splits*2*(session%3):splits*2*(session%3+1)]
        #randomize categories to be used as within and between repeated new stimuli to avoid systematic bias
        new_stimuli_categories = np.random.permutation(new_stimuli_categories)
        cat_unseen_within = new_stimuli_categories[:splits]
        cat_unseen_between = new_stimuli_categories[splits:]

        # get all the new stimuli that will be repeated within first
        img_unseen_within = images_exp[
            images_exp.category_nr.isin(cat_unseen_within) &
            images_exp.exemplar_nr.eq(exemplar)]
        img_unseen_within.condition = "unseen"
        img_unseen_within['subcondition'] = "unseen-within"
        img_unseen_within['repetition'] = 1

        # get all the new stimuli that will be repeated between first
        img_unseen_between = images_exp[
            images_exp.category_nr.isin(cat_unseen_between) &
            images_exp.exemplar_nr.eq(exemplar)]
        img_unseen_between.condition = "unseen"
        img_unseen_between['subcondition'] = "unseen-between"
        img_unseen_between['repetition'] = 1

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

        # pass new "within"/"between" stimuli to the next session
        img_between_within = img_unseen_between
        img_between_within.condition = 'seen'
        img_between_within.subcondition = "seen-between-within"
        img_between_within.repetition = 2

        img_within_between = img_unseen_within
        img_within_between.condition = 'seen'
        img_within_between.subcondition = "seen-within-between"
        img_within_between.repetition = 3

        # randomize order across the whole session
        all_run_trials = all_run_trials.sample(frac=1)
        repeated_within = all_run_trials['image_nr'].duplicated()

        # set seen condition for second viewing of new set of images
        all_run_trials.loc[repeated_within, 'condition'] = 'seen'
        all_run_trials.loc[repeated_within & all_run_trials.subcondition.eq('unseen-within'), 'repetition'] = 2
        all_run_trials.loc[repeated_within & all_run_trials.subcondition.eq('seen-between-within'), 'repetition'] = 3

        # split in runs
        all_run_trials["run"] = np.arange(1, n_runs_session+1).repeat(n_trials)
        # set timing
        all_run_trials["onset"] = np.tile(initial_wait + np.arange(n_trials) * trial_duration, n_runs_session)
        all_run_trials["duration"] = image_duration
        # set equal number of flipped and unflipped response mapping
        all_run_trials["response_mapping_flip_h"] = np.hstack([np.random.permutation(np.arange(2,dtype=np.bool).repeat(n_trials/2)) for i in range(n_runs_session)])
        all_run_trials["response_mapping_flip_v"] = np.hstack([np.random.permutation(np.arange(2,dtype=np.bool).repeat(n_trials/2)) for i in range(n_runs_session)])

        # save a file for the whole session (will be split in runs in the task)
        out_fname = os.path.join(
            THINGS_DATA_PATH,
            "memory_designs",
            f"sub-{parsed.subject}_ses-{session+1:03d}_design.tsv",
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
