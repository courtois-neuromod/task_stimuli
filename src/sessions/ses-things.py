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

n_sessions = 12  # number of sessions
n_runs = 10  # number of runs
n_trials_exp = 72  # number of trials for each run
n_trials_catch = 10  # catch trials where response is required
n_trials_test = 10  # for test data, separate images
n_trials_total = n_trials_exp + n_trials_test + n_trials_catch
final_wait = 9  # time to wait after last trial
initial_wait = 3  # time until first trial starts

# trial
trial_duration = 4.5  # mean trial duration
jitters = 0  # chosen to be a range that minimizes phase synchrony and that can be presented exactly on most screens
image_duration = 0.5  # duration of image presentation
rm_duration = 4.0  # duration of response mapping screen
max_rt = 4.0  # from stimulus onset

# constraints
min_catch_spacing = 3
max_catch_spacing = 20


def generate_design_file(subject, session):
    import pandas
    import numpy as np
    import random
    import hashlib

    images_list = pandas.read_csv(
        os.path.join(THINGS_DATA_PATH, "image_paths_fmri.csv")
    )

    images_exp = images_list[
        images_list.condition.eq("exp") & images_list.exemplar_nr.eq(int(session))
    ].sample(frac=1)
    images_catch = images_list[images_list.condition.eq("catch")].sample(frac=1)
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
        niter = 0
        while True:
            niter += 1
            randorder = np.random.permutation(n_trials_total)
            n_noncatch_trial = n_trials_exp + n_trials_test
            catch_indices = np.where(randorder >= n_noncatch_trial)[0]
            catch_indices_bounds = np.hstack([[0], catch_indices, [n_trials_total]])
            catch_spacings = np.diff(catch_indices_bounds)
            if np.all(catch_spacings > min_catch_spacing) and np.all(
                catch_spacings < max_catch_spacing
            ):
                break
        print(subject, session, run, niter)
        run_trials = pandas.concat(
            [
                images_exp[run * n_trials_exp : (run + 1) * n_trials_exp],
                images_test[run * n_trials_test : (run + 1) * n_trials_test],
                images_catch[run * n_trials_catch : (run + 1) * n_trials_catch],
            ]
        )
        run_trials = run_trials.iloc[randorder]
        run_trials["run"] = run + 1
        run_trials["onset"] = initial_wait + np.arange(n_trials_total) * trial_duration
        run_trials["duration"] = image_duration
        all_run_trials = pandas.concat([all_run_trials, run_trials])
    out_fname = os.path.join(
        THINGS_DATA_PATH,
        "designs",
        f"sub-{parsed.subject}_ses-{parsed.session}_design.tsv",
    )
    all_run_trials.to_csv(out_fname, sep="\t")


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
