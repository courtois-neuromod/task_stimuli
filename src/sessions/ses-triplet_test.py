def get_tasks():
    from ..tasks import language, task_base

    TASKS = [
        language.Triplet(
            "data/language/triplet/test_triplets.tsv", name="task-triplets"
        ),
        task_base.Pause(text="Take a break. Press any key to continue...", wait_key=None),
    ]
    return TASKS

TRIPLET_DATA_PATH = "data/language/triplet/"
TR=1.49
N_TRIALS_PER_RUN = 60
N_RUNS_PER_SESSION = 2
STIMULI_DURATION = 4
BASELINE_BEGIN = 6
BASELINE_END = 9
ISI = 4*TR - STIMULI_DURATION
ISI_JITTER = .5

def generate_design_file(subject):
    import pandas
    import os
    import hashlib
    import numpy as np
    all_triplets = pandas.read_csv(os.path.join(TRIPLET_DATA_PATH, 'fMRI_triplets.csv'), index_col=0)

    # seed numpy with subject id to have reproducible design generation
    seed = int(
        hashlib.sha1(("%s" % (subject)).encode("utf-8")).hexdigest(), 16
    ) % (2 ** 32 - 1)
    print("seed", seed)
    np.random.seed(seed)

    all_run_trials = pandas.DataFrame()


    isi_set = np.random.random_sample(N_TRIALS_PER_RUN)*ISI_JITTER + ISI
    # permute categories per participant

    all_triplets = all_triplets.sample(frac=1)
    for run in range(int(np.ceil(len(all_triplets)/N_TRIALS_PER_RUN))):
        run_triplets = all_triplets[run*N_TRIALS_PER_RUN:(run+1)*N_TRIALS_PER_RUN]
        run_isis = np.random.permutation(isi_set)
        run_triplets['onset'] = BASELINE_BEGIN + np.arange(len(run_triplets))*STIMULI_DURATION + run_isis[:len(run_triplets)]
        run_triplets['duration'] = STIMULI_DURATION

        session = run // N_RUNS_PER_SESSION + 1
        run_in_session = run % N_RUNS_PER_SESSION + 1

        out_fname = os.path.join(
            TRIPLET_DATA_PATH,
            "designs",
            f"sub-{parsed.subject}_ses-{session:03d}_{run_in_session:02d}_design.tsv",
        )
        run_triplets.to_csv(out_fname, sep="\t", index=False)

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
