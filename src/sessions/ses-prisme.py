import os

THINGS_DATA_PATH = os.path.join("data", "things")
PRISME_DATA_PATH = os.path.join("data", "prisme")
IMAGE_PATH = os.path.join(THINGS_DATA_PATH, "images")

# 3 conditions: exp, pos, neg
# shown = image seen by the user
# test:
# pos = test image user is expected to recognize, as he's seen it.
# neg = test image user is expected to not recognize, as it wasn't shown.

def get_tasks(parsed):
    from ..tasks.prisme import Prisme

    session_design_filename = os.path.join(
        PRISME_DATA_PATH,
        "designs",
        f"sub-{parsed.subject}_ses-{parsed.session}_design.tsv",
    )
    tasks = [
        Prisme(session_design_filename, IMAGE_PATH, run, name=f"task-prisme_run-{run}",use_eyetracking=True)
        for run in range(1, fmri_runs + 1)
    ]
    return tasks


# experiment

# n_sessions = 12  # number of sessions
# fmri_runs = 1
# eeg_runs = 1
# n_runs = fmri_runs + eeg_runs  # number of runs
# n_trials_shown = 3  # number of trials for each run
# n_trials_pos = 1  # number of trials for each run
# assert n_trials_pos < n_trials_shown
# n_trials_neg = 1


n_sessions = 12  # number of sessions
fmri_runs = 8
eeg_runs = 3
n_runs = fmri_runs + eeg_runs  # number of runs
n_trials_shown = 58  # number of trials for each run
n_trials_pos = 5  # number of trials for each run
assert n_trials_pos < n_trials_shown
n_trials_neg = 5

# n_trials_catch = 0  # catch trials where response is required -- deep dream eq.
# n_trials_test = 2  # for test data, separate images
# n_trials_total = n_trials_shown + n_trials_test # + n_trials_catch
final_wait = 9  # time to wait after last trial
initial_wait = 1.49*2  # time until first trial starts

# trial
trial_duration = 1.49*3  # mean trial duration
jitters = 0  # chosen to be a range that minimizes phase synchrony and that can be presented exactly on most screens
image_duration = 1.49*2  # duration of image presentation
rm_duration = 4.0  # duration of response mapping screen
# max_rt = 4.0  # from stimulus onset
max_rt = 1.49*3

# constraints
# min_catch_spacing = 3
# max_catch_spacing = 20


def generate_design_file(subject, session):
    import pandas
    import numpy as np
    import random
    import hashlib

    images_list = pandas.read_csv(
        os.path.join(THINGS_DATA_PATH, "images/image_paths_fmri.csv")
    )

    images_exp = images_list[
        images_list.condition.eq("exp") & images_list.exemplar_nr.eq(int(session))
    ].sample(frac=1)
    # images_catch = images_list[images_list.condition.eq("catch")].sample(frac=1)
    images_test = images_list[images_list.condition.eq("test")].sample(frac=1)

    design = pandas.DataFrame()

    print("%s-%s" % (subject, session))
    seed = int(
        hashlib.sha1(("%s-%s" % (subject, session)).encode("utf-8")).hexdigest(), 16
    ) % (2 ** 32 - 1)
    print("seed", seed)
    np.random.seed(seed)

    all_run_trials = pandas.DataFrame()

    for run in range(n_runs):
        # 1. retrieve random images to display for the run.
        niter = 0
        # prevent consecutive catch images.
        # while True:
        #     niter += 1
        #     randorder = np.random.permutation(n_trials_total)
        #     n_noncatch_trial = n_trials_shown + n_trials_test
        #     catch_indices = np.where(randorder >= n_noncatch_trial)[0]
        #     catch_indices_bounds = np.hstack([[0], catch_indices, [n_trials_total]])
        #     catch_spacings = np.diff(catch_indices_bounds)
        #     if not np.all(catch_spacings < min_catch_spacing) or not np.all(
        #         catch_spacings > max_catch_spacing
        #     ):
        #         break
        #     break
        print(subject, session, run, niter)
        # run_trials = run_images_exp.iloc[randorder]
        # run_trials = pandas.concat(
        #     [
        #         images_exp[run * n_trials_shown : (run + 1) * n_trials_shown],
        #         images_test[run * n_trials_test : (run + 1) * n_trials_test],
        #         images_catch[run * n_trials_catch : (run + 1) * n_trials_catch],
        #     ]
        # )
        randorder = np.random.permutation(n_trials_shown)
        shown_images = images_exp[run * n_trials_shown : (run + 1) * n_trials_shown] # retrieve
        shown_images = shown_images.copy(deep=True)
        shown_images = shown_images.iloc[randorder] # randomize
        shown_images["run"] = run + 1
        # shown_images["onset"] = initial_wait + np.arange(n_trials_shown) * trial_duration
        shown_images["duration"] = image_duration
        shown_images["condition"] = "shown"
        shown_images["onset"] = initial_wait + np.arange(n_trials_shown) * trial_duration

        # 2. pick up random images out of the shown ones and mix them up with
        # random test ones.
        # randorder = np.random.permutation(n_trials_total)
        # run_trials_test = 
        # image_pos = images_test[run * n_trials_test : (run + 1) * n_trials_test]

        randorder = np.random.permutation(n_trials_pos)
        positive_images = shown_images.copy(deep=True)
        positive_images = positive_images.iloc[randorder]
        positive_images["run"] = run + 1
        # @todo redefine onset
        # positive_images["onset"] = initial_wait + np.arange(n_trials_shown) * trial_duration  + np.arange(n_trials_pos) * trial_duration
        positive_images["duration"] = image_duration
        positive_images["condition"] = "pos"
        
        randorder = np.random.permutation(n_trials_neg)
        negative_images = images_test[run * n_trials_neg : (run + 1) * n_trials_neg]
        negative_images = negative_images.copy(deep=True)
        negative_images = negative_images.iloc[randorder]
        negative_images["run"] = run + 1
        negative_images["duration"] = image_duration
        negative_images["condition"] = "neg"

        randorder = np.random.permutation(n_trials_pos + n_trials_neg)
        test_images = pandas.concat([positive_images,negative_images])
        test_images = test_images.iloc[randorder]

        all_run_images = pandas.concat([shown_images, test_images])
        all_run_images["onset"] = initial_wait + np.arange(n_trials_shown + n_trials_neg + n_trials_pos) * trial_duration

        all_run_images["type"] = "fmri" if run <= 8 else "eeg"

        all_run_trials = pandas.concat([all_run_trials, all_run_images])

    out_fname_images = os.path.join(
        PRISME_DATA_PATH,
        "designs",
        f"sub-{parsed.subject}_ses-{parsed.session}_design.tsv",
    )
    all_run_trials.to_csv(out_fname_images, sep="\t")


    # out_fname_tests = os.path.join(
    #     PRISME_DATA_PATH,
    #     "designs",
    #     f"sub-{parsed.subject}_ses-{parsed.session}_test_design.tsv",
    # )


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="generate design files for participant / session",
    )
    parser.add_argument("subject", type=str, help="participant id")
    parser.add_argument("session", type=str, help="session id")
    parsed = parser.parse_args()
    generate_design_file(parsed.subject, parsed.session)
